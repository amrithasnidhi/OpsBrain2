# shared/schemas.py — CONTRACT FILE. Do not edit without team agreement.
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import date

class ChunkMetadata(BaseModel):
    doc_id: str
    doc_type: Literal["manual", "sop", "maintenance_log", "incident_report", "inspection_report"]
    source_file: str
    page_or_row: Optional[str] = None
    equipment_tags: List[str] = []
    section_title: Optional[str] = None
    doc_date: Optional[date] = None      # publication / log date, used for decay detection
    ingested_at: str

class Claim(BaseModel):
    id: str
    doc_id: str
    chunk_id: str
    equipment_tag: str
    parameter_name: str                  # e.g. "inspection_interval_months", "max_pressure_psi"
    value: str                           # kept as string, cast downstream
    unit: Optional[str] = None
    effective_date: Optional[date] = None
    source_text: str
    confidence: float

class Incident(BaseModel):
    id: str
    doc_id: str
    chunk_id: str
    equipment_tag: Optional[str]
    incident_type: str
    description: str
    date: Optional[date]
    severity: Literal["low", "medium", "high", "critical"]

class Citation(BaseModel):
    doc_id: str
    source_file: str
    page_or_row: Optional[str]
    excerpt: str

class Conflict(BaseModel):
    entity: str
    parameter: str
    source_a: Citation
    value_a: str
    source_b: Citation
    value_b: str
    explanation: str
    severity: Literal["low", "medium", "high"]
    risk_type: Literal["direct_contradiction", "decay"]
    # --- Extended fields (Person A fills these in) ---
    risk_score: Optional[float] = None
    business_impact: Optional[str] = None
    resolution: Optional[Literal["temporal_supersession", "unresolved"]] = None
    authoritative_source: Optional[Citation] = None
    superseded_source: Optional[Citation] = None


# === NEW MODELS FOR ROUND 2 ===

class ConfidenceBreakdown(BaseModel):
    score: float
    reasons: List[str]
    warnings: List[str] = []


class RootCauseChain(BaseModel):
    incident: Optional[Incident] = None
    related_claims: List[Claim] = []
    related_conflicts: List[Conflict] = []
    similar_incidents: List[Incident] = []
    likely_root_cause: str
    recommended_checks: List[str] = []


class ComplianceGap(BaseModel):
    standard: str
    requirement: str
    equipment_tag: str
    status: Literal["compliant", "gap", "unknown"]
    details: str


class StalenessRow(BaseModel):
    equipment_tag: str
    required_interval: str
    last_inspection_date: Optional[date] = None
    days_overdue: int
    status: Literal["ok", "warning", "overdue"]


class KnowledgeCaptureRequest(BaseModel):
    expert_name: str
    equipment_tag: str
    knowledge_type: Literal["undocumented_procedure", "tribal_knowledge", "failure_pattern"]
    free_text: str


class QueryResult(BaseModel):
    answer: str
    confidence: float
    citations: List[Citation]
    conflicts: List[Conflict]
    lessons_learned: List[Incident]
    # --- Extended fields ---
    confidence_breakdown: Optional[ConfidenceBreakdown] = None  # Person C fills this in
    root_cause_chain: Optional[RootCauseChain] = None           # Person B fills this in
    retrieval_mode: Optional[Literal["dense", "hybrid"]] = None # Person B fills this in
