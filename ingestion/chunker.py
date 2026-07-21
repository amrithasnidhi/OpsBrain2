"""
Chunking strategies for different document types.

Prose (manuals, SOPs, incidents):  recursive paragraph chunking, ~150-300 tokens, ~15% overlap.
Maintenance log (Excel):           one chunk per row — preserves per-work-order granularity.
Inspection reports (OCR):          page-level prose chunking (same as prose path).

Section/heading awareness: if a segment carries section_title (from docx_parser or explicit
heading detection), that title propagates to every child chunk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page_or_row: Optional[str] = None
    section_title: Optional[str] = None
    source_file: str = ""


# ----- helpers ----------------------------------------------------------------

def _token_count(text: str) -> int:
    """Approximate token count: 1 token ≈ 4 characters (conservative for industrial text)."""
    return max(1, len(text) // 4)


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


# ----- core chunkers ----------------------------------------------------------

def chunk_prose(
    segment: dict[str, Any],
    max_tokens: int = 300,
    overlap_tokens: int = 45,
    base_index: int = 0,
) -> list[Chunk]:
    """
    Recursive semantic chunking for prose documents.

    Strategy:
    1. Split text into paragraphs (double-newline boundaries).
    2. Accumulate paragraphs into a window up to max_tokens.
    3. On overflow, emit the current window, then carry over the last few
       paragraphs whose total token count <= overlap_tokens (≈15% of 300).
    4. If a single paragraph exceeds max_tokens, fall back to sentence-level splitting.
    5. Never splits mid-procedure step (steps end with '\n', not mid-sentence).
    """
    text = segment["text"]
    source = segment["source_file"]
    page = segment.get("page_or_row")
    section = segment.get("section_title")

    paragraphs = _split_paragraphs(text)
    chunks: list[Chunk] = []
    window: list[str] = []
    window_tokens = 0
    idx = base_index

    def _emit() -> None:
        nonlocal idx
        if window:
            chunks.append(Chunk(
                text="\n\n".join(window),
                chunk_index=idx,
                page_or_row=page,
                section_title=section,
                source_file=source,
            ))
            idx += 1

    def _carry_over() -> tuple[list[str], int]:
        """Retain trailing paragraphs up to overlap_tokens for the next window."""
        tail: list[str] = []
        tail_t = 0
        for p in reversed(window):
            t = _token_count(p)
            if tail_t + t <= overlap_tokens:
                tail.insert(0, p)
                tail_t += t
            else:
                break
        return tail, tail_t

    for para in paragraphs:
        pt = _token_count(para)

        if pt > max_tokens:
            # Paragraph too large — flush current window first, then sentence-split
            _emit()
            window, window_tokens = [], 0
            sub_window: list[str] = []
            sub_tokens = 0
            for sent in _split_sentences(para):
                st = _token_count(sent)
                if sub_tokens + st > max_tokens and sub_window:
                    chunks.append(Chunk(
                        text=" ".join(sub_window),
                        chunk_index=idx,
                        page_or_row=page,
                        section_title=section,
                        source_file=source,
                    ))
                    idx += 1
                    sub_window = sub_window[-1:]
                    sub_tokens = _token_count(" ".join(sub_window))
                sub_window.append(sent)
                sub_tokens += st
            if sub_window:
                chunks.append(Chunk(
                    text=" ".join(sub_window),
                    chunk_index=idx,
                    page_or_row=page,
                    section_title=section,
                    source_file=source,
                ))
                idx += 1
            continue

        if window_tokens + pt > max_tokens and window:
            _emit()
            window, window_tokens = _carry_over()

        window.append(para)
        window_tokens += pt

    _emit()
    return chunks


def chunk_row(segment: dict[str, Any], row_index: int) -> Chunk:
    """One chunk per Excel row — each work-order record is its own retrievable unit."""
    return Chunk(
        text=segment["text"],
        chunk_index=row_index,
        page_or_row=segment.get("page_or_row"),
        section_title=None,
        source_file=segment["source_file"],
    )


# ----- dispatcher -------------------------------------------------------------

def chunk_document(segments: list[dict[str, Any]], doc_type: str) -> list[Chunk]:
    """
    Dispatch to the correct chunking strategy based on doc_type from ChunkMetadata contract.

    maintenance_log → row-level (one chunk per work order)
    everything else → prose chunking with overlap
    """
    if doc_type == "maintenance_log":
        return [chunk_row(seg, i) for i, seg in enumerate(segments)]

    chunks: list[Chunk] = []
    for seg in segments:
        seg_chunks = chunk_prose(seg, base_index=len(chunks))
        chunks.extend(seg_chunks)
    return chunks
