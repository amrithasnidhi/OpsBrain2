import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add root directory to sys.path to allow importing rag_engine and knowledge_graph
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rag_engine.engine import answer_query, get_all_known_conflicts
from knowledge_graph.graph import build_graph

app = FastAPI(title="OpsBrain2 API")

# Allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.post("/api/query")
def query_rag(request: QueryRequest):
    try:
        # returns QueryResult
        result = answer_query(request.question)
        return result.model_dump(mode="json")
    except Exception as e:
        # Graceful error handling for missing API keys or other issues
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conflicts")
def get_conflicts():
    try:
        # returns list[Conflict]
        conflicts = get_all_known_conflicts()
        return [c.model_dump(mode="json") for c in conflicts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/graph")
def get_graph():
    try:
        G = build_graph()
        nodes = [{"id": n, "label": d.get("name", n), "group": d.get("type", "unknown")} for n, d in G.nodes(data=True)]
        edges = [{"source": u, "target": v, "label": d.get("type", "")} for u, v, d in G.edges(data=True)]
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
