export interface Citation {
  doc_id: string;
  source_file: string;
  page_or_row?: string;
  excerpt: string;
}

export interface Incident {
  id: string;
  doc_id: string;
  chunk_id: string;
  equipment_tag?: string;
  incident_type: string;
  description: string;
  date?: string;
  severity: "low" | "medium" | "high" | "critical";
}

export interface Conflict {
  entity: string;
  parameter: string;
  source_a: Citation;
  value_a: string;
  source_b: Citation;
  value_b: string;
  explanation: string;
  severity: "low" | "medium" | "high";
  risk_type: "direct_contradiction" | "decay";
}

export interface QueryResult {
  answer: string;
  confidence: number;
  citations: Citation[];
  conflicts: Conflict[];
  lessons_learned: Incident[];
}

// Type exports for runtime
export type { Citation, Incident, Conflict, QueryResult };
