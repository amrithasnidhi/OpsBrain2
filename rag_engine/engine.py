# rag_engine/engine.py
"""
Main RAG Engine Entry Point

Exposes the two primary functions for Person 4's app layer:
- answer_query(question: str) -> QueryResult
- get_all_known_conflicts() -> list[Conflict]

This module orchestrates retrieval, Q&A generation, conflict detection,
and lessons learned surfacing into a single coherent response.
"""

import logging
from typing import List, Optional

from shared.schemas import QueryResult, Conflict

from .retriever import retrieve, hybrid_retrieve, Chunk, get_all_equipment_tags_from_chunks
from .qa import generate_answer
from .conflicts import detect_conflicts_for_query, get_all_known_conflicts as _get_all_conflicts
from .lessons import surface_lessons_learned

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main Query Function
# ---------------------------------------------------------------------------

def answer_query(
    question: str,
    top_k: int = 6,
    include_conflicts: bool = True,
    include_lessons: bool = True
) -> QueryResult:
    """
    Main entry point for answering questions from the Industrial Knowledge Brain.

    This function:
    1. Retrieves relevant document chunks from ChromaDB
    2. Detects any conflicts between sources for mentioned equipment
    3. Generates an answer using Claude with proper citations
    4. Surfaces relevant lessons learned (past incidents)

    Args:
        question: The user's natural language question
        top_k: Number of chunks to retrieve (default 6)
        include_conflicts: Whether to detect and include conflicts (default True)
        include_lessons: Whether to surface lessons learned (default True)

    Returns:
        QueryResult containing:
        - answer: The generated answer
        - confidence: Confidence score (0.0 - 1.0)
        - citations: List of source citations
        - conflicts: List of detected conflicts (if any)
        - lessons_learned: List of relevant past incidents (if any)

    Example:
        >>> from rag_engine import answer_query
        >>> result = answer_query("What is the relief pressure for PSV-101?")
        >>> print(result.answer)
        >>> for conflict in result.conflicts:
        ...     print(f"CONFLICT: {conflict.explanation}")
    """
    logger.info(f"Processing query: '{question[:100]}...' " if len(question) > 100 else f"Processing query: '{question}'")

    # Step 1: Retrieve relevant chunks (hybrid: dense + knowledge-graph structured)
    chunks, retrieval_mode = hybrid_retrieve(question, top_k=top_k)
    logger.info(f"Retrieved {len(chunks)} chunks via {retrieval_mode} mode")

    # Step 2: Detect conflicts (if enabled)
    conflicts = []
    if include_conflicts:
        try:
            conflicts = detect_conflicts_for_query(question, chunks)
            if conflicts:
                logger.info(f"Detected {len(conflicts)} conflicts relevant to query")
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            # Don't fail the query, just skip conflicts

    # Step 3: Generate answer
    try:
        result = generate_answer(
            question=question,
            chunks=chunks,
            conflicts=conflicts,
            lessons=[]  # Will be added after generation
        )
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        # Return a graceful failure response
        result = QueryResult(
            answer=f"I encountered an error while processing your question: {str(e)}. Please try again.",
            confidence=0.1,
            citations=[],
            conflicts=conflicts,
            lessons_learned=[]
        )
        return result

    # Step 4: Surface lessons learned (if enabled)
    if include_lessons:
        try:
            lessons = surface_lessons_learned(
                question=question,
                answer_context=result.answer,
                chunks=chunks
            )
            # Update result with lessons (create new QueryResult since Pydantic models are immutable by default)
            result = QueryResult(
                answer=result.answer,
                confidence=result.confidence,
                citations=result.citations,
                conflicts=result.conflicts,
                lessons_learned=lessons
            )
            if lessons:
                logger.info(f"Surfaced {len(lessons)} lessons learned")
        except Exception as e:
            logger.error(f"Lessons learned surfacing failed: {e}")
            # Don't fail the query, just skip lessons

    logger.info(
        f"Query complete: confidence={result.confidence:.2f}, "
        f"citations={len(result.citations)}, "
        f"conflicts={len(result.conflicts)}, "
        f"lessons={len(result.lessons_learned)}"
    )

    # Append retrieval mode (Person B)
    result.retrieval_mode = retrieval_mode

    # Append root cause chain only for incident-related queries (Person B)
    from .rca import is_incident_query, build_root_cause_chain
    if is_incident_query(question, chunks):
        try:
            result.root_cause_chain = build_root_cause_chain(question, chunks)
        except Exception as rca_err:
            logger.warning(f"RCA chain failed: {rca_err}")

    return result


