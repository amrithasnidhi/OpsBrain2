# rag_engine/qa.py
"""
Question-Answering module using LLM for generation.

Takes retrieved chunks and generates answers with citations.
Computes confidence scores based on retrieval quality and source agreement.

Supports multiple LLM backends:
- Anthropic Claude (paid, best quality)
- Groq (free tier)
- Ollama (local, free)
"""

import os
import json
import logging
from typing import List, Optional, Tuple

from shared.schemas import QueryResult, Citation, Conflict, Incident
from .retriever import Chunk
from .llm import get_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert industrial knowledge assistant for a plant operations team.
Your job is to answer questions ONLY using the provided document excerpts.

CRITICAL RULES:
1. Only answer based on the provided context. Never use outside knowledge.
2. If the context doesn't contain enough information, say "I don't have sufficient information to answer this question based on the available documents."
3. Always cite which document(s) you're using (by source_file and page/row).
4. If you find conflicting information, point it out explicitly.
5. Be precise with numbers, units, and technical specifications.
6. If you're uncertain about something, express that uncertainty clearly.

Respond in a clear, professional manner suitable for plant operators and engineers."""


def _build_context_prompt(chunks: List[Chunk]) -> str:
    """Build the context section from retrieved chunks."""
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        meta = chunk.metadata
        source_info = f"[Source {i}] {meta.source_file}"
        if meta.page_or_row:
            source_info += f", {meta.page_or_row}"
        if meta.doc_type:
            source_info += f" (Type: {meta.doc_type})"
        if meta.doc_date:
            source_info += f" (Date: {meta.doc_date})"

        context_parts.append(f"{source_info}\n{chunk.content}")

    return "\n\n---\n\n".join(context_parts)


def _build_user_prompt(question: str, context: str) -> str:
    """Build the user prompt with question and context."""
    return f"""Based on the following document excerpts, please answer the question.

DOCUMENT EXCERPTS:
{context}

QUESTION: {question}

