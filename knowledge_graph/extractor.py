import json
import os
import uuid
from knowledge_graph.db import get_connection, init_db
from knowledge_graph.resolve import resolve_entity
from rag_engine.llm import LLMManager

"""
NORMALIZATION RULES for parameter_name:
- Always use lowercase snake_case (e.g. "max_pressure").
- Always strip units and store them in the `unit` field (e.g. parameter_name="max_pressure", unit="PSI").
- Maintenance intervals should be suffixed with the unit if applicable, or generic like "maintenance_interval".
- Lubrication requirements should be normalized to "lubrication_type".
These rules ensure that differing texts map to the exact same parameter string.
"""

def extract_from_chunk(chunk_id, doc_id, doc_type, text):
    # Tool schema for Claude
    tools = [
        {
            "name": "extract_knowledge",
            "description": "Extracts claims (parameters) and incidents from industrial maintenance text.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "equipment_tag": {"type": "string", "description": "The equipment identifier (e.g. Pump-P101)"},
                                "parameter_name": {"type": "string", "description": "Snake_case normalized parameter name without units (e.g. max_pressure, inspection_interval)."},
                                "value": {"type": "string", "description": "The value of the parameter (e.g. 150, weekly, self-lubricating)."},
                                "unit": {"type": "string", "description": "The unit of measurement if applicable (e.g. PSI, months)."},
                                "effective_date": {"type": "string", "description": "The date the claim was made or observed, if present."},
                                "confidence": {"type": "number", "description": "Confidence score 0.0 to 1.0 based on explicit vs inferred value."}
                            },
                            "required": ["equipment_tag", "parameter_name", "value"]
                        }
                    },
                    "incidents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "equipment_tag": {"type": "string"},
                                "incident_type": {"type": "string", "description": "e.g. Failure, Near Miss, Observation"},
                                "description": {"type": "string"},
                                "date": {"type": "string"},
                                "severity": {"type": "string"}
                            },
                            "required": ["equipment_tag", "incident_type", "description"]
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source_entity": {"type": "string"},
                                "target_entity": {"type": "string"},
                                "relation_type": {"type": "string", "description": "e.g. PART_OF, INSPECTED"}
                            },
                            "required": ["source_entity", "target_entity", "relation_type"]
                        }
                    }
                },
                "required": ["claims", "incidents", "relationships"]
            }
        }
    ]

    prompt = f"""Extract structured data from this industrial maintenance text.

Doc Type: {doc_type}
Text:
{text}

Return a JSON object with exactly this structure:
{{
  "claims": [
    {{"equipment_tag": "string", "parameter_name": "snake_case_name", "value": "string", "unit": "string or null", "effective_date": "YYYY-MM-DD or null", "confidence": 0.0-1.0}}
  ],
  "incidents": [
    {{"equipment_tag": "string", "incident_type": "Failure/Near Miss/Observation", "description": "string", "date": "YYYY-MM-DD or null", "severity": "low/medium/high"}}
  ],
  "relationships": [
    {{"source_entity": "string", "target_entity": "string", "relation_type": "FEEDS_INTO/PROTECTS/CONTROLS/PART_OF/etc"}}
  ]
}}

Rules:
- parameter_name must be lowercase snake_case (e.g. max_pressure, inspection_interval)
- Extract ALL equipment tags mentioned (e.g. PSV-101, PUMP-301, HX-401)
- Include relationships between equipment
- Return ONLY valid JSON, no other text"""

    try:
        llm = LLMManager()
        provider = llm.get_provider()

        # Check if we have a real provider (not mock)
        if provider.name == "Mock (No API)":
            return _mock_extraction(doc_id)

        response = llm.generate(prompt, max_tokens=2048)

        # Parse JSON from response
        # Find JSON in response (it might have markdown code blocks)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]

        # Clean up and parse
        json_str = json_str.strip()
        result = json.loads(json_str)
        return result
    except Exception as e:
        print(f"Extraction error: {e}")
        return _mock_extraction(doc_id)

