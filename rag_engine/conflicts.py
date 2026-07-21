# rag_engine/conflicts.py
"""
Conflict Detection Module - THE KEY DIFFERENTIATOR

This module detects and explains contradictions between documents:
1. Direct contradictions: Same parameter, different values
2. Decay/staleness: Procedure says X but practice shows Y, or intervals overdue

The system uses LLM to generate human-readable explanations of conflicts
suitable for plant operators, including severity assessment.

Supports multiple LLM backends (Claude, Groq, Ollama) with automatic fallback.
"""

import os
import re
import logging
from datetime import date, timedelta
from typing import List, Optional, Tuple, Dict
from functools import lru_cache
import time

from shared.schemas import Claim, Citation, Conflict
from .retriever import Chunk, extract_equipment_tags, get_all_equipment_tags_from_chunks
from .llm import get_llm
from . import fixtures

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Knowledge Graph Interface
# ---------------------------------------------------------------------------

def _get_claims_for_entity(equipment_tag: str) -> List[Claim]:
    """
    Get claims for an entity from knowledge graph.
    Falls back to fixtures if knowledge_graph module isn't available or returns empty.
    """
    try:
        from knowledge_graph.query import get_claims_for_entity
        claims = get_claims_for_entity(equipment_tag)
        if claims:
            return claims
    except Exception as e:
        logger.debug(f"Knowledge graph unavailable: {e}")
    return fixtures.get_claims_for_entity(equipment_tag)


def _find_conflicting_claims() -> List[Tuple[Claim, Claim]]:
    """
    Find all conflicting claim pairs from knowledge graph.
    Falls back to fixtures if knowledge_graph module isn't available or returns empty.
    """
    try:
        from knowledge_graph.query import find_conflicting_claims
        conflicts = find_conflicting_claims()
        if conflicts:
            return conflicts
    except Exception as e:
        logger.debug(f"Knowledge graph unavailable: {e}")
    return fixtures.find_conflicting_claims()


def _get_stale_claims(reference_date: Optional[date] = None) -> List[Claim]:
    """
    Get claims that may be stale.
    Falls back to fixtures if knowledge_graph module isn't available.
    """
    try:
        from knowledge_graph.query import get_stale_claims
        # Person 2's signature: get_stale_claims(staleness_days: int = 365)
        stale = get_stale_claims(staleness_days=365)
        if stale:
            return stale
    except Exception as e:
        logger.debug(f"Knowledge graph unavailable: {e}")
    return fixtures.get_stale_claims(reference_date)


# ---------------------------------------------------------------------------
# LLM Prompts for Conflict Explanation
# ---------------------------------------------------------------------------

CONFLICT_EXPLANATION_PROMPT = """You are an expert industrial knowledge assistant analyzing potential conflicts in plant documentation.

Two excerpts describe the same parameter ({parameter}) for equipment {equipment_tag}, but give different values:

EXCERPT A (from {source_a}, dated {date_a}):
"{text_a}"
Value A: {value_a}

EXCERPT B (from {source_b}, dated {date_b}):
"{text_b}"
Value B: {value_b}

Please analyze this discrepancy:
1. Explain the difference in plain language for a plant operator
2. Assess whether this is a DIRECT_CONTRADICTION (both claim to be the correct current value) or DECAY (one is outdated, superseded, or the practice has evolved away from the documented procedure)
3. Rate the severity as LOW (minor documentation issue), MEDIUM (could cause operational confusion), or HIGH (safety-critical discrepancy)
4. Suggest what action should be taken

Respond in this JSON format:
{{
    "explanation": "Plain language explanation for operators...",
    "risk_type": "direct_contradiction" or "decay",
    "severity": "low" or "medium" or "high",
    "recommended_action": "What to do about this..."
}}"""


