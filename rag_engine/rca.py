"""
rag_engine/rca.py — Root Cause Analysis Chain (Feature 5)

Triggered only when the query is incident-related (mentions trip/failure/incident
keywords, or the top retrieved chunk is doc_type == "incident_report").
"""
from __future__ import annotations

import logging
import re
from typing import List

from shared.schemas import Incident, RootCauseChain, Claim, Conflict
from knowledge_graph.query import (
    get_claims_for_entity,
    get_incidents_similar_to,
)
from rag_engine.llm import get_llm

logger = logging.getLogger(__name__)

# Keywords that signal an incident-related query
_INCIDENT_KEYWORDS = re.compile(
    r"\b(trip|fail|failure|incident|why did|root cause|cause of|breakdown|"
    r"shut down|shutdown|alarm|emergency|overpressure|leak|fire|explosion)\b",
    re.IGNORECASE,
)


def is_incident_query(question: str, chunks: list) -> bool:
    """Return True when the question/top-chunk signals an incident-related query."""
    if _INCIDENT_KEYWORDS.search(question):
        return True
    # Check top retrieved chunk doc_type
    if chunks:
        top_meta = getattr(chunks[0], "metadata", None)
        if top_meta and getattr(top_meta, "doc_type", "") == "incident_report":
            return True
    return False


def _get_all_conflicts_for_entity(entity: str) -> List[Conflict]:
    """Pull conflicts for a specific entity from the knowledge graph."""
    try:
        from rag_engine.conflicts import get_all_known_conflicts
        all_conflicts = get_all_known_conflicts()
        return [c for c in all_conflicts if c.entity.upper() == entity.upper()]
    except Exception as e:
        logger.warning("Could not retrieve conflicts for %s: %s", entity, e)
        return []


def _extract_equipment_tag(question: str, chunks: list) -> str | None:
    """Best-effort equipment tag extraction from question or top chunks."""
    from rag_engine.retriever import extract_equipment_tags
    tags = extract_equipment_tags(question)
    if tags:
        return tags[0]
    for chunk in chunks[:3]:
        meta = getattr(chunk, "metadata", None)
        if meta:
            eq_tags = getattr(meta, "equipment_tags", [])
            if eq_tags:
                return eq_tags[0]
    return None


def _parse_llm_rca(response: str) -> tuple[str, list[str]]:
    """
    Parse LLM response into (likely_root_cause, recommended_checks).
    Expected format:
        ROOT CAUSE: <text>
        CHECKS:
        1. <check>
        2. <check>
    Falls back gracefully if format differs.
    """
    likely_root_cause = "Unable to determine root cause from available data."
    recommended_checks: list[str] = []

    lines = response.strip().splitlines()
    in_checks = False
    cause_parts: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("ROOT CAUSE:"):
            cause_parts.append(line[len("ROOT CAUSE:"):].strip())
        elif upper.startswith("CHECKS:") or upper.startswith("RECOMMENDED CHECKS:"):
            in_checks = True
        elif in_checks:
            # Strip leading numbers/bullets
            cleaned = re.sub(r"^[\d]+[\.\)]\s*", "", line)
            cleaned = re.sub(r"^[-•]\s*", "", cleaned)
            if cleaned:
                recommended_checks.append(cleaned)
        else:
            cause_parts.append(line)

    if cause_parts:
        likely_root_cause = " ".join(cause_parts).strip()

    # Fallback: if no checks parsed, split by newline numbers
    if not recommended_checks:
        numbered = re.findall(r"\d+[\.\)]\s*(.+)", response)
        recommended_checks = numbered

    return likely_root_cause, recommended_checks


def build_root_cause_chain(question: str, chunks: list) -> RootCauseChain | None:
    """
    Build a RootCauseChain for the current query.
    Returns None if insufficient context or equipment tag cannot be found.
    """
    equipment_tag = _extract_equipment_tag(question, chunks)

    # Gather context
    claims: List[Claim] = []
    conflicts: List[Conflict] = []
    similar: List[Incident] = []

    if equipment_tag:
        try:
            claims = get_claims_for_entity(equipment_tag)
        except Exception as e:
            logger.warning("Claims retrieval failed: %s", e)

        conflicts = _get_all_conflicts_for_entity(equipment_tag)

    try:
        similar = get_incidents_similar_to(question, top_k=3)
    except Exception as e:
        logger.warning("Similar incidents retrieval failed: %s", e)

    # Build LLM prompt
    claims_text = "\n".join(
        f"- {c.parameter_name}: {c.value} (source: {c.doc_id}, conf: {c.confidence:.2f})"
        for c in claims[:8]
    ) or "No claims found."

    conflicts_text = "\n".join(
        f"- [{c.risk_type}] {c.entity}/{c.parameter}: {c.value_a} vs {c.value_b}"
        for c in conflicts[:4]
    ) or "No conflicts found."

    similar_text = "\n".join(
        f"- [{inc.severity}] {inc.incident_type}: {inc.description[:120]}"
        for inc in similar[:3]
    ) or "No similar incidents found."

    prompt = f"""You are an industrial reliability engineer doing root cause analysis.

INCIDENT QUERY: {question}

KNOWN CLAIMS about relevant equipment:
{claims_text}

KNOWN CONFLICTS/CONTRADICTIONS:
{conflicts_text}

SIMILAR PAST INCIDENTS:
{similar_text}

Based on the above, provide a specific root cause analysis.

Respond in exactly this format:
ROOT CAUSE: <one concise sentence identifying the most likely root cause>
CHECKS:
1. <first thing to check or verify>
2. <second thing to check or verify>
3. <third thing to check or verify>
4. <fourth thing to check or verify>
"""

    try:
        llm = get_llm()
        response = llm.generate(
            prompt=prompt,
            system="You are an industrial reliability engineer. Be specific, not generic. Reference the actual equipment and parameters mentioned.",
            max_tokens=600,
        )
        likely_root_cause, recommended_checks = _parse_llm_rca(response)
    except Exception as e:
        logger.error("RCA LLM call failed: %s", e)
        likely_root_cause = f"RCA unavailable: {e}"
        recommended_checks = ["Check maintenance logs", "Review recent parameter changes", "Inspect equipment physically"]

    # Find best matching incident for the chain header
    primary_incident = similar[0] if similar else None

    return RootCauseChain(
        incident=primary_incident,
        related_claims=claims[:8],
        related_conflicts=conflicts[:4],
        similar_incidents=similar,
        likely_root_cause=likely_root_cause,
        recommended_checks=recommended_checks or ["No specific checks identified"],
    )
