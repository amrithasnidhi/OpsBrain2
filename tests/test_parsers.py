"""Tests for ingestion/parsers.py — one test per parser function."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.parsers import excel_parser, ocr_parser, pdf_parser


# ----- pdf_parser -------------------------------------------------------------

def test_pdf_parser_returns_segments(sample_pdf):
    segments = pdf_parser(str(sample_pdf))
    assert len(segments) >= 1, "Expected at least one page segment"


def test_pdf_parser_segment_structure(sample_pdf):
    segments = pdf_parser(str(sample_pdf))
    seg = segments[0]
    assert "text" in seg
    assert "page_or_row" in seg
    assert "source_file" in seg


def test_pdf_parser_contains_known_text(sample_pdf):
    segments = pdf_parser(str(sample_pdf))
    all_text = " ".join(s["text"] for s in segments)
    assert "Compressor-C1" in all_text
    assert "150 psi" in all_text


def test_pdf_parser_page_numbers_are_strings(sample_pdf):
    segments = pdf_parser(str(sample_pdf))
    for seg in segments:
        assert isinstance(seg["page_or_row"], str)


# ----- excel_parser -----------------------------------------------------------

def test_excel_parser_returns_rows(sample_xlsx):
    segments = excel_parser(str(sample_xlsx))
    assert len(segments) == 3, "Expected 3 data rows (header excluded)"


def test_excel_parser_segment_structure(sample_xlsx):
    segments = excel_parser(str(sample_xlsx))
    for seg in segments:
        assert "text" in seg
        assert "page_or_row" in seg
        assert "row_data" in seg


def test_excel_parser_text_contains_column_values(sample_xlsx):
    segments = excel_parser(str(sample_xlsx))
    texts = [s["text"] for s in segments]
    assert any("Compressor-C1" in t for t in texts)
    assert any("Valve-V12" in t for t in texts)


def test_excel_parser_skips_empty_rows(tmp_path):
    """Rows where all cells are None should not produce segments."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["id", "tag"])
    ws.append([None, None])
    ws.append(["WO-X", "Pump-P3"])
    path = tmp_path / "empty_rows.xlsx"
    wb.save(str(path))

    segments = excel_parser(str(path))
    assert len(segments) == 1, "Only the non-empty row should produce a segment"


# ----- ocr_parser -------------------------------------------------------------

def test_ocr_parser_returns_list(sample_png):
    try:
        import pytesseract
    except ImportError:
        pytest.skip("pytesseract not installed")

    try:
        segments = ocr_parser(str(sample_png))
        assert isinstance(segments, list)
    except Exception as exc:
        if "tesseract" in str(exc).lower():
            pytest.skip(f"Tesseract binary not found: {exc}")
        raise


def test_ocr_parser_segment_has_required_keys(sample_png):
    try:
        import pytesseract
    except ImportError:
        pytest.skip("pytesseract not installed")

    try:
        segments = ocr_parser(str(sample_png))
        if segments:
            assert "text" in segments[0]
            assert segments[0]["page_or_row"] == "1"
    except Exception as exc:
        if "tesseract" in str(exc).lower():
            pytest.skip(f"Tesseract binary not found: {exc}")
        raise
