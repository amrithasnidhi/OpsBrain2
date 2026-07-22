"""
app/backend/routers/ingestion_reasoning.py

Features:
  - POST /api/ingest          — Upload a document file, ingest it, return conflict count
  - POST /api/capture-knowledge — Capture expert knowledge as a searchable chunk
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

# Ensure project root is on the path
_ROOT = Path(__file__).parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.schemas import ChunkMetadata, KnowledgeCaptureRequest
from ingestion.pipeline import _SUPPORTED_EXTS, run_pipeline, make_chunk_id, metadata_to_chroma
from ingestion.chunker import chunk_document
from ingestion.embed import embed_batch
from ingestion.tagger import extract_equipment_tags

logger = logging.getLogger(__name__)

router = APIRouter()

# ChromaDB settings (same as retriever uses)
_CHROMA_PATH = os.environ.get("CHROMADB_PATH", "./data/chromadb")
_COLLECTION  = os.environ.get("CHROMADB_COLLECTION", "opsbrain_chunks")


def _get_collection():
    import chromadb
    client = chromadb.PersistentClient(path=_CHROMA_PATH)
    return client.get_or_create_collection(name=_COLLECTION, metadata={"hnsw:space": "cosine"})


# ──────────────────────────────────────────────────────────────────────────────
# Feature 2 — Document Upload
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/api/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload a document and run the full ingestion pipeline on it.
    Returns the number of chunks ingested and the current total conflict count.
    """
    suffix = Path(file.filename).suffix.lower()

    # Validate file type before touching disk
    if suffix not in _SUPPORTED_EXTS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Supported types: {', '.join(sorted(_SUPPORTED_EXTS))}"
            ),
        )

    # Write to a cross-platform temp directory
    tmp_dir = Path(os.environ.get("TEMP", "/tmp")) / "opsbrain_live_ingest"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / file.filename

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    tmp_path.write_bytes(content)
    logger.info("Uploaded file saved to %s", tmp_path)

    try:
        result = run_pipeline(
            input_dir=str(tmp_dir),
            collection_name=_COLLECTION,
            chroma_path=_CHROMA_PATH,
        )
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")
    finally:
        # Cleanup temp file after ingestion
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    return {
        "status": "ingested",
        "filename": file.filename,
        "chunks_ingested": result.get("chunks_ingested", 0),
        "conflict_count": result.get("conflict_count", 0),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Feature 3 — Knowledge Retention Mode
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/api/capture-knowledge")
async def capture_knowledge(req: KnowledgeCaptureRequest):
    """
    Capture an expert's knowledge as a single chunk stored in ChromaDB.
    The captured text is immediately searchable in subsequent /api/query calls.
    """
    doc_id = f"expert_capture_{uuid4().hex[:8]}"
    ingested_at = datetime.now(timezone.utc).isoformat()

    # Build metadata
    tags = extract_equipment_tags(req.free_text)
    if req.equipment_tag and req.equipment_tag not in tags:
        tags.insert(0, req.equipment_tag)

    chunk_meta = ChunkMetadata(
        doc_id=doc_id,
        doc_type="sop",
        source_file=f"expert:{req.expert_name}",
        section_title="Expert Knowledge Capture",
        equipment_tags=tags,
        ingested_at=ingested_at,
    )

    # Chunk the free text (reuse existing chunker)
    segments = [{"text": req.free_text, "page_or_row": "1", "source_file": f"expert:{req.expert_name}"}]
    try:
        chunks = chunk_document(segments, "sop")
    except Exception as exc:
        logger.error("Chunking failed: %s", exc)
        # Fallback: treat as a single chunk
        from ingestion.chunker import TextChunk
        chunks = [TextChunk(text=req.free_text, chunk_index=0, page_or_row="1", section_title="Expert Knowledge")]

    texts = [c.text for c in chunks]
    chunk_ids = [make_chunk_id(doc_id, c.chunk_index) for c in chunks]
    flat_meta = metadata_to_chroma(chunk_meta)

    # Embed using the same embed_batch function (Voyage AI)
    try:
        embeddings = embed_batch(texts)
    except Exception as exc:
        logger.error("Embedding failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}")

    # Upsert into ChromaDB
    try:
        collection = _get_collection()
        collection.upsert(
            ids=chunk_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=[flat_meta] * len(chunks),
        )
    except Exception as exc:
        logger.error("ChromaDB upsert failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Storage failed: {exc}")

    logger.info("Captured expert knowledge as doc_id=%s (%d chunks)", doc_id, len(chunks))
    return {
        "status": "captured",
        "doc_id": doc_id,
        "chunks_stored": len(chunks),
        "expert_name": req.expert_name,
        "equipment_tag": req.equipment_tag,
    }