def _explain_conflict_with_llm(
    equipment_tag: str,
    parameter: str,
    claim_a: Claim,
    claim_b: Claim
) -> Tuple[str, str, str]:
    """
    Use LLM to explain a conflict between two claims.
    Supports Claude, Groq, Ollama with automatic fallback.

    Returns:
        Tuple of (explanation, risk_type, severity)
    """
    import json

    prompt = CONFLICT_EXPLANATION_PROMPT.format(
        parameter=parameter,
        equipment_tag=equipment_tag,
        source_a=claim_a.doc_id,
        date_a=claim_a.effective_date or "unknown",
        text_a=claim_a.source_text,
        value_a=claim_a.value,
        source_b=claim_b.doc_id,
        date_b=claim_b.effective_date or "unknown",
        text_b=claim_b.source_text,
        value_b=claim_b.value
    )

    try:
        llm = get_llm()
        response_text = llm.generate(prompt, max_tokens=500)

        # Check for mock response
        if response_text.startswith("[Mock response"):
            return _generate_fallback_explanation(claim_a, claim_b)

        # Parse JSON response
        # Find JSON in response (handle potential markdown wrapping)
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            explanation = result.get("explanation", "Conflict detected between sources.")
            risk_type = result.get("risk_type", "direct_contradiction")
            severity = result.get("severity", "medium")

            # Validate risk_type
            if risk_type not in ("direct_contradiction", "decay"):
                risk_type = "direct_contradiction"

            # Validate severity
            if severity not in ("low", "medium", "high"):
                severity = "medium"

            return explanation, risk_type, severity
        else:
            return _generate_fallback_explanation(claim_a, claim_b)

    except Exception as e:
        logger.error(f"LLM call failed for conflict explanation: {e}")
        return _generate_fallback_explanation(claim_a, claim_b)


def _generate_fallback_explanation(claim_a: Claim, claim_b: Claim) -> Tuple[str, str, str]:
    """
    Generate a basic conflict explanation without Claude API.

    Classification logic:
    - DIRECT_CONTRADICTION: Both docs are authoritative (e.g., manual vs SOP, SOP vs SOP)
      and claim different current values for the same parameter.
    - DECAY: One doc is a procedure/spec, the other is a log/report showing actual practice
      has deviated, OR a scheduled interval has been exceeded.
    """
    # Get chunk info to determine document types
    chunk_a = fixtures.get_chunk_by_id(claim_a.chunk_id)
    chunk_b = fixtures.get_chunk_by_id(claim_b.chunk_id)

    doc_type_a = chunk_a.metadata.doc_type if chunk_a else "unknown"
    doc_type_b = chunk_b.metadata.doc_type if chunk_b else "unknown"

    # Document types that represent "authoritative" specs/procedures
    authoritative_types = {"manual", "sop"}
    # Document types that represent "actual practice" records
    practice_types = {"maintenance_log", "incident_report", "inspection_report"}

    # Determine if this is decay (procedure vs practice) or direct contradiction
    is_decay = (
        (doc_type_a in authoritative_types and doc_type_b in practice_types) or
        (doc_type_a in practice_types and doc_type_b in authoritative_types)
    )

    if is_decay:
        # Identify which is the procedure and which is the practice
        if doc_type_a in authoritative_types:
            proc_value, prac_value = claim_a.value, claim_b.value
            proc_doc, prac_doc = claim_a.doc_id, claim_b.doc_id
        else:
            proc_value, prac_value = claim_b.value, claim_a.value
            proc_doc, prac_doc = claim_b.doc_id, claim_a.doc_id

        risk_type = "decay"
        explanation = (
            f"The documented procedure ({proc_doc}) specifies {proc_value}, "
            f"but actual practice records ({prac_doc}) show {prac_value}. "
            f"This indicates the documented procedure may not reflect current practice "
            f"and should be reviewed for a potential update."
        )
    else:
        # Both are authoritative documents - direct contradiction
        risk_type = "direct_contradiction"
        if claim_a.effective_date and claim_b.effective_date:
            date_diff = abs((claim_a.effective_date - claim_b.effective_date).days)
            explanation = (
                f"Two authoritative documents give different values for the same parameter: "
                f"{claim_a.value} (from {claim_a.doc_id}) vs {claim_b.value} (from {claim_b.doc_id}). "
                f"The documents are dated {date_diff} days apart but both appear to be current. "
                f"This requires immediate clarification from engineering."
            )
        else:
            explanation = (
                f"Conflicting values found in authoritative documents: "
                f"{claim_a.value} vs {claim_b.value}. "
                f"Both documents appear to be current specifications. "
                f"This requires immediate clarification."
            )

    # Estimate severity based on parameter type
    param_lower = claim_a.parameter_name.lower()
    if any(kw in param_lower for kw in ['pressure', 'temperature', 'limit', 'max', 'min', 'safety']):
        severity = "high"
    elif any(kw in param_lower for kw in ['interval', 'frequency', 'schedule']):
        severity = "medium"
    else:
        severity = "low"

    return explanation, risk_type, severity


