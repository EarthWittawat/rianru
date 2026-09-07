import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers import coach as coach_router
from app.services import progress, study_plan

client = TestClient(app)

SAMPLE_TASKS = [
    {
        "action": "Redo the TF-IDF worked example",
        "topic": "Textual Feature Representation",
        "source": {"document_title": "L6.pdf", "page": 19},
        "why": "you scored 2/7 here",
        "est_minutes": 25,
    },
    {
        "action": "Answer more practice questions",
        "topic": "Web Scraping",
        "source": None,
        "why": "too few attempts to judge",
        "est_minutes": 15,
    },
]


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "progress_db_path", str(tmp_path / "progress.db"))
    progress.init_db()
    study_plan.init_db()
    yield


def test_generating_a_plan_stores_it(monkeypatch):
    monkeypatch.setattr(coach_router.coach_agent, "plan_study", lambda: SAMPLE_TASKS)

    response = client.post("/coach/plan")

    assert response.status_code == 200
    plan = response.json()
    assert len(plan["tasks"]) == 2
    assert plan["tasks"][0]["topic"] == "Textual Feature Representation"
    assert plan["tasks"][0]["source"]["page"] == 19
    assert plan["tasks"][1]["source"] is None
    assert all(task["done"] is False for task in plan["tasks"])


def test_latest_plan_is_returned_without_regenerating(monkeypatch):
    calls = {"n": 0}

    def counted():
        calls["n"] += 1
        return SAMPLE_TASKS

    monkeypatch.setattr(coach_router.coach_agent, "plan_study", counted)
    client.post("/coach/plan")

    fetched = client.get("/coach/plan/latest")

    assert fetched.status_code == 200
    assert len(fetched.json()["tasks"]) == 2
    assert calls["n"] == 1, "fetching a plan must not re-run the agent"


def test_latest_plan_is_404_before_anything_is_generated():
    assert client.get("/coach/plan/latest").status_code == 404


def test_ticking_a_task_persists(monkeypatch):
    monkeypatch.setattr(coach_router.coach_agent, "plan_study", lambda: SAMPLE_TASKS)
    task_id = client.post("/coach/plan").json()["tasks"][0]["id"]

    assert client.patch(f"/coach/tasks/{task_id}", json={"done": True}).status_code == 200

    refetched = client.get("/coach/plan/latest").json()
    done = {t["id"]: t["done"] for t in refetched["tasks"]}
    assert done[task_id] is True


def test_ticking_an_unknown_task_is_404():
    response = client.patch("/coach/tasks/nope", json={"done": True})
    assert response.status_code == 404


def test_an_empty_plan_is_reported_not_stored(monkeypatch):
    """A blank plan is a failure to surface, not a plan to save."""
    monkeypatch.setattr(coach_router.coach_agent, "plan_study", lambda: [])

    response = client.post("/coach/plan")

    assert response.status_code == 502
    assert study_plan.latest_plan() is None