Please provide a clear answer citing the relevant sources. If information is incomplete or uncertain, state that explicitly."""


# ---------------------------------------------------------------------------
# Confidence Scoring
# ---------------------------------------------------------------------------

def compute_confidence_score(
    chunks: List[Chunk],
    citations_used: int,
    answer_length: int
) -> float:
    """
    Compute a confidence score for the answer.

    Formula:
    - Base score from average retrieval similarity (0-0.4)
    - Bonus for multiple independent sources agreeing (0-0.3)
    - Bonus for relevant citations used (0-0.2)
    - Penalty for very short answers that might indicate uncertainty (0-0.1)

    The formula prioritizes:
    1. High retrieval similarity (documents are semantically close to question)
    2. Multi-source agreement (multiple docs say similar things)
    3. Citation coverage (answer uses the retrieved sources)

    Returns a score between 0.0 and 1.0.
    """
    if not chunks:
        return 0.1  # Minimum confidence for no-context answers

    # Component 1: Average retrieval similarity (max 0.4)
    avg_similarity = sum(c.similarity_score for c in chunks) / len(chunks)
    similarity_score = avg_similarity * 0.4

    # Component 2: Multi-source agreement (max 0.3)
    # Check if multiple documents cover the same equipment/topic
    doc_ids = set(c.metadata.doc_id for c in chunks)
    equipment_coverage = {}
    for chunk in chunks:
        for tag in chunk.metadata.equipment_tags:
            if tag not in equipment_coverage:
                equipment_coverage[tag] = set()
            equipment_coverage[tag].add(chunk.metadata.doc_id)

    # Higher score if same equipment mentioned in multiple docs
    if equipment_coverage:
        max_coverage = max(len(docs) for docs in equipment_coverage.values())
        agreement_score = min(0.3, (max_coverage - 1) * 0.15)
    else:
        agreement_score = 0.0

    # Component 3: Citation utilization (max 0.2)
    # Reward for actually using retrieved chunks in the answer
    if citations_used > 0:
        citation_ratio = min(1.0, citations_used / len(chunks))
        citation_score = citation_ratio * 0.2
    else:
        citation_score = 0.0

    # Component 4: Answer substantiveness (max 0.1)
    # Very short answers might indicate uncertainty
    if answer_length > 200:
        substantive_score = 0.1
    elif answer_length > 100:
        substantive_score = 0.07
    elif answer_length > 50:
        substantive_score = 0.04
    else:
        substantive_score = 0.0

    total = similarity_score + agreement_score + citation_score + substantive_score

    # Clamp to [0.1, 0.95] - never fully confident, never totally unsure
    return max(0.1, min(0.95, total))


def build_breakdown(chunks: List[Chunk], citations_used: int, answer_length: int, question: str) -> 'ConfidenceBreakdown':
    from shared.schemas import ConfidenceBreakdown
    from rag_engine.conflicts import get_all_known_conflicts
    from rag_engine.retriever import extract_equipment_tags, get_all_equipment_tags_from_chunks

    score = compute_confidence_score(chunks, citations_used, answer_length)
    reasons = []
    warnings = []

    if not chunks:
        warnings.append("No context documents found")
        return ConfidenceBreakdown(score=score, reasons=reasons, warnings=warnings)

    # Multi-source agreement reason
    doc_ids = set(c.metadata.doc_id for c in chunks)
    equipment_coverage = {}
    for chunk in chunks:
        for tag in chunk.metadata.equipment_tags:
            if tag not in equipment_coverage:
                equipment_coverage[tag] = set()
            equipment_coverage[tag].add(chunk.metadata.doc_id)
            
    if equipment_coverage:
        max_coverage = max(len(docs) for docs in equipment_coverage.values())
        if max_coverage > 1:
            reasons.append(f"{max_coverage} independent chunks agree on this value")
            
    if len(doc_ids) == 1:
        warnings.append("Only 1 chunk found")

    # Document freshness logic (approximate)
    import datetime
    today = datetime.date.today()
    doc_dates = [c.metadata.doc_date for c in chunks if c.metadata.doc_date]
    if doc_dates:
        avg_age_days = sum((today - d).days for d in doc_dates) / len(doc_dates)
        avg_age_months = int(avg_age_days / 30)
        if avg_age_months > 36:
            warnings.append(f"Source document is {avg_age_months // 12} years old")
        else:
            reasons.append(f"Source documents are recent (avg. {avg_age_months} months old)")
            
    # Conflicts for entity
    equipment_tags = extract_equipment_tags(question)
    chunk_tags = get_all_equipment_tags_from_chunks(chunks)
    equipment_tags = list(set(equipment_tags + chunk_tags))
    
    if equipment_tags:
        all_conflicts = get_all_known_conflicts()
        entity_conflicts = [c for c in all_conflicts if c.entity in equipment_tags]
        if entity_conflicts:
            warnings.append(f"{len(entity_conflicts)} conflicting claim(s) exist for {', '.join(equipment_tags)}")

    return ConfidenceBreakdown(score=score, reasons=reasons, warnings=warnings)



# ---------------------------------------------------------------------------
# Citation Extraction
# ---------------------------------------------------------------------------

def extract_citations_from_chunks(
    chunks: List[Chunk],
    answer: str
) -> List[Citation]:
    """
    Build Citation objects from chunks that appear to be used in the answer.
    Uses simple heuristics to determine which chunks were actually cited.
    """
    citations = []

    for chunk in chunks:
        # Check if the source file is mentioned in the answer
        source_mentioned = chunk.metadata.source_file.lower() in answer.lower()

        # Check if key content from the chunk appears in the answer
        # Extract some key phrases from the chunk
        chunk_words = set(chunk.content.lower().split())
        answer_words = set(answer.lower().split())

        # Check for significant overlap (at least 5 shared words beyond common ones)
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                       'to', 'of', 'and', 'in', 'for', 'on', 'with', 'at', 'by'}
        meaningful_overlap = len((chunk_words & answer_words) - common_words)

        if source_mentioned or meaningful_overlap >= 5:
            # Create excerpt (first 150 chars of chunk or key sentence)
            excerpt = chunk.content[:200].strip()
            if len(chunk.content) > 200:
                excerpt += "..."

            citation = Citation(
                doc_id=chunk.metadata.doc_id,
                source_file=chunk.metadata.source_file,
                page_or_row=chunk.metadata.page_or_row,
                excerpt=excerpt
            )
            citations.append(citation)

    return citations


# ---------------------------------------------------------------------------
# Main QA Function
# ---------------------------------------------------------------------------

def generate_answer(
    question: str,
    chunks: List[Chunk],
    conflicts: Optional[List[Conflict]] = None,
    lessons: Optional[List[Incident]] = None
) -> QueryResult:
    """
    Generate an answer to the question using Claude and the retrieved chunks.

    Args:
        question: The user's question
        chunks: Retrieved document chunks
        conflicts: Pre-detected conflicts to include in result
        lessons: Pre-detected lessons learned to include in result

    Returns:
        QueryResult with answer, confidence, citations, conflicts, and lessons
    """
    conflicts = conflicts or []
    lessons = lessons or []

    # Handle no-context case
    if not chunks:
        return QueryResult(
            answer="I don't have sufficient information to answer this question. No relevant documents were found in the knowledge base.",
            confidence=0.1,
            citations=[],
            conflicts=conflicts,
            lessons_learned=lessons
        )

    # Build context from chunks
    context = _build_context_prompt(chunks)
    user_prompt = _build_user_prompt(question, context)

    # Get answer from LLM (with automatic fallback to free providers)
    llm = get_llm()
    try:
        answer = llm.generate(user_prompt, system=SYSTEM_PROMPT, max_tokens=1500)
        logger.debug(f"Got answer from {llm.provider_name}")

        # Check if we got a mock response
        if answer.startswith("[Mock response"):
            answer = _generate_fallback_answer(question, chunks)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = _generate_fallback_answer(question, chunks)

    # Extract citations
    citations = extract_citations_from_chunks(chunks, answer)

    # Compute confidence
    confidence = compute_confidence_score(
        chunks=chunks,
        citations_used=len(citations),
        answer_length=len(answer)
    )

    return QueryResult(
        answer=answer,
        confidence=confidence,
        citations=citations,
        conflicts=conflicts,
        lessons_learned=lessons
    )


def _generate_fallback_answer(question: str, chunks: List[Chunk]) -> str:
    """
    Generate a basic answer without Claude API.
    Used for development/testing when API isn't available.
    """
    if not chunks:
        return "No relevant information found in the knowledge base."

    # Build a simple extractive answer
    answer_parts = [
        f"Based on the available documents, here's what I found regarding your question:\n"
    ]

    for chunk in chunks[:3]:  # Use top 3 chunks
        meta = chunk.metadata
        source = f"{meta.source_file}"
        if meta.page_or_row:
            source += f" ({meta.page_or_row})"

        # Extract relevant sentences (simple heuristic)
        sentences = chunk.content.split('.')
        relevant = [s.strip() for s in sentences if len(s.strip()) > 20][:2]

        if relevant:
            answer_parts.append(f"\nFrom {source}:")
            for sent in relevant:
                answer_parts.append(f"- {sent}.")

    answer_parts.append(
        "\n\n[Note: This is a fallback response generated without the full AI model. "
        "For more detailed analysis, ensure ANTHROPIC_API_KEY is configured.]"
    )

    return "\n".join(answer_parts)