# ---------------------------------------------------------------------------
# Conflict Detection
# ---------------------------------------------------------------------------

def _values_conflict(value_a: str, value_b: str, parameter_name: str) -> bool:
    """
    Determine if two values conflict beyond reasonable tolerance.
    """
    # Exact match = no conflict
    if value_a.strip().lower() == value_b.strip().lower():
        return False

    # Try numeric comparison with tolerance
    try:
        num_a = float(re.sub(r'[^\d.\-]', '', value_a))
        num_b = float(re.sub(r'[^\d.\-]', '', value_b))

        # Allow 2% tolerance for numeric values
        if num_a == 0 and num_b == 0:
            return False
        tolerance = 0.02 * max(abs(num_a), abs(num_b))
        return abs(num_a - num_b) > tolerance

    except (ValueError, TypeError):
        # Non-numeric values: any difference is a conflict
        return True


def _claim_to_citation(claim: Claim) -> Citation:
    """Convert a Claim to a Citation for the Conflict schema."""
    # Get the chunk to find source file info
    chunk = fixtures.get_chunk_by_id(claim.chunk_id)

    if chunk:
        return Citation(
            doc_id=claim.doc_id,
            source_file=chunk.metadata.source_file,
            page_or_row=chunk.metadata.page_or_row,
            excerpt=claim.source_text[:200]
        )
    else:
        return Citation(
            doc_id=claim.doc_id,
            source_file=f"Document {claim.doc_id}",
            page_or_row=None,
            excerpt=claim.source_text[:200]
        )


def detect_conflicts_for_claims(
    claim_pairs: List[Tuple[Claim, Claim]]
) -> List[Conflict]:
    """
    Detect and explain conflicts from a list of claim pairs.
    """
    conflicts = []

    for claim_a, claim_b in claim_pairs:
        if not _values_conflict(claim_a.value, claim_b.value, claim_a.parameter_name):
            continue

        # Get explanation from Claude (or fallback)
        explanation, risk_type, severity = _explain_conflict_with_llm(
            equipment_tag=claim_a.equipment_tag,
            parameter=claim_a.parameter_name,
            claim_a=claim_a,
            claim_b=claim_b
        )

        conflict = Conflict(
            entity=claim_a.equipment_tag,
            parameter=claim_a.parameter_name,
            source_a=_claim_to_citation(claim_a),
            value_a=claim_a.value,
            source_b=_claim_to_citation(claim_b),
            value_b=claim_b.value,
            explanation=explanation,
            severity=severity,
            risk_type=risk_type
        )
        conflicts.append(conflict)

    return conflicts


def detect_conflicts_for_query(
    question: str,
    chunks: Optional[List[Chunk]] = None
) -> List[Conflict]:
    """
    Detect conflicts relevant to a specific query.

    Extracts equipment tags from the question and retrieved chunks,
    then checks for conflicting claims on those entities.

    Args:
        question: The user's question
        chunks: Retrieved chunks (optional, for additional equipment tag extraction)

    Returns:
        List of Conflict objects relevant to the query
    """
    # Extract equipment tags from question
    equipment_tags = extract_equipment_tags(question)

    # Also get tags from retrieved chunks
    if chunks:
        chunk_tags = get_all_equipment_tags_from_chunks(chunks)
        equipment_tags = list(set(equipment_tags + chunk_tags))

    if not equipment_tags:
        return []

    # Get claims for each equipment tag and find conflicts
    all_claims: Dict[str, List[Claim]] = {}

    for tag in equipment_tags:
        claims = _get_claims_for_entity(tag)
        for claim in claims:
            key = f"{claim.equipment_tag}:{claim.parameter_name}"
            if key not in all_claims:
                all_claims[key] = []
            all_claims[key].append(claim)

    # Find conflicting pairs
    conflict_pairs = []
    for key, claims in all_claims.items():
        if len(claims) > 1:
            for i in range(len(claims)):
                for j in range(i + 1, len(claims)):
                    if _values_conflict(claims[i].value, claims[j].value, claims[i].parameter_name):
                        conflict_pairs.append((claims[i], claims[j]))

    return detect_conflicts_for_claims(conflict_pairs)


