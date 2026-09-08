from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import requires_ingested_corpus

client = TestClient(app)

pytestmark = requires_ingested_corpus


def test_path_returns_stages_in_teaching_order():
    response = client.get("/path")
    assert response.status_code == 200

    stages = response.json()["stages"]
    assert stages, "expected positioned documents; run scripts/set_positions.py"
    positions = [stage["position"] for stage in stages]
    assert positions == sorted(positions)


def test_concepts_are_ordered_by_how_deep_their_prerequisites_run():
    stages = client.get("/path").json()["stages"]

    for stage in stages:
        depths = [concept["depth"] for concept in stage["concepts"]]
        assert depths == sorted(depths)


def test_edges_only_reference_concepts_the_path_returned():
    body = client.get("/path").json()
    names = {c["name"] for stage in body["stages"] for c in stage["concepts"]}

    for edge in body["edges"]:
        assert edge["source"] in names
        assert edge["target"] in names


def test_the_mention_floor_thins_the_path():
    wide = client.get("/path", params={"min_mentions": 1}).json()
    narrow = client.get("/path", params={"min_mentions": 5}).json()

    def total(body):
        return sum(len(stage["concepts"]) for stage in body["stages"])

    assert total(narrow) < total(wide)
