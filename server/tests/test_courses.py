"""Every course in the graph, and retrieval that stays inside one."""

import pytest

from app.services import graph_store
from app.services.chunking import Chunk
from app.services.neo4j_client import get_driver

COURSES = ("MULTIA", "MULTIB")


@pytest.fixture(autouse=True)
def two_courses():
    # These search, so they need the vector index. A developer machine has one
    # left over from ingest; a fresh CI database has nothing, and the query
    # fails with "There is no such vector schema index" rather than returning
    # no hits. The test seeds the schema it depends on.
    graph_store.ensure_schema()
    _await_indexes()

    _wipe()
    for course in COURSES:
        graph_store.write_document(
            doc_id=f"{course}::doc",
            title=f"{course} lecture",
            course=course,
            topic=f"{course} topic",
            activity_type="material",
            file_path=f"{course}.pdf",
            chunks=[
                Chunk(
                    text=f"Vector similarity in course {course} explains retrieval.",
                    source_path=f"{course}.pdf",
                    page=1,
                )
            ],
        )
    yield
    _wipe()


def _await_indexes() -> None:
    """A freshly created vector index answers queries with nothing until online."""
    with get_driver().session() as session:
        session.run("CALL db.awaitIndexes(60)")


def _wipe():
    with get_driver().session() as session:
        for course in COURSES:
            session.run(
                "MATCH (d:Document {course: $course}) "
                "OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk) DETACH DELETE d, c",
                course=course,
            )


def test_courses_are_listed_with_what_they_contain():
    courses = {c["code"]: c for c in graph_store.list_courses()}

    assert set(COURSES) <= set(courses)
    assert courses["MULTIA"]["documents"] == 1
    assert courses["MULTIA"]["chunks"] == 1


def test_similarity_search_can_be_held_to_one_course():
    hits = graph_store.similarity_search("vector similarity retrieval", course="MULTIA")

    assert hits, "expected the seeded chunk"
    assert all(hit["document_id"].startswith("MULTIA") for hit in hits)


def test_similarity_search_without_a_course_still_searches_everything():
    hits = graph_store.similarity_search("vector similarity retrieval", top_k=50)

    documents = {hit["document_id"] for hit in hits}
    assert any(doc.startswith("MULTIA") for doc in documents)
    assert any(doc.startswith("MULTIB") for doc in documents)
