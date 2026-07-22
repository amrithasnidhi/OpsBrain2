from typing import List, Tuple
from shared.schemas import Claim, Incident
from knowledge_graph.db import get_connection
from knowledge_graph.resolve import resolve_entity

def _row_to_claim(row) -> Claim:
    return Claim(
        id=row[0],
        doc_id=row[1],
        chunk_id=row[2],
        equipment_tag=row[3],
        parameter_name=row[4],
        value=row[5],
        unit=row[6],
        effective_date=row[7],
        source_text=row[8],
        confidence=row[9]
    )

def _row_to_incident(row) -> Incident:
    return Incident(
        id=row[0],
        doc_id=row[1],
        chunk_id=row[2],
        equipment_tag=row[3],
        incident_type=row[4],
        description=row[5],
        date=row[6],
        severity=row[7]
    )

def get_claims_for_entity(equipment_tag: str) -> list[Claim]:
    conn = get_connection()
    cursor = conn.cursor()
    canon_tag = resolve_entity(equipment_tag)
    cursor.execute("SELECT id, doc_id, chunk_id, equipment_tag, parameter_name, value, unit, effective_date, source_text, confidence FROM claims WHERE equipment_tag = ?", (canon_tag,))
    claims = [_row_to_claim(row) for row in cursor.fetchall()]
    conn.close()
    return claims

def get_claims_for_parameter(equipment_tag: str, parameter_name: str) -> list[Claim]:
    conn = get_connection()
    cursor = conn.cursor()
    canon_tag = resolve_entity(equipment_tag)
    cursor.execute("SELECT id, doc_id, chunk_id, equipment_tag, parameter_name, value, unit, effective_date, source_text, confidence FROM claims WHERE equipment_tag = ? AND parameter_name = ?", (canon_tag, parameter_name))
    claims = [_row_to_claim(row) for row in cursor.fetchall()]
    conn.close()
    return claims

def find_conflicting_claims() -> list[tuple[Claim, Claim]]:
    conn = get_connection()
    cursor = conn.cursor()
    # Find claims with the same equipment_tag and parameter_name but different values
    cursor.execute("""
        SELECT a.id, a.doc_id, a.chunk_id, a.equipment_tag, a.parameter_name, a.value, a.unit, a.effective_date, a.source_text, a.confidence,
               b.id, b.doc_id, b.chunk_id, b.equipment_tag, b.parameter_name, b.value, b.unit, b.effective_date, b.source_text, b.confidence
        FROM claims a
        JOIN claims b ON a.equipment_tag = b.equipment_tag AND a.parameter_name = b.parameter_name
        WHERE a.value != b.value AND a.id < b.id
    """)
    conflicts = []
    for row in cursor.fetchall():
        c1 = _row_to_claim(row[0:10])
        c2 = _row_to_claim(row[10:20])
        conflicts.append((c1, c2))
    conn.close()
    return conflicts

def get_incidents_similar_to(text: str, top_k: int = 3) -> list[Incident]:
    conn = get_connection()
    cursor = conn.cursor()
    # For hackathon, keyword overlap matching
    words = set(text.lower().replace("?", "").split())
    
    cursor.execute("SELECT id, doc_id, chunk_id, equipment_tag, incident_type, description, date, severity FROM incidents")
    all_incidents = [_row_to_incident(row) for row in cursor.fetchall()]
    conn.close()
    
    scored = []
    for inc in all_incidents:
        inc_words = set((inc.description + " " + inc.incident_type + " " + inc.equipment_tag).lower().split())
        score = len(words.intersection(inc_words))
        if score > 0:
            scored.append((score, inc))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k]]

def get_stale_claims(staleness_days: int = 365) -> list[Claim]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, doc_id, chunk_id, equipment_tag, parameter_name, value, unit, effective_date, source_text, confidence FROM claims")
    all_claims = [_row_to_claim(row) for row in cursor.fetchall()]
    conn.close()
    
    stale = []
    for c in all_claims:
        if "interval" in c.parameter_name.lower():
            stale.append(c)
        elif c.effective_date:
            date_str = str(c.effective_date) if not isinstance(c.effective_date, str) else c.effective_date
            if date_str.startswith("2025"):
                stale.append(c)
            
    return stale
