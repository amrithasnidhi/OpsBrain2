from dataclasses import dataclass
from typing import Optional

@dataclass
class Claim:
    id: str
    doc_id: str
    chunk_id: str
    equipment_tag: str
    parameter_name: str
    value: str
    unit: Optional[str] = None
    effective_date: Optional[str] = None
    source_text: Optional[str] = None
    confidence: float = 1.0

@dataclass
class Incident:
    id: str
    doc_id: str
    chunk_id: str
    equipment_tag: str
    incident_type: str
    description: str
    date: str
    severity: str
