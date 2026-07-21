// Neo4j Cypher Export
MATCH (n) DETACH DELETE n;

CREATE (e_Pump_P101:Equipment {id: 'Pump-P101', name: 'Pump-P101'});
CREATE (e_Valve_12:Equipment {id: 'Valve-12', name: 'Valve-12'});
CREATE (e_Compressor_C1:Unknown {id: 'Compressor-C1', name: 'Compressor-C1'});
CREATE (e_Filter_F300:Equipment {id: 'Filter-F300', name: 'Filter-F300'});
MATCH (a {id: 'Valve-12'}), (b {id: 'Compressor-C1'}) CREATE (a)-[:PART_OF]->(b);
