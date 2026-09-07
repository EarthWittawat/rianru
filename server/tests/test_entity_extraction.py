import pytest

from app.services.entity_extraction import (
    extract_graph_from_text,
    parse_extraction_response,
)
from app.services.graph_store import ensure_schema, write_entities
from app.services.neo4j_client import get_driver

TEST_CHUNK_ID = "pytest-entities-chunk"


@pytest.fixture(autouse=True)
def clean_test_data():
    _cleanup()
    yield
    _cleanup()


def _cleanup():
    with get_driver().session() as session:
        session.run("MATCH (c:Chunk {id: $id}) DETACH DELETE c", id=TEST_CHUNK_ID)
        session.run(
            "MATCH (e:Entity) WHERE e.name IN $names DETACH DELETE e",
            names=["TF-IDF", "Bag of Words", "Tokenization"],
        )


def test_parses_clean_json():
    raw = (
        '{"entities": [{"name": "TF-IDF", "type": "method"}], '
        '"relations": [{"source": "TF-IDF", "target": "Bag of Words", "type": "extends"}]}'
    )
    entities, relations = parse_extraction_response(raw)

    assert entities == [{"name": "TF-IDF", "type": "method"}]
    assert relations == []  # target not in entity list, so dropped


def test_parses_json_wrapped_in_markdown_fence():
    raw = '```json\n{"entities": [{"name": "Tokenization", "type": "concept"}], "relations": []}\n```'
    entities, relations = parse_extraction_response(raw)

    assert entities == [{"name": "Tokenization", "type": "concept"}]
    assert relations == []


def test_keeps_relations_between_known_entities():
    raw = (
        '{"entities": [{"name": "TF-IDF", "type": "method"}, '
        '{"name": "Bag of Words", "type": "method"}], '
        '"relations": [{"source": "TF-IDF", "target": "Bag of Words", "type": "extends"}]}'
    )
    _, relations = parse_extraction_response(raw)

    assert relations == [
        {"source": "TF-IDF", "target": "Bag of Words", "type": "extends"}
    ]


def test_malformed_json_yields_empty_rather_than_raising():
    entities, relations = parse_extraction_response("I could not find any entities.")

    assert entities == []
    assert relations == []


def test_drops_entries_missing_required_fields():
    raw = '{"entities": [{"type": "method"}, {"name": "TF-IDF", "type": "method"}], "relations": [{"source": "TF-IDF"}]}'
    entities, relations = parse_extraction_response(raw)

    assert entities == [{"name": "TF-IDF", "type": "method"}]
    assert relations == []


def test_extraction_failure_is_not_fatal(monkeypatch):
    from app.services import entity_extraction

    def boom(*args, **kwargs):
        raise entity_extraction.VLLMError("gateway down")

    monkeypatch.setattr(entity_extraction, "chat", boom)

    entities, relations = extract_graph_from_text("some course text")

    assert entities == []
    assert relations == []


def test_write_entities_merges_duplicates():
    ensure_schema()
    with get_driver().session() as session:
        session.run("CREATE (c:Chunk {id: $id, text: 'x'})", id=TEST_CHUNK_ID)

    entities = [
        {"name": "TF-IDF", "type": "method"},
        {"name": "TF-IDF", "type": "method"},
        {"name": "Bag of Words", "type": "method"},
    ]
    relations = [{"source": "TF-IDF", "target": "Bag of Words", "type": "extends"}]

    write_entities(TEST_CHUNK_ID, entities, relations)
    write_entities(TEST_CHUNK_ID, entities, relations)

    with get_driver().session() as session:
        entity_count = session.run(
            "MATCH (e:Entity) WHERE e.name IN ['TF-IDF', 'Bag of Words'] "
            "RETURN count(e) AS n"
        ).single()["n"]
        mention_count = session.run(
            "MATCH (:Chunk {id: $id})-[m:MENTIONS]->(:Entity) RETURN count(m) AS n",
            id=TEST_CHUNK_ID,
        ).single()["n"]
        relation_count = session.run(
            "MATCH (:Entity {name: 'TF-IDF'})-[r:RELATES_TO]->(:Entity {name: 'Bag of Words'}) "
            "RETURN count(r) AS n"
        ).single()["n"]

    assert entity_count == 2
    assert mention_count == 2
    assert relation_count == 1
