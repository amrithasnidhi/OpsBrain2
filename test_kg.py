import os
import sys

# Ensure OpsBrain2 is in sys.path
sys.path.append(os.path.dirname(__file__))

from knowledge_graph.extractor import process_manifest
from knowledge_graph.query import find_conflicting_claims, get_claims_for_entity, get_stale_claims, get_incidents_similar_to
from knowledge_graph.graph import export_neo4j_script

def run_tests():
    db_path = os.path.join(os.path.dirname(__file__), "knowledge_graph", "knowledge.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    print("--- Running Extractor ---")
    process_manifest()
    print("Extraction complete. Database populated.")
    
    print("\n--- Testing Entity Resolution ---")
    claims_v12 = get_claims_for_entity("Valve-12")
    claims_v12_variant = get_claims_for_entity("Valve V-12")
    
    print(f"Claims for 'Valve-12': {len(claims_v12)}")
    print(f"Claims for 'Valve V-12': {len(claims_v12_variant)}")
    
    print("\n--- Testing find_conflicting_claims ---")
    conflicts = find_conflicting_claims()
    print(f"Total Direct Conflicts Found: {len(conflicts)}")
    for c1, c2 in conflicts:
        print(f"  - {c1.equipment_tag}: {c1.parameter_name} -> '{c1.value}' vs '{c2.value}'")
        
    print("\n--- Testing get_stale_claims ---")
    stale = get_stale_claims()
    print(f"Total Stale Claims Found: {len(stale)}")
    for s in stale:
        print(f"  - {s.equipment_tag}: {s.parameter_name} -> {s.value}")
        
    print("\n--- Testing export_neo4j_script ---")
    export_neo4j_script()
    
if __name__ == "__main__":
    run_tests()
