from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Database!8")

_driver = GraphDatabase.driver(URI, auth=AUTH)

def run_query(cypher, params=None):
    """Run a Cypher query and return list of records (as dicts)."""
    params = params or {}
    with _driver.session() as session:
        result = session.run(cypher, params)
        return [dict(rec) for rec in result]

def close():
    _driver.close()
