"""
OpsBrain2 API - Thin shell entry point.
Each person adds exactly two lines below to register their router.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OpsBrain2 API")

# CORS middleware - allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROUTER REGISTRATIONS ===
# Each person adds exactly two lines: import + include_router

from app.backend.routers.core import router as core_router
app.include_router(core_router)

# --- Person A (Risk/Compliance) ---
from app.backend.routers.risk_compliance import router as risk_compliance_router
app.include_router(risk_compliance_router)

# --- Person B (Ingestion/Reasoning) adds here ---
# from app.backend.routers.reasoning import router as reasoning_router
# app.include_router(reasoning_router)

# --- Person C (Dashboards/UX) adds here ---
# from app.backend.routers.dashboards import router as dashboards_router
# app.include_router(dashboards_router)
