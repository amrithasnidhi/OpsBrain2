"""Core API routes - Query, Conflicts, Health, Graph"""
import os
import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from rag_engine.engine import answer_query, get_all_known_conflicts
from knowledge_graph.graph import build_graph

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
        nodes = [{"id": n, "label": d.get("name", n), "group": d.get("type", "unknown")} for n, d in G.nodes(data=True)]
        edges = [{"source": u, "target": v, "label": d.get("type", "")} for u, v, d in G.edges(data=True)]
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
