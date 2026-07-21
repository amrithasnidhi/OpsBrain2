import os
import networkx as nx
from knowledge_graph.db import get_connection

def build_graph() -> nx.DiGraph:
    """Builds an in-memory graph from the SQLite tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    G = nx.DiGraph()
    
    cursor.execute("SELECT id, entity_type, canonical_name FROM entities")
    for row in cursor.fetchall():
        G.add_node(row[0], type=row[1], name=row[2])
        
    cursor.execute("SELECT source_entity_id, target_entity_id, relation_type FROM relationships")
    for row in cursor.fetchall():
        G.add_edge(row[0], row[1], type=row[2])
        
    conn.close()
    return G

def get_related_entities(tag: str, max_depth: int = 2) -> list:
    """Returns related entities up to a certain depth."""
    G = build_graph()
    from knowledge_graph.resolve import resolve_entity
    canon = resolve_entity(tag)
    
    if canon not in G:
        return []
        
    related = set()
    # Simple BFS for max_depth
    frontier = [(canon, 0)]
    visited = set()
    
    while frontier:
        node, depth = frontier.pop(0)
        if node in visited:
            continue
        visited.add(node)
        
        if depth > 0:
            related.add(node)
            
        if depth < max_depth:
            for neighbor in G.neighbors(node):
                frontier.append((neighbor, depth + 1))
            for predecessor in G.predecessors(node):
                frontier.append((predecessor, depth + 1))
                
    return list(related)

def export_neo4j_script():
    """Generates export_neo4j.cypher script from the DB."""
    conn = get_connection()
    cursor = conn.cursor()
    
    output_path = os.path.join(os.path.dirname(__file__), "..", "export_neo4j.cypher")
    
    with open(output_path, 'w') as f:
        f.write("// Neo4j Cypher Export\n")
        f.write("MATCH (n) DETACH DELETE n;\n\n")
        
        cursor.execute("SELECT id, entity_type, canonical_name FROM entities")
        for row in cursor.fetchall():
            eid, etype, name = row
            etype_label = etype.capitalize() if etype else "Entity"
            f.write(f"CREATE (e_{eid.replace('-', '_')}:{etype_label} {{id: '{eid}', name: '{name}'}});\n")
            
        cursor.execute("SELECT source_entity_id, target_entity_id, relation_type FROM relationships")
        for row in cursor.fetchall():
            src, tgt, rel = row
            src_clean = src.replace('-', '_')
            tgt_clean = tgt.replace('-', '_')
            f.write(f"MATCH (a {{id: '{src}'}}), (b {{id: '{tgt}'}}) CREATE (a)-[:{rel.upper()}]->(b);\n")
            
    conn.close()

if __name__ == "__main__":
    export_neo4j_script()
    print("Exported Cypher script.")
