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

class QueryResult(BaseModel):
    answer: str
    confidence: float
    citations: List[Citation]
    conflicts: List[Conflict]
    lessons_learned: List[Incident]
