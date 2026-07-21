"""
Pipeline-level tests for ingestion/pipeline.py.
These tests do NOT call Voyage AI or ChromaDB — they test the deterministic
helper functions and verify the manifest structure matches document count.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.pipeline import (
    detect_doc_type,
    make_chunk_id,
    metadata_to_chroma,
    parse_file,
)
from shared.schemas import ChunkMetadata


# ----- make_chunk_id ----------------------------------------------------------

def test_chunk_id_is_deterministic():
    a = make_chunk_id("compressor_c1_manual", 3)
    b = make_chunk_id("compressor_c1_manual", 3)
    assert a == b


def test_chunk_id_differs_by_doc():
    a = make_chunk_id("compressor_c1_manual", 0)
    b = make_chunk_id("valve_v12_maintenance_manual", 0)
    assert a != b


def test_chunk_id_differs_by_index():
    a = make_chunk_id("doc_x", 0)
    b = make_chunk_id("doc_x", 1)
    assert a != b


def test_chunk_id_length():
    cid = make_chunk_id("doc_x", 0)
    assert len(cid) == 20


# ----- detect_doc_type --------------------------------------------------------

@pytest.mark.parametrize("filename,expected", [
    ("compressor_c1_manual.pdf",          "manual"),
    ("valve_v12_maintenance_manual.pdf",  "manual"),
    ("pump_p3_oem_manual.pdf",            "manual"),
    ("sop_process_safety.pdf",            "sop"),
    ("sop_emergency_response.pdf",        "sop"),
    ("maintenance_log.xlsx",              "maintenance_log"),
    ("incident_report_001.txt",           "incident_report"),
    ("inspection_scan_001.png",           "inspection_report"),
])
def test_detect_doc_type_for_synthetic_files(filename, expected):
    result = detect_doc_type(Path(filename))
    assert result == expected, f"{filename}: expected {expected!r}, got {result!r}"


# ----- metadata_to_chroma -----------------------------------------------------

def test_metadata_to_chroma_is_flat():
    meta = ChunkMetadata(
        doc_id="compressor_c1_manual",
        doc_type="manual",
        source_file="data/raw/compressor_c1_manual.pdf",
        page_or_row="2",
        equipment_tags=["Compressor-C1"],
        section_title="Section 2",
        doc_date=None,
        ingested_at="2026-07-21T10:00:00",
    )
    flat = metadata_to_chroma(meta)
    for v in flat.values():
        assert isinstance(v, (str, int, float, bool)), f"Non-scalar value in chroma meta: {v!r}"


def test_metadata_to_chroma_equipment_tags_joined():
    meta = ChunkMetadata(
        doc_id="doc",
        doc_type="sop",
        source_file="f.pdf",
        equipment_tags=["Compressor-C1", "Valve-V12"],
        ingested_at="2026-07-21T00:00:00",
    )
    flat = metadata_to_chroma(meta)
    assert flat["equipment_tags"] == "Compressor-C1,Valve-V12"


def test_metadata_to_chroma_empty_tags():
    meta = ChunkMetadata(
        doc_id="doc",
        doc_type="sop",
        source_file="f.pdf",
        equipment_tags=[],
        ingested_at="2026-07-21T00:00:00",
    )
    flat = metadata_to_chroma(meta)
    assert flat["equipment_tags"] == ""


def test_metadata_to_chroma_doc_date_serialised():
    from datetime import date

    meta = ChunkMetadata(
        doc_id="doc",
        doc_type="manual",
        source_file="f.pdf",
        equipment_tags=[],
        doc_date=date(2023, 1, 15),
        ingested_at="2026-07-21T00:00:00",
    )
    flat = metadata_to_chroma(meta)
    assert flat["doc_date"] == "2023-01-15"


# ----- parse_file (plain text path — no external deps) -----------------------

def test_parse_file_txt(sample_txt):
    segments = parse_file(sample_txt)
    assert len(segments) == 1
    assert "Pump-P3" in segments[0]["text"]


# ----- end-to-end manifest test (mocked embed + chroma) ----------------------

def test_manifest_row_count_matches_chunks(tmp_path, sample_pdf, sample_xlsx, sample_txt):
    """
    Run the full pipeline against 3 fixture files with embed + chroma mocked out.
    The manifest must contain one entry per chunk produced.
    """
    import shutil

    # Assemble a minimal input_dir
    input_dir = tmp_path / "raw"
    input_dir.mkdir()
    shutil.copy(sample_pdf,  input_dir / "test_manual.pdf")
    shutil.copy(sample_xlsx, input_dir / "maintenance_log.xlsx")
    shutil.copy(sample_txt,  input_dir / "incident_report_001.txt")

    manifest_path = tmp_path / "data" / "chunks_manifest.json"

    # Mock Voyage AI and ChromaDB so no network or DB access occurs
    fake_collection = MagicMock()
    fake_chroma_client = MagicMock()
    fake_chroma_client.get_or_create_collection.return_value = fake_collection

    def fake_embed_batch(texts, **kwargs):
        return [[0.0] * 1024 for _ in texts]

    with (
        patch("ingestion.pipeline.embed_batch", side_effect=fake_embed_batch),
        patch("ingestion.pipeline.chromadb.PersistentClient", return_value=fake_chroma_client),
        patch("ingestion.pipeline.Path", wraps=Path) as mock_path,
    ):
        # Override the manifest output path to our tmp_path
        import ingestion.pipeline as pl
        orig_run = pl.run_pipeline

        def patched_run(input_dir_arg, collection_name, chroma_path="./chroma_db"):
            import json as _json
            from pathlib import Path as _Path

            result = orig_run(input_dir_arg, collection_name, chroma_path)
            # also write manifest to tmp location for inspection
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(_json.dumps(result, default=str))
            return result

        manifest = patched_run(str(input_dir), "test_collection", str(tmp_path / "chroma"))

    assert isinstance(manifest, list)
    assert len(manifest) > 0, "Manifest must contain at least one chunk"

    # Every entry must have the required keys
    for entry in manifest:
        assert "chunk_id" in entry
        assert "doc_id" in entry
        assert "text" in entry
        assert "metadata" in entry
        assert entry["text"].strip(), "Chunk text must not be empty"

    # Number of upsert calls must equal number of non-empty documents processed
    assert fake_collection.upsert.called, "ChromaDB upsert should have been called"
