# rag_engine/lessons.py
"""
Lessons Learned Surfacing Module

Proactively surfaces relevant past incidents and lessons learned based on:
- The user's question
- Equipment tags mentioned in the query/answer
- Similar incident patterns

This should feel proactive/unprompted in the UI - surfacing relevant safety
learnings even when the user didn't explicitly ask about incidents.
"""

import logging
from typing import List, Optional, Set
from datetime import date

from shared.schemas import Incident
from .retriever import Chunk, extract_equipment_tags, get_all_equipment_tags_from_chunks
from . import fixtures

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Knowledge Graph Interface
# ---------------------------------------------------------------------------

def _get_incidents_similar_to(
    query: str,
    equipment_tags: Optional[List[str]] = None
) -> List[Incident]:
    """
    Get incidents similar to a query from knowledge graph.
    Falls back to fixtures if knowledge_graph module isn't available.
    """
    try:
        from knowledge_graph.query import get_incidents_similar_to
        # Person 2's signature: get_incidents_similar_to(text: str, top_k: int = 3)
        # Include equipment tags in the search text for better matching
        search_text = query
        if equipment_tags:
            search_text = f"{query} {' '.join(equipment_tags)}"
        return get_incidents_similar_to(search_text, top_k=5)
    except (ImportError, Exception) as e:
        logger.debug(f"Using fixtures for incidents: {e}")
        return fixtures.get_incidents_similar_to(query, equipment_tags)


# ---------------------------------------------------------------------------
# Relevance Scoring
# ---------------------------------------------------------------------------

# Keywords that indicate the query might benefit from incident surfacing
INCIDENT_TRIGGER_KEYWORDS = {
    # Safety-related
    'safety', 'hazard', 'risk', 'danger', 'warning', 'caution',
    'incident', 'accident', 'near miss', 'injury',

    # Equipment issues
    'failure', 'failed', 'malfunction', 'breakdown', 'leak', 'leaking',
    'alarm', 'trip', 'shutdown', 'emergency',

    # Maintenance-related
    'maintenance', 'repair', 'inspection', 'check', 'test', 'testing',
    'troubleshoot', 'diagnose', 'problem', 'issue',

    # Operational
    'startup', 'shutdown', 'operate', 'operating', 'procedure',
    'deviation', 'abnormal', 'unusual'
}

# Minimum relevance score to include an incident (0.0 - 1.0)
MIN_RELEVANCE_THRESHOLD = 0.3


def _compute_incident_relevance(
    incident: Incident,
    question: str,
    equipment_tags: List[str],
    answer_context: Optional[str] = None
) -> float:
    """
    Compute a relevance score for an incident given the query context.

    Factors:
    - Equipment tag match (highest weight)
    - Keyword overlap with question
    - Keyword overlap with answer context
    - Incident severity (higher severity = more relevant to surface)

    Returns a score between 0.0 and 1.0.
    """
    score = 0.0

    # Factor 1: Equipment tag match (max 0.4)
    if incident.equipment_tag and incident.equipment_tag in equipment_tags:
        score += 0.4

    # Factor 2: Keyword overlap with question (max 0.25)
    question_lower = question.lower()
    question_words = set(question_lower.split())
    incident_desc_words = set(incident.description.lower().split())

    # Check for trigger keywords in question
    trigger_matches = question_words & INCIDENT_TRIGGER_KEYWORDS
    if trigger_matches:
        score += min(0.15, len(trigger_matches) * 0.05)

    # Check for description word overlap
    meaningful_overlap = len(question_words & incident_desc_words)
    score += min(0.1, meaningful_overlap * 0.02)

    # Factor 3: Answer context overlap (max 0.2)
    if answer_context:
        context_lower = answer_context.lower()
        context_words = set(context_lower.split())
        context_overlap = len(context_words & incident_desc_words)
        score += min(0.2, context_overlap * 0.02)

    # Factor 4: Severity bonus (max 0.15)
    severity_bonus = {
        'critical': 0.15,
        'high': 0.12,
        'medium': 0.08,
        'low': 0.04
    }
    score += severity_bonus.get(incident.severity, 0.05)

    return min(1.0, score)


# ---------------------------------------------------------------------------
# Main Lessons Learned Function
# ---------------------------------------------------------------------------

def surface_lessons_learned(
    question: str,
    answer_context: Optional[str] = None,
    chunks: Optional[List[Chunk]] = None,
    max_lessons: int = 3
) -> List[Incident]:
    """
    Surface relevant lessons learned (past incidents) based on query context.

    This is called after generating an answer to proactively surface relevant
    incidents even when the user didn't ask about them.

    Args:
        question: The user's original question
        answer_context: The generated answer (optional, for better relevance)
        chunks: Retrieved chunks (for equipment tag extraction)
        max_lessons: Maximum number of incidents to return

    Returns:
        List of relevant Incident objects, sorted by relevance
    """
    # Extract equipment tags from question and chunks
    equipment_tags = extract_equipment_tags(question)

    if chunks:
        chunk_tags = get_all_equipment_tags_from_chunks(chunks)
        equipment_tags = list(set(equipment_tags + chunk_tags))

    # Get potentially relevant incidents from knowledge graph
    candidate_incidents = _get_incidents_similar_to(question, equipment_tags)

    if not candidate_incidents:
        logger.debug("No candidate incidents found for lessons learned")
        return []

    # Score each incident for relevance
    scored_incidents = []
    for incident in candidate_incidents:
        relevance = _compute_incident_relevance(
            incident=incident,
            question=question,
            equipment_tags=equipment_tags,
            answer_context=answer_context
        )

        if relevance >= MIN_RELEVANCE_THRESHOLD:
            scored_incidents.append((relevance, incident))

    # Sort by relevance (descending) and take top N
    scored_incidents.sort(key=lambda x: x[0], reverse=True)
    top_incidents = [incident for _, incident in scored_incidents[:max_lessons]]

    if top_incidents:
        logger.info(f"Surfacing {len(top_incidents)} lessons learned for query")

    return top_incidents


def should_surface_lessons(question: str) -> bool:
    """
    Quick check if a question is likely to benefit from lessons learned.

    This can be used to skip the more expensive incident search for
    clearly unrelated queries.
    """
    question_lower = question.lower()
    question_words = set(question_lower.split())

    # Check for trigger keywords
    if question_words & INCIDENT_TRIGGER_KEYWORDS:
        return True

    # Check for equipment tags (always potentially relevant)
    if extract_equipment_tags(question):
        return True

    # Generic questions probably don't need incidents
    return False
