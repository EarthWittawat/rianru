import pytest

from app.services.chunking import Chunk
from app.services.embeddings import EMBEDDING_DIM, embed_texts
from app.services.graph_store import (
    ensure_schema,
    similarity_search,
    write_document,
)
from app.services.neo4j_client import get_driver

TEST_DOC_ID = "pytest-embeddings-doc"


@pytest.fixture(autouse=True)
def clean_test_document():
    _delete_test_document()
    yield
    _delete_test_document()


def _delete_test_document():
    with get_driver().session() as session:
        session.run(
            "MATCH (d:Document {id: $id}) "
            "OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk) "
            "DETACH DELETE d, c",
            id=TEST_DOC_ID,
        )


def test_embed_texts_returns_fixed_dimension_vectors():
    vectors = embed_texts(["TF-IDF weights rare terms", "regular expressions"])

    assert len(vectors) == 2
    assert all(len(v) == EMBEDDING_DIM for v in vectors)
    assert all(isinstance(x, float) for x in vectors[0])


def test_write_document_creates_document_and_chunk_nodes():
    chunks = [
        Chunk(text="Tokenization splits text into tokens.", source_path="a.pdf", page=1),
        Chunk(text="Stemming reduces words to a root form.", source_path="a.pdf", page=2),
    ]

    write_document(
        doc_id=TEST_DOC_ID,
        title="Pytest Doc",
        course="CPE393",
        topic="Testing",
        activity_type="material",
        file_path="a.pdf",
        chunks=chunks,
    )

    with get_driver().session() as session:
        record = session.run(
            "MATCH (d:Document {id: $id})-[:HAS_CHUNK]->(c:Chunk) "
            "RETURN d.title AS title, count(c) AS chunk_count",
            id=TEST_DOC_ID,
        ).single()

    assert record["title"] == "Pytest Doc"
    assert record["chunk_count"] == 2


def test_write_document_is_idempotent():
    chunks = [Chunk(text="Only chunk.", source_path="a.pdf", page=1)]

    write_document(
        doc_id=TEST_DOC_ID,
        title="Pytest Doc",
        course="CPE393",
        topic="Testing",
        activity_type="material",
        file_path="a.pdf",
        chunks=chunks,
    )
    write_document(
        doc_id=TEST_DOC_ID,
        title="Pytest Doc",
        course="CPE393",
        topic="Testing",
        activity_type="material",
        file_path="a.pdf",
        chunks=chunks,
    )

    with get_driver().session() as session:
        count = session.run(
            "MATCH (d:Document {id: $id})-[:HAS_CHUNK]->(c:Chunk) RETURN count(c) AS n",
            id=TEST_DOC_ID,
        ).single()["n"]

    assert count == 1


def test_similarity_search_finds_the_matching_chunk():
    ensure_schema()
    chunks = [
        Chunk(
            text="TF-IDF down-weights terms that appear in many documents.",
            source_path="a.pdf",
            page=1,
        ),
        Chunk(
            text="Web scraping with BeautifulSoup parses HTML tags.",
            source_path="a.pdf",
            page=2,
        ),
    ]
    write_document(
        doc_id=TEST_DOC_ID,
        title="Pytest Doc",
        course="CPE393",
        topic="Testing",
        activity_type="material",
        file_path="a.pdf",
        chunks=chunks,
    )

    hits = similarity_search("how does tf-idf weight common words", top_k=5)

    assert hits, "expected at least one similarity hit"
    texts = [h["text"] for h in hits]
    assert any("TF-IDF" in t for t in texts)
