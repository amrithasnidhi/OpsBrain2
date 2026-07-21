# knowledge_graph/__init__.py
"""
Knowledge Graph module (Person 2's domain).

This module provides:
- Entity/claim extraction from documents
- Graph-based querying
- Conflict detection primitives

The RAG engine imports from knowledge_graph.query for:
- get_claims_for_entity(equipment_tag) -> List[Claim]
- get_claims_for_parameter(parameter_name) -> List[Claim]
- find_conflicting_claims() -> List[Tuple[Claim, Claim]]
- get_incidents_similar_to(query, equipment_tags) -> List[Incident]
- get_stale_claims(reference_date) -> List[Claim]
"""
