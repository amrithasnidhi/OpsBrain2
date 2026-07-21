# rag_engine/fixtures.py
"""
Development fixtures matching schemas from Person 1 (ChromaDB) and Person 2 (Knowledge Graph).

These fixtures are used when real dependencies aren't available yet.
They include 3 PLANTED CONTRADICTIONS for acceptance testing:
  1. PSV-101 relief pressure: Manual says 150 psi, SOP says 145 psi (direct_contradiction)
  2. PUMP-203 inspection interval: Manual says 6 months, but last inspection was 9 months ago (decay)
  3. HX-301 tube cleaning: Old SOP says quarterly, new maintenance log shows monthly (decay/evolution)

See data/CONTRADICTIONS.md for full test specification.
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import ChunkMetadata, Claim, Incident, Citation

# ---------------------------------------------------------------------------
# MOCK CHUNKS (simulating Person 1's ChromaDB collection)
# ---------------------------------------------------------------------------

class Chunk:
    """Represents a document chunk with content and metadata."""
    def __init__(self, chunk_id: str, content: str, metadata: ChunkMetadata, similarity_score: float = 0.0):
        self.chunk_id = chunk_id
        self.content = content
        self.metadata = metadata
        self.similarity_score = similarity_score


# Pre-defined chunks with planted contradictions
MOCK_CHUNKS: List[Chunk] = [
    # --- PSV-101 CONTRADICTION (Manual vs SOP) ---
    Chunk(
        chunk_id="chunk_001",
        content="""PSV-101 Pressure Safety Valve Specifications:
        - Set pressure: 150 psi
        - Relief capacity: 5000 lb/hr
        - Material: Stainless Steel 316
        - Inspection interval: 12 months
        The relief pressure of 150 psi must not be exceeded under normal operating conditions.""",
        metadata=ChunkMetadata(
            doc_id="DOC-MAN-001",
            doc_type="manual",
            source_file="equipment_manual_psv101.pdf",
            page_or_row="Page 12",
            equipment_tags=["PSV-101"],
            section_title="Pressure Safety Valve Specifications",
            doc_date=date(2023, 1, 15),
            ingested_at="2024-01-10T10:00:00Z"
        )
    ),
    Chunk(
        chunk_id="chunk_002",
        content="""Standard Operating Procedure: PSV-101 Relief Test
        IMPORTANT: Verify relief pressure is set to 145 psi before returning to service.
        The 145 psi setpoint provides adequate margin below vessel MAWP.
        Document all test results in the maintenance log.""",
        metadata=ChunkMetadata(
            doc_id="DOC-SOP-001",
            doc_type="sop",
            source_file="sop_psv_testing.pdf",
            page_or_row="Page 3",
            equipment_tags=["PSV-101"],
            section_title="Relief Valve Test Procedure",
            doc_date=date(2024, 6, 20),
            ingested_at="2024-01-10T10:05:00Z"
        )
    ),

    # --- PUMP-203 DECAY (Overdue inspection) ---
    Chunk(
        chunk_id="chunk_003",
        content="""PUMP-203 Centrifugal Pump Maintenance Requirements:
        - Bearing inspection: Every 6 months
        - Seal replacement: Annually or as needed
        - Alignment check: After any maintenance
        - Vibration monitoring: Monthly
        Failure to maintain 6-month inspection intervals may void warranty.""",
        metadata=ChunkMetadata(
            doc_id="DOC-MAN-002",
            doc_type="manual",
            source_file="pump_maintenance_manual.pdf",
            page_or_row="Page 45",
            equipment_tags=["PUMP-203"],
            section_title="Preventive Maintenance Schedule",
            doc_date=date(2022, 8, 10),
            ingested_at="2024-01-10T10:10:00Z"
        )
    ),
    Chunk(
        chunk_id="chunk_004",
        content="""Maintenance Log Entry - PUMP-203
        Date: 2024-10-15
        Technician: J. Smith
        Work performed: Routine bearing inspection completed.
        Bearings in good condition, no replacement needed.
        Next scheduled inspection: April 2025""",
        metadata=ChunkMetadata(
            doc_id="DOC-LOG-001",
            doc_type="maintenance_log",
            source_file="maintenance_log_2024.xlsx",
            page_or_row="Row 142",
            equipment_tags=["PUMP-203"],
            section_title="Maintenance Record",
            doc_date=date(2024, 10, 15),
            ingested_at="2024-01-10T10:15:00Z"
        )
    ),

    # --- HX-301 DECAY (Procedure evolution) ---
    Chunk(
        chunk_id="chunk_005",
        content="""Heat Exchanger HX-301 Cleaning Procedure:
        Tube bundle cleaning shall be performed quarterly (every 3 months).
        Use approved chemical cleaning solution per specification CHEM-201.
        Document fouling factor measurements before and after cleaning.""",
        metadata=ChunkMetadata(
            doc_id="DOC-SOP-002",
            doc_type="sop",
            source_file="heat_exchanger_sop_v2.pdf",
            page_or_row="Page 8",
            equipment_tags=["HX-301"],
            section_title="Cleaning Requirements",
            doc_date=date(2021, 3, 1),
            ingested_at="2024-01-10T10:20:00Z"
        )
    ),
    Chunk(
        chunk_id="chunk_006",
        content="""Maintenance Log Entry - HX-301
        Date: 2025-07-01
        Note: Per operations request, tube cleaning frequency increased to MONTHLY
        due to higher than expected fouling rates observed since feedstock change.
        Engineering change request ECR-2025-042 pending formal SOP update.""",
        metadata=ChunkMetadata(
            doc_id="DOC-LOG-002",
            doc_type="maintenance_log",
            source_file="maintenance_log_2025.xlsx",
            page_or_row="Row 89",
            equipment_tags=["HX-301"],
            section_title="Maintenance Note",
            doc_date=date(2025, 7, 1),
            ingested_at="2025-07-02T08:00:00Z"
        )
    ),

    # --- Additional context chunks (no conflicts) ---
    Chunk(
        chunk_id="chunk_007",
        content="""Compressor C-401 Operating Limits:
        - Maximum discharge pressure: 250 psi
        - Minimum suction pressure: 5 psi
        - Operating temperature range: -20F to 150F
        - Lubrication: ISO VG 68 compressor oil""",
        metadata=ChunkMetadata(
            doc_id="DOC-MAN-003",
            doc_type="manual",
            source_file="compressor_manual.pdf",
            page_or_row="Page 23",
            equipment_tags=["C-401"],
            section_title="Operating Parameters",
            doc_date=date(2023, 5, 20),
            ingested_at="2024-01-10T10:25:00Z"
        )
    ),
    Chunk(
        chunk_id="chunk_008",
        content="""INCIDENT REPORT - Near Miss
        Equipment: PUMP-203
        Date: 2024-03-15
        Description: Bearing temperature alarm activated during routine operation.
        Investigation found low lubricant level. Topped up immediately.
        Root Cause: Oil drain plug not fully tightened after last maintenance.
        Corrective Action: Added torque verification step to maintenance checklist.""",
        metadata=ChunkMetadata(
            doc_id="DOC-INC-001",
            doc_type="incident_report",
            source_file="incident_reports_2024.pdf",
            page_or_row="Page 12",
            equipment_tags=["PUMP-203"],
            section_title="Near Miss Report",
            doc_date=date(2024, 3, 15),
            ingested_at="2024-03-16T09:00:00Z"
        )
    ),
    Chunk(
        chunk_id="chunk_009",
        content="""INCIDENT REPORT - Equipment Failure
        Equipment: PSV-101
        Date: 2023-08-22
        Description: Relief valve failed to reseat after activation during upset condition.
        Product loss estimated at 500 gallons before isolation completed.
        Root Cause: Seat damage from previous testing cycle.
        Corrective Action: Implemented soft-seat verification after each test.""",
        metadata=ChunkMetadata(
            doc_id="DOC-INC-002",
            doc_type="incident_report",
            source_file="incident_reports_2023.pdf",
            page_or_row="Page 45",
            equipment_tags=["PSV-101"],
            section_title="Equipment Failure Report",
            doc_date=date(2023, 8, 22),
            ingested_at="2024-01-10T10:30:00Z"
        )
    ),
    Chunk(
        chunk_id="chunk_010",
        content="""Inspection Report - HX-301
        Date: 2025-06-15
        Inspector: M. Rodriguez
        Findings: Tube fouling more severe than expected.
        Thermal efficiency degraded 15% since last quarterly clean.
        Recommendation: Consider increasing cleaning frequency or
        investigating alternate tube material for new feedstock.""",
        metadata=ChunkMetadata(
            doc_id="DOC-INS-001",
            doc_type="inspection_report",
            source_file="inspection_2025_q2.pdf",
            page_or_row="Page 7",
            equipment_tags=["HX-301"],
            section_title="Heat Exchanger Inspection",
            doc_date=date(2025, 6, 15),
            ingested_at="2025-06-16T10:00:00Z"
        )
    ),
]

# ---------------------------------------------------------------------------
# MOCK CLAIMS (simulating Person 2's knowledge_graph.query outputs)
# ---------------------------------------------------------------------------

MOCK_CLAIMS: List[Claim] = [
    # PSV-101 conflicting claims
    Claim(
        id="claim_001",
        doc_id="DOC-MAN-001",
        chunk_id="chunk_001",
        equipment_tag="PSV-101",
        parameter_name="relief_pressure_psi",
        value="150",
        unit="psi",
        effective_date=date(2023, 1, 15),
        source_text="Set pressure: 150 psi",
        confidence=0.95
    ),
    Claim(
        id="claim_002",
        doc_id="DOC-SOP-001",
        chunk_id="chunk_002",
        equipment_tag="PSV-101",
        parameter_name="relief_pressure_psi",
        value="145",
        unit="psi",
        effective_date=date(2024, 6, 20),
        source_text="Verify relief pressure is set to 145 psi",
        confidence=0.92
    ),

    # PUMP-203 claims (including decay scenario)
    Claim(
        id="claim_003",
        doc_id="DOC-MAN-002",
        chunk_id="chunk_003",
        equipment_tag="PUMP-203",
        parameter_name="inspection_interval_months",
        value="6",
        unit="months",
        effective_date=date(2022, 8, 10),
        source_text="Bearing inspection: Every 6 months",
        confidence=0.98
    ),
    Claim(
        id="claim_004",
        doc_id="DOC-LOG-001",
        chunk_id="chunk_004",
        equipment_tag="PUMP-203",
        parameter_name="last_inspection_date",
        value="2024-10-15",
        unit=None,
        effective_date=date(2024, 10, 15),
        source_text="Date: 2024-10-15 - Routine bearing inspection completed",
        confidence=0.99
    ),

    # HX-301 claims (procedure evolution)
    Claim(
        id="claim_005",
        doc_id="DOC-SOP-002",
        chunk_id="chunk_005",
        equipment_tag="HX-301",
        parameter_name="cleaning_frequency",
        value="quarterly",
        unit=None,
        effective_date=date(2021, 3, 1),
        source_text="Tube bundle cleaning shall be performed quarterly",
        confidence=0.96
    ),
    Claim(
        id="claim_006",
        doc_id="DOC-LOG-002",
        chunk_id="chunk_006",
        equipment_tag="HX-301",
        parameter_name="cleaning_frequency",
        value="monthly",
        unit=None,
        effective_date=date(2025, 7, 1),
        source_text="tube cleaning frequency increased to MONTHLY",
        confidence=0.94
    ),

    # C-401 claims (no conflicts)
    Claim(
        id="claim_007",
        doc_id="DOC-MAN-003",
        chunk_id="chunk_007",
        equipment_tag="C-401",
        parameter_name="max_discharge_pressure_psi",
        value="250",
        unit="psi",
        effective_date=date(2023, 5, 20),
        source_text="Maximum discharge pressure: 250 psi",
        confidence=0.97
    ),
]

# ---------------------------------------------------------------------------
# MOCK INCIDENTS (simulating Person 2's incident data)
# ---------------------------------------------------------------------------

MOCK_INCIDENTS: List[Incident] = [
    Incident(
        id="inc_001",
        doc_id="DOC-INC-001",
        chunk_id="chunk_008",
        equipment_tag="PUMP-203",
        incident_type="near_miss",
        description="Bearing temperature alarm activated due to low lubricant level. Root cause: oil drain plug not fully tightened after maintenance. Added torque verification step.",
        date=date(2024, 3, 15),
        severity="medium"
    ),
    Incident(
        id="inc_002",
        doc_id="DOC-INC-002",
        chunk_id="chunk_009",
        equipment_tag="PSV-101",
        incident_type="equipment_failure",
        description="Relief valve failed to reseat after activation, causing 500 gallon product loss. Root cause: seat damage from testing. Implemented soft-seat verification.",
        date=date(2023, 8, 22),
        severity="high"
    ),
]


# ---------------------------------------------------------------------------
# FIXTURE FUNCTIONS (matching Person 2's knowledge_graph.query interface)
# ---------------------------------------------------------------------------

def get_all_chunks() -> List[Chunk]:
    """Return all mock chunks for testing."""
    return MOCK_CHUNKS


def search_chunks_by_similarity(query: str, top_k: int = 6) -> List[Chunk]:
    """
    Simulate vector similarity search.
    In fixtures, we do simple keyword matching and assign fake similarity scores.
    """
    query_lower = query.lower()
    scored_chunks = []

    for chunk in MOCK_CHUNKS:
        # Simple keyword scoring
        score = 0.0
        content_lower = chunk.content.lower()

        # Check for equipment tags in query
        for tag in chunk.metadata.equipment_tags:
            if tag.lower() in query_lower:
                score += 0.4

        # Check for keyword overlap
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        overlap = len(query_words & content_words)
        score += min(0.5, overlap * 0.1)

        # Check doc type relevance
        if "procedure" in query_lower and chunk.metadata.doc_type == "sop":
            score += 0.1
        if "incident" in query_lower and chunk.metadata.doc_type == "incident_report":
            score += 0.2
        if "maintenance" in query_lower and chunk.metadata.doc_type == "maintenance_log":
            score += 0.15

        if score > 0:
            chunk.similarity_score = min(0.99, score)
            scored_chunks.append(chunk)

    # Sort by score descending
    scored_chunks.sort(key=lambda c: c.similarity_score, reverse=True)
    return scored_chunks[:top_k]


def get_claims_for_entity(equipment_tag: str) -> List[Claim]:
    """Get all claims for a specific equipment tag."""
    return [c for c in MOCK_CLAIMS if c.equipment_tag == equipment_tag]


def get_claims_for_parameter(parameter_name: str) -> List[Claim]:
    """Get all claims for a specific parameter across all equipment."""
    return [c for c in MOCK_CLAIMS if c.parameter_name == parameter_name]


def find_conflicting_claims() -> List[tuple]:
    """
    Find all pairs of claims that may conflict.
    Returns list of (claim_a, claim_b) tuples where both claims
    share equipment_tag and parameter_name but differ in value.
    """
    conflicts = []
    claims_by_key: Dict[str, List[Claim]] = {}

    for claim in MOCK_CLAIMS:
        key = f"{claim.equipment_tag}:{claim.parameter_name}"
        if key not in claims_by_key:
            claims_by_key[key] = []
        claims_by_key[key].append(claim)

    for key, claims in claims_by_key.items():
        if len(claims) > 1:
            # Check if values differ
            for i in range(len(claims)):
                for j in range(i + 1, len(claims)):
                    if claims[i].value != claims[j].value:
                        conflicts.append((claims[i], claims[j]))

    return conflicts


def get_incidents_similar_to(query: str, equipment_tags: Optional[List[str]] = None) -> List[Incident]:
    """
    Find incidents relevant to the query or equipment tags.
    """
    results = []
    query_lower = query.lower()

    for incident in MOCK_INCIDENTS:
        relevance = 0

        # Check equipment tag match
        if equipment_tags and incident.equipment_tag in equipment_tags:
            relevance += 2

        # Check keyword match in description
        if any(word in incident.description.lower() for word in query_lower.split()):
            relevance += 1

        # Check incident type match
        if incident.incident_type in query_lower:
            relevance += 1

        if relevance > 0:
            results.append(incident)

    return results


def get_stale_claims(reference_date: Optional[date] = None) -> List[Claim]:
    """
    Find claims that may be stale (e.g., inspection intervals that have passed).
    For fixtures, we specifically check PUMP-203 inspection interval.
    """
    if reference_date is None:
        reference_date = date.today()

    stale = []

    # Find inspection interval claims and check against last inspection dates
    inspection_intervals = [c for c in MOCK_CLAIMS if "inspection_interval" in c.parameter_name]
    last_inspections = [c for c in MOCK_CLAIMS if "last_inspection" in c.parameter_name]

    for interval_claim in inspection_intervals:
        # Find matching last inspection
        matching_inspection = next(
            (c for c in last_inspections if c.equipment_tag == interval_claim.equipment_tag),
            None
        )

        if matching_inspection:
            try:
                interval_months = int(interval_claim.value)
                last_date = date.fromisoformat(matching_inspection.value)
                next_due = date(
                    last_date.year + (last_date.month + interval_months - 1) // 12,
                    (last_date.month + interval_months - 1) % 12 + 1,
                    min(last_date.day, 28)  # Simplify for month-end handling
                )

                if reference_date > next_due:
                    stale.append(interval_claim)
            except (ValueError, TypeError):
                pass

    return stale


def get_chunk_by_id(chunk_id: str) -> Optional[Chunk]:
    """Get a specific chunk by ID."""
    for chunk in MOCK_CHUNKS:
        if chunk.chunk_id == chunk_id:
            return chunk
    return None
