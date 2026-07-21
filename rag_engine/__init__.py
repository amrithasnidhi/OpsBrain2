# rag_engine/__init__.py
"""
RAG Query Engine with Conflict Detection and Lessons Learned Surfacing.

This module provides the core Q&A functionality for the Industrial Knowledge Brain.
Key features:
- Retrieval-Augmented Generation against industrial documents
- Automatic conflict/contradiction detection between sources
- Proactive surfacing of relevant past incidents (lessons learned)
"""

from .engine import answer_query, get_all_known_conflicts

__all__ = ["answer_query", "get_all_known_conflicts"]
