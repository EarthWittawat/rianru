import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import quiz as quiz_service
from app.services.neo4j_client import get_driver

client = TestClient(app)

SAMPLE_RESPONSE = json.dumps(
    {
        "questions": [
            {
                "format": "multiple_choice",
                "question": "What does IDF weight against?",
                "options": ["Rare terms", "Common terms", "Long terms", "Digits"],
                "answer": "Common terms",
                "explanation": "IDF down-weights terms appearing in many documents.",
            },
            {
                "format": "short_answer",
                "question": "Name the two factors multiplied in TF-IDF.",
                "answer": "Term frequency and inverse document frequency.",
                "explanation": "TF-IDF is TF multiplied by IDF.",
            },
        ]
    }
)


@pytest.fixture(autouse=True)
def clean_generated_questions():
    yield
    with get_driver().session() as session:
        session.run(
            "MATCH (q:QuizQuestion) WHERE q.question STARTS WITH 'What does IDF' "
            "OR q.question STARTS WITH 'Name the two factors' DETACH DELETE q"
        )


def _a_topic() -> str:
    return client.get("/graph/topics").json()[0]


def test_generate_returns_both_question_formats(monkeypatch):
    captured = {}

    def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return SAMPLE_RESPONSE

    monkeypatch.setattr(quiz_service, "chat", fake_chat)

    response = client.post("/quiz/generate", json={"topic": _a_topic(), "count": 2})

    assert response.status_code == 200
    questions = response.json()["questions"]
    assert {q["format"] for q in questions} == {"multiple_choice", "short_answer"}
    assert len(captured["messages"][-1]["content"]) > 200, "excerpts must be prompted"


def test_generated_questions_are_persisted_and_refetchable(monkeypatch):
    monkeypatch.setattr(quiz_service, "chat", lambda messages, **kwargs: SAMPLE_RESPONSE)
    topic = _a_topic()

    client.post("/quiz/generate", json={"topic": topic, "count": 2})
    stored = client.get("/quiz", params={"topic": topic}).json()["questions"]

    assert any(q["question"] == "What does IDF weight against?" for q in stored)


def test_multiple_choice_answer_must_be_one_of_its_options(monkeypatch):
    bad = json.dumps(
        {
            "questions": [
                {
                    "format": "multiple_choice",
                    "question": "Broken question",
                    "options": ["a", "b", "c", "d"],
                    "answer": "not in the options",
                    "explanation": "x",
                }
            ]
        }
    )
    monkeypatch.setattr(quiz_service, "chat", lambda messages, **kwargs: bad)

    response = client.post("/quiz/generate", json={"topic": _a_topic(), "count": 1})

    assert response.status_code == 200
    assert response.json()["questions"] == [], "invalid question should be dropped"


def test_unknown_topic_returns_404(monkeypatch):
    monkeypatch.setattr(quiz_service, "chat", lambda messages, **kwargs: SAMPLE_RESPONSE)
    response = client.post("/quiz/generate", json={"topic": "No Such Topic"})
    assert response.status_code == 404


def test_malformed_model_output_is_a_502(monkeypatch):
    monkeypatch.setattr(
        quiz_service, "chat", lambda messages, **kwargs: "I cannot do that."
    )
    response = client.post("/quiz/generate", json={"topic": _a_topic()})
    assert response.status_code == 502