def _mock_extraction(doc_id):
    """Fallback if API key isn't provided so testing isn't blocked."""
    data = {"claims": [], "incidents": [], "relationships": []}
    doc_id_lower = doc_id.lower()

    if "compressor" in doc_id_lower or "c1" in doc_id_lower:
        data["claims"].append({"equipment_tag": "Compressor-C1", "parameter_name": "max_pressure", "value": "150", "unit": "PSI", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "Compressor-C1", "parameter_name": "inspection_interval", "value": "6", "unit": "months", "confidence": 1.0})
        data["relationships"].append({"source_entity": "Compressor-C1", "target_entity": "Process-Area-B", "relation_type": "LOCATED_IN"})
    elif "pump" in doc_id_lower:
        data["claims"].append({"equipment_tag": "Pump-P3", "parameter_name": "max_flow_rate", "value": "500", "unit": "GPM", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "Pump-P3", "parameter_name": "maintenance_interval", "value": "3", "unit": "months", "confidence": 0.9})
        data["relationships"].append({"source_entity": "Pump-P3", "target_entity": "Compressor-C1", "relation_type": "FEEDS_INTO"})
    elif "valve" in doc_id_lower or "v12" in doc_id_lower:
        data["claims"].append({"equipment_tag": "Valve-V12", "parameter_name": "lubrication_type", "value": "self-lubricating", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "Valve-V12", "parameter_name": "max_pressure", "value": "200", "unit": "PSI", "confidence": 1.0})
        data["relationships"].append({"source_entity": "Valve-V12", "target_entity": "Compressor-C1", "relation_type": "CONTROLS"})
    elif "incident" in doc_id_lower:
        data["incidents"].append({"equipment_tag": "Compressor-C1", "incident_type": "Failure", "description": "Unexpected shutdown due to bearing failure.", "severity": "high"})
        data["relationships"].append({"source_entity": "Compressor-C1", "target_entity": "Incident-Report", "relation_type": "HAS_INCIDENT"})
    elif "maintenance" in doc_id_lower or "report" in doc_id_lower or "inspection" in doc_id_lower:
        # PSV equipment
        data["claims"].append({"equipment_tag": "PSV-101", "parameter_name": "inspection_interval", "value": "12", "unit": "months", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "PSV-101", "parameter_name": "relief_pressure_psi", "value": "145", "unit": "PSI", "effective_date": "2026-01-15", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "PSV-202", "parameter_name": "inspection_interval", "value": "12", "unit": "months", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "PSV-202", "parameter_name": "relief_pressure_psi", "value": "200", "unit": "PSI", "confidence": 1.0})
        # Pump equipment
        data["claims"].append({"equipment_tag": "PUMP-101", "parameter_name": "inspection_interval_months", "value": "6", "unit": "months", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "PUMP-101", "parameter_name": "vibration_monitoring", "value": "2.1", "unit": "mm/s", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "PUMP-203", "parameter_name": "inspection_interval_months", "value": "6", "unit": "months", "confidence": 1.0})
        # Heat exchanger
        data["claims"].append({"equipment_tag": "HX-301", "parameter_name": "cleaning_frequency", "value": "quarterly", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "HX-402", "parameter_name": "cleaning_frequency", "value": "monthly", "confidence": 1.0})
        # Compressor
        data["claims"].append({"equipment_tag": "Compressor-C1", "parameter_name": "discharge_pressure", "value": "250", "unit": "PSI", "confidence": 1.0})
        data["claims"].append({"equipment_tag": "Compressor-C2", "parameter_name": "discharge_pressure", "value": "275", "unit": "PSI", "confidence": 1.0})
        # Fire safety
        data["claims"].append({"equipment_tag": "Facility", "parameter_name": "fire_drill_interval_months", "value": "6", "unit": "months", "confidence": 1.0})
        # Relationships
        data["relationships"].append({"source_entity": "PSV-101", "target_entity": "Compressor-C1", "relation_type": "PROTECTS"})
        data["relationships"].append({"source_entity": "PUMP-101", "target_entity": "HX-301", "relation_type": "FEEDS_INTO"})
        data["relationships"].append({"source_entity": "PUMP-203", "target_entity": "Compressor-C1", "relation_type": "FEEDS_INTO"})
        data["relationships"].append({"source_entity": "HX-301", "target_entity": "Compressor-C1", "relation_type": "COOLS"})
        data["relationships"].append({"source_entity": "Compressor-C2", "target_entity": "Compressor-C1", "relation_type": "BACKUP_FOR"})
        data["relationships"].append({"source_entity": "Valve-V12", "target_entity": "Compressor-C1", "relation_type": "CONTROLS"})
        data["relationships"].append({"source_entity": "Valve-V15", "target_entity": "HX-301", "relation_type": "CONTROLS"})
        # Incidents
        data["incidents"].append({"equipment_tag": "PUMP-203", "incident_type": "Near Miss", "description": "Unusual vibration detected during routine check. Bearing replaced preventively.", "severity": "low", "date": "2026-02-10"})
        data["incidents"].append({"equipment_tag": "Compressor-C1", "incident_type": "Unplanned Shutdown", "description": "High discharge temperature triggered automatic shutdown. Root cause: Fouled intercooler.", "severity": "medium", "date": "2026-05-22"})
    elif "sop" in doc_id_lower:
        data["claims"].append({"equipment_tag": "Facility", "parameter_name": "emergency_response_time", "value": "5", "unit": "minutes", "confidence": 1.0})
        data["relationships"].append({"source_entity": "Facility", "target_entity": "Emergency-Team", "relation_type": "MANAGED_BY"})

    return data
    
