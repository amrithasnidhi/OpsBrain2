"""Tests for ingestion/chunker.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.chunker import Chunk, chunk_document, chunk_prose, chunk_row

_PROSE_SEGMENT = {
    "text": (
        "Compressor-C1 operates at a maximum pressure of 150 psi.\n\n"
        "The unit must be inspected semi-annually by a certified technician.\n\n"
        "Valve-V12 requires a 90-day inspection interval per the OEM specification.\n\n"
        "Pump-P3 cooldown: 15 minutes minimum after emergency shutdown.\n\n"
        "All maintenance must be logged in the facility work-order system."
    ),
    "page_or_row": "1",
    "source_file": "test_doc.pdf",
}

_ROW_SEGMENT = {
    "text": "work_order_id: WO-001 | equipment_tag: Compressor-C1 | date: 2025-01-15",
    "page_or_row": "2",
    "source_file": "maintenance_log.xlsx",
}


# ----- chunk_prose ------------------------------------------------------------

def test_chunk_prose_returns_chunks():
    chunks = chunk_prose(_PROSE_SEGMENT)
    assert len(chunks) >= 1


def test_chunk_prose_chunk_type():
    chunks = chunk_prose(_PROSE_SEGMENT)
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_prose_text_is_non_empty():
    chunks = chunk_prose(_PROSE_SEGMENT)
    assert all(c.text.strip() for c in chunks)


def test_chunk_prose_index_is_sequential():
    chunks = chunk_prose(_PROSE_SEGMENT, base_index=0)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_prose_respects_max_tokens():
    """No chunk should significantly exceed max_tokens * 4 chars."""
    max_tokens = 100
    chunks = chunk_prose(_PROSE_SEGMENT, max_tokens=max_tokens)
    for c in chunks:
        char_limit = max_tokens * 4 * 2  # allow 2× headroom for single-para overshoot
        assert len(c.text) <= char_limit, f"Chunk too large: {len(c.text)} chars"


def test_chunk_prose_all_content_preserved():
    """Union of all chunk texts should contain the key planted values."""
    chunks = chunk_prose(_PROSE_SEGMENT)
    combined = " ".join(c.text for c in chunks)
    assert "150 psi" in combined
    assert "Compressor-C1" in combined
    assert "Valve-V12" in combined


def test_chunk_prose_base_index_offset():
    chunks = chunk_prose(_PROSE_SEGMENT, base_index=10)
    assert chunks[0].chunk_index == 10


def test_chunk_prose_large_paragraph_split():
    """A paragraph longer than max_tokens should be split at sentence level."""
    long_para = "This is sentence number {}. " * 50
    seg = {"text": long_para.format(*range(50)), "page_or_row": "1", "source_file": "f.pdf"}
    chunks = chunk_prose(seg, max_tokens=50)
    assert len(chunks) > 1


# ----- chunk_row --------------------------------------------------------------

def test_chunk_row_returns_single_chunk():
    chunk = chunk_row(_ROW_SEGMENT, row_index=5)
    assert isinstance(chunk, Chunk)
    assert chunk.chunk_index == 5
    assert chunk.text == _ROW_SEGMENT["text"]
    assert chunk.page_or_row == "2"


# ----- chunk_document dispatcher ----------------------------------------------

def test_chunk_document_maintenance_log():
    segments = [_ROW_SEGMENT, _ROW_SEGMENT]
    chunks = chunk_document(segments, "maintenance_log")
    assert len(chunks) == 2
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_chunk_document_manual_uses_prose():
    segments = [_PROSE_SEGMENT]
    chunks = chunk_document(segments, "manual")
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_document_sop_uses_prose():
    segments = [_PROSE_SEGMENT]
    chunks = chunk_document(segments, "sop")
    assert len(chunks) >= 1


def test_chunk_document_incident_report():
    segments = [_PROSE_SEGMENT]
    chunks = chunk_document(segments, "incident_report")
    assert len(chunks) >= 1


def test_chunk_document_multi_segment_index_continuity():
    """chunk_index must be unique and sequential across multiple segments."""
    segments = [_PROSE_SEGMENT, _PROSE_SEGMENT]
    chunks = chunk_document(segments, "manual")
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks))), f"Indices not sequential: {indices}"
