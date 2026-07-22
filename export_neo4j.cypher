// Neo4j Cypher Export
MATCH (n) DETACH DELETE n;

CREATE (e_Valve V_12:Equipment {id: 'Valve V-12', name: 'Valve V-12'});
