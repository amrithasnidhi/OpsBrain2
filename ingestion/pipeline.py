"""
Ingestion pipeline: parse → chunk → tag → embed → upsert into ChromaDB.

CLI:
    python -m ingestion.pipeline --input_dir data/raw --collection industrial_docs

Idempotency: chunk IDs are a SHA-256 hash of (doc_id + chunk_index), so re-running
upserts to the same IDs without creating duplicates in ChromaDB.

ChromaDB metadata note: ChunkMetadata.equipment_tags is List[str] but ChromaDB only
accepts scalar metadata values. It is serialised as a comma-joined string
("Compressor-C1,Valve-V12") and must be split by downstream consumers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import chromadb

# Allow `python -m ingestion.pipeline` from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.schemas import ChunkMetadata

from ingestion.chunker import chunk_document
from ingestion.embed import embed_batch
from ingestion.parsers import docx_parser, excel_parser, ocr_parser, pdf_parser
from ingestion.tagger import extract_equipment_tags

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ----- doc type inference -----------------------------------------------------

_NAME_TO_TYPE: dict[str, str] = {
    "incident": "incident_report",
    "near_miss": "incident_report",
    "sop": "sop",
    "procedure": "sop",
    "safety": "sop",
    "emergency": "sop",
    "manual": "manual",
    "oem": "manual",
    "maintenance_log": "maintenance_log",
}

_EXT_TO_TYPE: dict[str, str] = {
    ".xlsx": "maintenance_log",
    ".xls": "maintenance_log",
    ".png": "inspection_report",
    ".jpg": "inspection_report",
    ".jpeg": "inspection_report",
    ".txt": "incident_report",
}

_SUPPORTED_EXTS = {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".txt", ".docx"}


def detect_doc_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in _EXT_TO_TYPE:
        return _EXT_TO_TYPE[ext]
    name = path.stem.lower()
    for keyword, dtype in _NAME_TO_TYPE.items():
        if keyword in name:
            return dtype
    return "manual"


# ----- helpers ----------------------------------------------------------------

def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    """Deterministic 20-char hex ID — guarantees idempotent upserts."""
    return hashlib.sha256(f"{doc_id}:{chunk_index}".encode()).hexdigest()[:20]


def metadata_to_chroma(meta: ChunkMetadata) -> dict:
    """
    Flatten ChunkMetadata to a ChromaDB-compatible dict.
    All values must be str | int | float | bool — no lists or nested objects.
    equipment_tags: List[str] → comma-joined string (e.g. "Compressor-C1,Valve-V12").
    Consumers must split on "," to recover the list.
    """
    return {
        "doc_id": meta.doc_id,
        "doc_type": meta.doc_type,
        "source_file": str(meta.source_file),
        "page_or_row": meta.page_or_row or "",
        "equipment_tags": ",".join(meta.equipment_tags),
        "section_title": meta.section_title or "",
        "doc_date": meta.doc_date.isoformat() if meta.doc_date else "",
        "ingested_at": meta.ingested_at,
    }


def parse_file(path: Path) -> list[dict]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return pdf_parser(str(path))
    if ext in (".xlsx", ".xls"):
        return excel_parser(str(path))
    if ext in (".png", ".jpg", ".jpeg"):
        return ocr_parser(str(path))
    if ext == ".docx":
        return docx_parser(str(path))
    if ext == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        return [{"text": text, "page_or_row": "1", "source_file": str(path)}] if text else []
    return []


# ----- main pipeline ----------------------------------------------------------

def run_pipeline(
    input_dir: str,
    collection_name: str,
    chroma_path: str = "./chroma_db",
) -> dict:
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    manifest: list[dict] = []
    files = sorted(f for f in input_path.iterdir() if f.suffix.lower() in _SUPPORTED_EXTS)
    log.info("Found %d documents in %s", len(files), input_dir)

    for file_path in files:
        doc_id = file_path.stem
        doc_type = detect_doc_type(file_path)
        log.info("Processing %-45s  doc_type=%s", file_path.name, doc_type)

        try:
            segments = parse_file(file_path)
        except Exception as exc:
            log.error("  ✗ Parse failed: %s", exc)
            continue

        if not segments:
            log.warning("  ✗ No content extracted")
            continue

        chunks = chunk_document(segments, doc_type)
        log.info("  → %d chunks", len(chunks))

        chunk_ids: list[str] = []
        texts: list[str] = []
        chroma_metas: list[dict] = []
        ingested_at = datetime.now(timezone.utc).isoformat()

        for chunk in chunks:
            cid = make_chunk_id(doc_id, chunk.chunk_index)
            tags = extract_equipment_tags(chunk.text)
            meta = ChunkMetadata(
                doc_id=doc_id,
                doc_type=doc_type,
                source_file=str(file_path),
                page_or_row=chunk.page_or_row,
                equipment_tags=tags,
                section_title=chunk.section_title,
                doc_date=None,
                ingested_at=ingested_at,
            )
            flat_meta = metadata_to_chroma(meta)

            chunk_ids.append(cid)
            texts.append(chunk.text)
            chroma_metas.append(flat_meta)

            manifest.append({
                "chunk_id": cid,
                "doc_id": doc_id,
                "text": chunk.text,
                "metadata": flat_meta,
            })

        try:
            embeddings = embed_batch(texts)
        except Exception as exc:
            log.error("  ✗ Embedding failed: %s", exc)
            continue
        finally:
            # Voyage AI free tier = 3 RPM. Sleep 21 s between every document's
            # API call so we never exceed the rate limit, even without a paid plan.
            time.sleep(21)

        collection.upsert(
            ids=chunk_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=chroma_metas,
        )
        log.info("  ✓ Upserted %d chunks for doc_id=%s", len(chunks), doc_id)

    # Post-ingestion conflict scan (Feature 1)
    try:
        from rag_engine.conflicts import get_all_known_conflicts
        new_conflicts = get_all_known_conflicts(force_refresh=True)
        conflict_count = len(new_conflicts)
        log.info("Post-ingestion conflict scan: %d conflicts found", conflict_count)
    except Exception as exc:
        log.warning("Conflict scan skipped: %s", exc)
        conflict_count = 0

    # Dump manifest for Person 2 and Person 3
    manifest_path = Path("data/chunks_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)

    log.info(
        "\nDone. %d total chunks | ChromaDB: %s (%s) | Manifest: %s",
        len(manifest), chroma_path, collection_name, manifest_path,
    )
    return {"chunks_ingested": len(manifest), "conflict_count": conflict_count}


# ----- CLI entry point --------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Industrial docs ingestion pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input_dir", default="data/raw", help="Directory of raw documents")
    parser.add_argument("--collection", default="industrial_docs", help="ChromaDB collection name")
    parser.add_argument("--chroma_path", default="./chroma_db", help="ChromaDB persistence path")
    args = parser.parse_args()

    run_pipeline(args.input_dir, args.collection, args.chroma_path)
