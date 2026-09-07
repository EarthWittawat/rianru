from neo4j import GraphDatabase

from app.config import settings

_driver = GraphDatabase.driver(
    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)


def get_driver():
    return _driver


def check_connectivity() -> bool:
    with _driver.session() as session:
        result = session.run("RETURN 1 AS ok")
        return result.single()["ok"] == 1