def get_all_known_conflicts(force_refresh: bool = False) -> List[Conflict]:
    """
    Get ALL known conflicts across the entire knowledge base.

    This is used by Person 4's dashboard to display a "flagged conflicts"
    panel showing all contradictions and staleness issues, not just those
    related to the current query.

    Results are cached for 5 minutes by default.

    Args:
        force_refresh: If True, bypass cache and recompute all conflicts

    Returns:
        List of all Conflict objects in the system

    Example:
        >>> from rag_engine import get_all_known_conflicts
        >>> conflicts = get_all_known_conflicts()
        >>> for c in conflicts:
        ...     print(f"[{c.severity.upper()}] {c.entity}: {c.explanation}")
    """
    return _get_all_conflicts(force_refresh=force_refresh)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def quick_answer(question: str) -> str:
    """
    Quick answer without conflict detection or lessons learned.
    Useful for simple lookups or when latency is critical.

    Args:
        question: The user's question

    Returns:
        Just the answer text (not the full QueryResult)
    """
    result = answer_query(
        question=question,
        top_k=3,
        include_conflicts=False,
        include_lessons=False
    )
    return result.answer


def get_conflicts_for_equipment(equipment_tag: str) -> List[Conflict]:
    """
    Get all conflicts for a specific piece of equipment.

    Args:
        equipment_tag: The equipment identifier (e.g., "PSV-101")

    Returns:
        List of conflicts involving that equipment
    """
    all_conflicts = get_all_known_conflicts()
    return [c for c in all_conflicts if c.entity == equipment_tag]


# ---------------------------------------------------------------------------
# Health Check / Validation
# ---------------------------------------------------------------------------

def validate_against_contradictions_md() -> dict:
    """
    Validate that the system correctly detects the planted contradictions.

    This function should be run to verify acceptance criteria against
    data/CONTRADICTIONS.md before the hour 6 deadline.

    Returns:
        Dict with pass/fail status for each planted contradiction
    """
    results = {
        'PSV-101_relief_pressure': {'status': 'unknown', 'details': ''},
        'PUMP-203_inspection_interval': {'status': 'unknown', 'details': ''},
        'HX-301_cleaning_frequency': {'status': 'unknown', 'details': ''}
    }

    all_conflicts = get_all_known_conflicts(force_refresh=True)

    for conflict in all_conflicts:
        # Check PSV-101 relief pressure
        if conflict.entity == 'PSV-101' and 'pressure' in conflict.parameter.lower():
            expected_contradiction = conflict.risk_type == 'direct_contradiction'
            results['PSV-101_relief_pressure'] = {
                'status': 'PASS' if expected_contradiction else 'FAIL',
                'details': f"Found: {conflict.value_a} vs {conflict.value_b}, type={conflict.risk_type}"
            }

        # Check PUMP-203 inspection interval (should be decay)
        if conflict.entity == 'PUMP-203' and 'inspection' in conflict.parameter.lower():
            expected_decay = conflict.risk_type == 'decay'
            results['PUMP-203_inspection_interval'] = {
                'status': 'PASS' if expected_decay else 'FAIL',
                'details': f"Found: {conflict.value_a} vs {conflict.value_b}, type={conflict.risk_type}"
            }

        # Check HX-301 cleaning frequency (should be decay)
        if conflict.entity == 'HX-301' and 'cleaning' in conflict.parameter.lower():
            expected_decay = conflict.risk_type == 'decay'
            results['HX-301_cleaning_frequency'] = {
                'status': 'PASS' if expected_decay else 'FAIL',
                'details': f"Found: {conflict.value_a} vs {conflict.value_b}, type={conflict.risk_type}"
            }

    # Check for any not found
    for key, value in results.items():
        if value['status'] == 'unknown':
            value['status'] = 'FAIL'
            value['details'] = 'Conflict not detected'

    return results


# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------

__all__ = [
    'answer_query',
    'get_all_known_conflicts',
    'quick_answer',
    'get_conflicts_for_equipment',
    'validate_against_contradictions_md'
]
