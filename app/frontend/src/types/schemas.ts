// Frontend TypeScript types matching shared/schemas.py
// Keep in sync with Python schemas

export interface Citation {
  doc_id: string;
  source_file: string;
  page_or_row?: string;
  excerpt: string;
}

export interface Claim {
  id: string;
  doc_id: string;
  chunk_id: string;
  equipment_tag: string;
  parameter_name: string;
  value: string;
  unit?: string;
  effective_date?: string;
  source_text: string;
  confidence: number;
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
  // Extended fields (Person A fills these)
  risk_score?: number;
  business_impact?: string;
  resolution?: "temporal_supersession" | "unresolved";
  authoritative_source?: Citation;
  superseded_source?: Citation;
}

// === NEW MODELS FOR ROUND 2 ===

export interface ConfidenceBreakdown {
  score: number;
  reasons: string[];
  warnings: string[];
}

export interface RootCauseChain {
  incident?: Incident;
  related_claims: Claim[];
  related_conflicts: Conflict[];
  similar_incidents: Incident[];
  likely_root_cause: string;
  recommended_checks: string[];
}

export interface ComplianceGap {
  standard: string;
  requirement: string;
  equipment_tag: string;
  status: "compliant" | "gap" | "unknown";
  details: string;
}

export interface StalenessRow {
  equipment_tag: string;
  required_interval: string;
  last_inspection_date?: string;
  days_overdue: number;
  status: "ok" | "warning" | "overdue";
}

export interface KnowledgeCaptureRequest {
  expert_name: string;
  equipment_tag: string;
  knowledge_type: "undocumented_procedure" | "tribal_knowledge" | "failure_pattern";
  free_text: string;
}

export interface QueryResult {
  answer: string;
  confidence: number;
  citations: Citation[];
  conflicts: Conflict[];
  lessons_learned: Incident[];
  // Extended fields
  confidence_breakdown?: ConfidenceBreakdown;  // Person C fills this
  root_cause_chain?: RootCauseChain;           // Person B fills this
  retrieval_mode?: "dense" | "hybrid";         // Person B fills this
}
