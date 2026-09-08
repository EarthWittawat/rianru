import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.graph_store import ensure_schema
from app.services.neo4j_client import get_driver
from tests.conftest import requires_ingested_corpus

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_highlights():
    _cleanup()
    ensure_schema()
    yield
    _cleanup()


def _cleanup():
    with get_driver().session() as session:
        session.run(
            "MATCH (h:Highlight) WHERE h.selected_text STARTS WITH 'PYTEST' DETACH DELETE h"
        )


def _pdf_document() -> dict:
    documents = client.get("/documents").json()
    pdf_doc = max(
        (d for d in documents if d["file_type"] == "pdf"),
        key=lambda d: d["chunk_count"],
    )
    return client.get(f"/documents/{pdf_doc['id']}").json()


@requires_ingested_corpus
def test_saving_a_highlight_links_it_to_its_chunk():
    document = _pdf_document()
    chunk = document["chunks"][1]

    response = client.post(
        "/highlights",
        json={
            "chunk_id": chunk["id"],
            "selected_text": "PYTEST selection one",
            "explanation": "Because tests need a highlight.",
        },
    )

    assert response.status_code == 200
    highlight_id = response.json()["id"]

    with get_driver().session() as session:
        record = session.run(
            """
            MATCH (c:Chunk)-[:HAS_HIGHLIGHT]->(h:Highlight {id: $id})
            RETURN c.id AS chunk_id, h.selected_text AS text, h.explanation AS explanation
            """,
            id=highlight_id,
        ).single()

    assert record["chunk_id"] == chunk["id"]
    assert record["text"] == "PYTEST selection one"
    assert record["explanation"] == "Because tests need a highlight."


@requires_ingested_corpus
def test_highlight_mentions_entities_found_in_the_selection():
    document = _pdf_document()
    chunk = document["chunks"][1]

    with get_driver().session() as session:
        session.run("MERGE (e:Entity {name: 'Tokenization'}) SET e.type = 'concept'")

    response = client.post(
        "/highlights",
        json={
            "chunk_id": chunk["id"],
            "selected_text": "PYTEST Tokenization splits text into tokens",
            "explanation": "x",
        },
    )
    highlight_id = response.json()["id"]

    with get_driver().session() as session:
        mentioned = session.run(
            "MATCH (:Highlight {id: $id})-[:MENTIONS]->(e:Entity) RETURN e.name AS name",
            id=highlight_id,
        ).value()

    assert "Tokenization" in mentioned


def test_highlights_survive_reingesting_the_document():
    """Re-running ingest must not destroy the student's own saved work."""
    from app.services.chunking import Chunk
    from app.services.graph_store import write_document

    doc_id = "pytest-reingest-doc"
    chunks = [
        Chunk(text="Stemming reduces words to a root form.", source_path="a.pdf", page=1),
        Chunk(text="Lemmatization uses a dictionary instead.", source_path="a.pdf", page=2),
    ]
    write_kwargs = dict(
        doc_id=doc_id,
        title="Re-ingest Doc",
        course="CPE393",
        topic="Testing",
        activity_type="material",
        file_path="a.pdf",
        chunks=chunks,
    )
    write_document(**write_kwargs)

    saved = client.post(
        "/highlights",
        json={
            "chunk_id": f"{doc_id}::1",
            "selected_text": "PYTEST survives re-ingest",
            "explanation": "should still be attached afterwards",
        },
    )
    assert saved.status_code == 200
    highlight_id = saved.json()["id"]

    write_document(**write_kwargs)

    try:
        with get_driver().session() as session:
            record = session.run(
                """
                MATCH (h:Highlight {id: $id})
                OPTIONAL MATCH (c:Chunk)-[:HAS_HIGHLIGHT]->(h)
                RETURN c.id AS chunk_id, c.text AS chunk_text
                """,
                id=highlight_id,
            ).single()

        assert record["chunk_id"] == f"{doc_id}::1", (
            "highlight was orphaned by re-ingest"
        )
        assert "Lemmatization" in record["chunk_text"]
    finally:
        with get_driver().session() as session:
            session.run(
                "MATCH (d:Document {id: $id}) "
                "OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk) "
                "OPTIONAL MATCH (c)-[:HAS_HIGHLIGHT]->(h:Highlight) "
                "DETACH DELETE d, c, h",
                id=doc_id,
            )


def test_unknown_chunk_returns_404():
    response = client.post(
        "/highlights",
        json={
            "chunk_id": "nope::0",
            "selected_text": "PYTEST orphan",
            "explanation": "x",
        },
    )
    assert response.status_code == 404


@requires_ingested_corpus
def test_lists_saved_highlights():
    document = _pdf_document()
    chunk = document["chunks"][1]
    client.post(
        "/highlights",
        json={
            "chunk_id": chunk["id"],
            "selected_text": "PYTEST listed highlight",
            "explanation": "x",
        },
    )

    response = client.get("/highlights")

    assert response.status_code == 200
    texts = [h["selected_text"] for h in response.json()]
    assert "PYTEST listed highlight" in texts
