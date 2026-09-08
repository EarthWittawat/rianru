"""The spine of the learning path: which document teaches a concept first."""

import pytest

from app.services import graph_store
from app.services.chunking import Chunk
from app.services.neo4j_client import get_driver

COURSE = "ORDERTEST"


@pytest.fixture(autouse=True)
def clean_course():
    _wipe()
    yield
    _wipe()


def _wipe():
    with get_driver().session() as session:
        session.run(
            "MATCH (d:Document {course: $course}) "
            "OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk) DETACH DELETE d, c",
            course=COURSE,
        )
        session.run("MATCH (e:Entity) WHERE e.name STARTS WITH 'OrderTest' DETACH DELETE e")


def _write_lecture(index: int, concepts: list[str]) -> str:
    doc_id = f"{COURSE}::lecture-{index}"
    graph_store.write_document(
        doc_id=doc_id,
        title=f"Lecture {index}",
        course=COURSE,
        topic=f"Topic {index}",
        activity_type="material",
        file_path=f"L{index}.pdf",
        chunks=[Chunk(text=f"Lecture {index} text", source_path=f"L{index}.pdf", page=1)],
    )
    graph_store.write_entities(
        f"{doc_id}::0", [{"name": name, "type": "concept"} for name in concepts], []
    )
    return doc_id


def test_position_is_stored_on_the_document():
    doc_id = _write_lecture(1, ["OrderTest Alpha"])
    graph_store.set_document_positions({doc_id: 3})

    with get_driver().session() as session:
        position = session.run(
            "MATCH (d:Document {id: $id}) RETURN d.position AS position", id=doc_id
        ).single()["position"]

    assert position == 3


def test_a_concept_takes_the_position_of_the_first_document_that_teaches_it():
    early = _write_lecture(1, ["OrderTest Shared", "OrderTest Early"])
    late = _write_lecture(2, ["OrderTest Shared", "OrderTest Late"])
    graph_store.set_document_positions({early: 0, late: 1})

    positions = graph_store.concept_positions(COURSE)

    assert positions["OrderTest Early"] == 0
    assert positions["OrderTest Shared"] == 0, "first taught in lecture 1, not lecture 2"
    assert positions["OrderTest Late"] == 1


def test_documents_without_a_position_do_not_place_a_concept():
    _write_lecture(1, ["OrderTest Unplaced"])

    positions = graph_store.concept_positions(COURSE)

    assert "OrderTest Unplaced" not in positions


def test_requirement_edges_are_stored_with_their_reason():
    _write_lecture(1, ["OrderTest Base"])
    _write_lecture(2, ["OrderTest Built"])

    graph_store.write_requirements(
        [
            {
                "source": "OrderTest Built",
                "target": "OrderTest Base",
                "origin": "timeline",
                "reason": "taught first",
            }
        ]
    )

    with get_driver().session() as session:
        record = session.run(
            """
            MATCH (a:Entity {name: 'OrderTest Built'})-[r:REQUIRES]->(b:Entity)
            RETURN b.name AS target, r.origin AS origin, r.reason AS reason
            """
        ).single()

    assert record["target"] == "OrderTest Base"
    assert record["origin"] == "timeline"
    assert record["reason"] == "taught first"


def test_rebuilding_replaces_edges_of_one_origin_only():
    _write_lecture(1, ["OrderTest Base"])
    _write_lecture(2, ["OrderTest Built"])
    graph_store.write_requirements(
        [
            {
                "source": "OrderTest Built",
                "target": "OrderTest Base",
                "origin": "timeline",
                "reason": "a",
            }
        ]
    )
    graph_store.write_requirements(
        [
            {
                "source": "OrderTest Base",
                "target": "OrderTest Built",
                "origin": "model",
                "reason": "b",
            }
        ]
    )

    graph_store.clear_requirements(COURSE, origin="timeline")

    with get_driver().session() as session:
        remaining = [
            record["origin"]
            for record in session.run(
                "MATCH (a:Entity)-[r:REQUIRES]->(b:Entity) "
                "WHERE a.name STARTS WITH 'OrderTest' RETURN r.origin AS origin"
            )
        ]

    assert remaining == ["model"]