def detect_staleness_conflicts(reference_date: Optional[date] = None) -> List[Conflict]:
    """
    Detect conflicts arising from stale/overdue maintenance intervals.

    This is a special type of decay conflict where no contradicting document exists,
    but the current date has passed the implied next-due-date.
    """
    if reference_date is None:
        reference_date = date.today()

    stale_claims = _get_stale_claims(reference_date)
    conflicts = []

    for claim in stale_claims:
        # For staleness, we create a "virtual" conflicting claim representing current date
        explanation = (
            f"The {claim.parameter_name} for {claim.equipment_tag} specifies {claim.value}, "
            f"but based on the last recorded maintenance date, this interval has been exceeded. "
            f"This represents a potential compliance or safety issue that should be addressed."
        )

        conflict = Conflict(
            entity=claim.equipment_tag,
            parameter=claim.parameter_name,
            source_a=_claim_to_citation(claim),
            value_a=f"{claim.value} (required interval)",
            source_b=Citation(
                doc_id="SYSTEM",
                source_file="Current Date Check",
                page_or_row=None,
                excerpt=f"As of {reference_date}, the scheduled interval has passed."
            ),
            value_b=f"Overdue as of {reference_date}",
            explanation=explanation,
            severity="medium",  # Overdue maintenance is at least medium severity
            risk_type="decay"
        )
        conflicts.append(conflict)

    return conflicts


# ---------------------------------------------------------------------------
# Global Conflict Cache (for dashboard panel)
# ---------------------------------------------------------------------------

_conflict_cache: Optional[List[Conflict]] = None
_cache_timestamp: float = 0
CACHE_TTL_SECONDS = 300  # 5 minute cache


def get_all_known_conflicts(force_refresh: bool = False) -> List[Conflict]:
    """
    Get ALL known conflicts across the entire knowledge base.

    This is used by Person 4's dashboard panel to show all flagged conflicts,
    not just those related to the current query.

    Results are cached for 5 minutes to avoid recomputing on every request.

    Args:
        force_refresh: If True, bypass cache and recompute

    Returns:
        List of all Conflict objects in the system
    """
    global _conflict_cache, _cache_timestamp

    current_time = time.time()

    # Check cache validity
    if (
        not force_refresh
        and _conflict_cache is not None
        and (current_time - _cache_timestamp) < CACHE_TTL_SECONDS
    ):
        return _conflict_cache

    logger.info("Refreshing global conflict cache...")

    all_conflicts = []

    # Get all conflicting claim pairs from knowledge graph
    conflicting_pairs = _find_conflicting_claims()
    all_conflicts.extend(detect_conflicts_for_claims(conflicting_pairs))

    # Also check for staleness/decay conflicts
    staleness_conflicts = detect_staleness_conflicts()
    all_conflicts.extend(staleness_conflicts)

    # Deduplicate (same entity + parameter)
    seen = set()
    unique_conflicts = []
    for conflict in all_conflicts:
        key = f"{conflict.entity}:{conflict.parameter}"
        if key not in seen:
            seen.add(key)
            unique_conflicts.append(conflict)

    # Update cache
    _conflict_cache = unique_conflicts
    _cache_timestamp = current_time

    logger.info(f"Found {len(unique_conflicts)} unique conflicts")
    return unique_conflicts


def refresh_conflict_cache() -> List[Conflict]:
    """Force refresh of the conflict cache."""
    return get_all_known_conflicts(force_refresh=True)
