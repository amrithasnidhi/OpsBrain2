CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    equipment_tag TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    value TEXT NOT NULL,
    unit TEXT,
    effective_date TEXT,
    source_text TEXT,
    confidence REAL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    equipment_tag TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    description TEXT NOT NULL,
    date TEXT,
    severity TEXT
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    doc_id TEXT,
    chunk_id TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    FOREIGN KEY(source_entity_id) REFERENCES entities(id),
    FOREIGN KEY(target_entity_id) REFERENCES entities(id)
);