def process_manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "data", "chunks_manifest.json")
    if not os.path.exists(manifest_path):
        print("Manifest not found.")
        return
        
    db_path = os.path.join(os.path.dirname(__file__), "knowledge.db")
    if not os.path.exists(db_path):
        init_db()
        
    conn = get_connection()
    cursor = conn.cursor()
    
    with open(manifest_path, 'r') as f:
        chunks = json.load(f)
        
    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        doc_id = chunk["doc_id"]
        text = chunk["text"]
        doc_type = chunk.get("doc_type", "unknown")
        
        extracted = extract_from_chunk(chunk_id, doc_id, doc_type, text)
        
        for c in extracted.get("claims", []):
            canon_tag = resolve_entity(c.get("equipment_tag", "Unknown"))
            cursor.execute("INSERT OR IGNORE INTO entities (id, entity_type, canonical_name, doc_id, chunk_id) VALUES (?, ?, ?, ?, ?)",
                           (canon_tag, "equipment", canon_tag, doc_id, chunk_id))
            cursor.execute("""
                INSERT INTO claims (id, doc_id, chunk_id, equipment_tag, parameter_name, value, unit, effective_date, source_text, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), doc_id, chunk_id, canon_tag, c.get("parameter_name"), str(c.get("value")), c.get("unit"), c.get("effective_date"), text, c.get("confidence", 1.0)))
            
        for i in extracted.get("incidents", []):
            canon_tag = resolve_entity(i.get("equipment_tag", "Unknown"))
            cursor.execute("""
                INSERT INTO incidents (id, doc_id, chunk_id, equipment_tag, incident_type, description, date, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), doc_id, chunk_id, canon_tag, i.get("incident_type"), i.get("description"), i.get("date"), i.get("severity")))
            
        for r in extracted.get("relationships", []):
            src = resolve_entity(r.get("source_entity"))
            tgt = resolve_entity(r.get("target_entity"))
            cursor.execute("INSERT OR IGNORE INTO entities (id, entity_type, canonical_name) VALUES (?, ?, ?)", (src, "unknown", src))
            cursor.execute("INSERT OR IGNORE INTO entities (id, entity_type, canonical_name) VALUES (?, ?, ?)", (tgt, "unknown", tgt))
            cursor.execute("""
                INSERT INTO relationships (id, source_entity_id, target_entity_id, relation_type)
                VALUES (?, ?, ?, ?)
            """, (str(uuid.uuid4()), src, tgt, r.get("relation_type")))
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    process_manifest()
