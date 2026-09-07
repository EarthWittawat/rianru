import json

import pytest

from app.agents import coach


class FakeAgent:
    def __init__(self, content):
        self._content = content

    def invoke(self, _payload):
        return {"messages": [type("Msg", (), {"content": self._content})()]}


def _run_with(content, monkeypatch):
    monkeypatch.setattr(coach, "create_agent", lambda **kwargs: FakeAgent(content))
    return coach.plan_study()


WELL_FORMED = json.dumps(
    {
        "tasks": [
            {
                "action": "Redo the TF-IDF worked example by hand",
                "topic": "Textual Feature Representation",
                "source": {"document_title": "L6 - Text Feature Representation.pdf", "page": 19},
                "why": "you scored 2/7 here",
                "est_minutes": 25,
            }
        ]
    }
)


def test_returns_validated_tasks(monkeypatch):
    tasks = _run_with(WELL_FORMED, monkeypatch)

    assert len(tasks) == 1
    task = tasks[0]
    assert task["topic"] == "Textual Feature Representation"
    assert task["source"]["page"] == 19
    assert task["est_minutes"] == 25


def test_accepts_json_wrapped_in_a_fence(monkeypatch):
    tasks = _run_with(f"```json\n{WELL_FORMED}\n```", monkeypatch)
    assert len(tasks) == 1


def test_unparseable_output_is_an_empty_plan_not_a_crash(monkeypatch):
    assert _run_with("I could not work that out, sorry.", monkeypatch) == []


def test_empty_model_output_is_an_empty_plan(monkeypatch):
    assert _run_with("", monkeypatch) == []


def test_tasks_missing_an_action_or_topic_are_dropped(monkeypatch):
    payload = json.dumps(
        {
            "tasks": [
                {"topic": "No Action"},
                {"action": "No topic"},
                {"action": "Keep me", "topic": "Pattern Matching"},
            ]
        }
    )

    tasks = _run_with(payload, monkeypatch)

    assert [t["action"] for t in tasks] == ["Keep me"]


def test_a_task_with_no_usable_source_still_survives(monkeypatch):
    """Not every task needs reading; losing it entirely would be worse."""
    payload = json.dumps(
        {"tasks": [{"action": "Practise questions", "topic": "Web Scraping", "source": {}}]}
    )

    tasks = _run_with(payload, monkeypatch)

    assert len(tasks) == 1
    assert tasks[0]["source"] is None


def test_nonsense_page_numbers_are_dropped(monkeypatch):
    payload = json.dumps(
        {
            "tasks": [
                {
                    "action": "Read it",
                    "topic": "Pattern Matching",
                    "source": {"document_title": "L2.pdf", "page": "somewhere"},
                    "est_minutes": "ages",
                }
            ]
        }
    )

    tasks = _run_with(payload, monkeypatch)

    assert tasks[0]["source"]["page"] is None
    assert tasks[0]["est_minutes"] is None


@pytest.mark.slow
def test_live_coach_produces_a_plan_from_real_data():
    tasks = coach.plan_study()

    assert tasks, "the coach returned no tasks against real ingested material"
    assert all(t["action"] and t["topic"] for t in tasks)
