"""Core API routes - Query, Conflicts, Health, Graph"""
import os
import sys
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from rag_engine.engine import answer_query, get_all_known_conflicts
from knowledge_graph.graph import build_graph
from ingestion.pipeline import run_pipeline
from knowledge_graph.extractor import process_manifest

router = APIRouter(prefix="/api", tags=["core"])


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
def query_rag(request: QueryRequest):
    try:
        result = answer_query(request.question)
        return result.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts")
def get_conflicts():
    try:
        conflicts = get_all_known_conflicts()
        return [c.model_dump(mode="json") for c in conflicts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/graph")
def get_graph():
    try:
        G = build_graph()
        nodes = []
        for n, d in G.nodes(data=True):
            node_type = d.get("type", "unknown")
            color = "#3b82f6" if node_type == "equipment" else "#9ca3af"
            nodes.append({"id": n, "label": d.get("name", n), "group": node_type, "color": color})

        links = []
        for u, v, d in G.edges(data=True):
            edge_type = d.get("type", "")
            color = "#ef4444" if edge_type.lower() == "conflict" else "#9ca3af"
            links.append({"source": u, "target": v, "label": edge_type, "color": color})

        return {"nodes": nodes, "links": links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
def ingest_document(file: UploadFile = File(...)):
    try:
        # Create a temporary directory for the upload
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        temp_dir = base_dir / "data" / "temp_upload"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = temp_dir / file.filename
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run the ingestion pipeline on the temporary directory
        result = run_pipeline(str(temp_dir), "industrial_docs", str(base_dir / "chroma_db"))
        
        # Run the knowledge graph extraction on the newly created manifest
        process_manifest()
        
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
        
        return {
            "filename": file.filename,
            "chunks_ingested": result["chunks_ingested"],
            "conflict_count": result["conflict_count"]
        }
    except Exception as e:
        # Ensure cleanup on error if temp_dir exists
        if 'temp_dir' in locals() and temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=str(e))
