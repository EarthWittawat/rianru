"""A concept's own page: what it is, an example, and what it stands on."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import concepts as concept_service
from app.services.neo4j_client import get_driver

client = TestClient(app)

NAME = "ConceptTest Widget"
PREREQ = "ConceptTest Base"


@pytest.fixture(autouse=True)
def seeded_concept():
    _wipe()
    with get_driver().session() as session:
        session.run(
            """
            MERGE (d:Document {id: 'ConceptTest::doc'})
              SET d.title = 'Lecture 9', d.course = 'CONCEPTTEST',
                  d.topic = 'Widgets', d.position = 1, d.activity_type = 'material'
            MERGE (c:Chunk {id: 'ConceptTest::doc::0'})
              SET c.text = 'A widget batches records before they are counted.',
                  c.page = 4, c.index = 0
            MERGE (d)-[:HAS_CHUNK]->(c)
            MERGE (w:Entity {name: $name}) SET w.type = 'concept'
            MERGE (b:Entity {name: $prereq}) SET b.type = 'concept'
            MERGE (c)-[:MENTIONS]->(w)
            MERGE (c)-[:MENTIONS]->(b)
            MERGE (w)-[r:REQUIRES]->(b) SET r.reason = 'a widget batches bases', r.origin = 'model'
            """,
            name=NAME,
            prereq=PREREQ,
        )
    yield
    _wipe()


def _wipe():
    with get_driver().session() as session:
        session.run(
            "MATCH (d:Document {course: 'CONCEPTTEST'}) "
            "OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk) DETACH DELETE d, c"
        )
        session.run("MATCH (e:Entity) WHERE e.name STARTS WITH 'ConceptTest' DETACH DELETE e")


def test_unknown_concept_is_a_404():
    assert client.get("/concepts/NotAConcept").status_code == 404


def test_explanation_is_written_on_first_request_and_cites_its_source(monkeypatch):
    monkeypatch.setattr(
        concept_service,
        "chat",
        lambda *_, **__: '{"summary": "A widget batches records.", '
        '"example": "Ten records in, two batches out."}',
    )

    body = client.get(f"/concepts/{NAME}").json()

    assert body["summary"] == "A widget batches records."
    assert body["example"] == "Ten records in, two batches out."
    assert body["sources"][0]["document_title"] == "Lecture 9"
    assert body["sources"][0]["page"] == 4


def test_prerequisites_come_back_with_the_reason_for_each():
    body = client.get(f"/concepts/{NAME}").json()

    assert body["requires"] == [
        {"name": PREREQ, "reason": "a widget batches bases", "origin": "model"}
    ]


def test_a_second_request_reads_the_cache_instead_of_the_model(monkeypatch):
    calls = []

    def once(*_, **__):
        calls.append(1)
        return '{"summary": "Written once.", "example": "Only once."}'

    monkeypatch.setattr(concept_service, "chat", once)

    client.get(f"/concepts/{NAME}")
    second = client.get(f"/concepts/{NAME}").json()

    assert len(calls) == 1
    assert second["summary"] == "Written once."


def test_a_model_that_returns_nothing_usable_is_a_502(monkeypatch):
    monkeypatch.setattr(concept_service, "chat", lambda *_, **__: "no json here")

    assert client.get(f"/concepts/{NAME}").status_code == 502
