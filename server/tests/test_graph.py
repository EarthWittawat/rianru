from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import requires_ingested_corpus

client = TestClient(app)

pytestmark = requires_ingested_corpus


def test_graph_returns_nodes_and_edges():
    response = client.get("/graph")
    assert response.status_code == 200

    graph = response.json()
    assert graph["nodes"], "expected nodes from ingested material"
    assert graph["edges"], "expected edges between them"

    node = graph["nodes"][0]
    assert {"id", "label", "type"} <= set(node)
    assert {n["type"] for n in graph["nodes"]} <= {
        "Document",
        "Entity",
        "Highlight",
    }


def test_graph_edges_only_reference_returned_nodes():
    graph = client.get("/graph").json()
    node_ids = {n["id"] for n in graph["nodes"]}

    for edge in graph["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids


def test_graph_can_be_filtered_by_topic():
    full = client.get("/graph").json()
    topic = next(
        n["topic"] for n in full["nodes"] if n["type"] == "Document" and n.get("topic")
    )

    filtered = client.get("/graph", params={"topic": topic}).json()

    documents = [n for n in filtered["nodes"] if n["type"] == "Document"]
    assert documents, "expected documents for the filtered topic"
    assert all(n["topic"] == topic for n in documents)
    assert len(filtered["nodes"]) < len(full["nodes"])


def test_topics_endpoint_lists_available_topics():
    response = client.get("/graph/topics")
    assert response.status_code == 200
    topics = response.json()
    assert topics
    assert all(isinstance(t, str) for t in topics)
