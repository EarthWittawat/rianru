import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import progress

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_progress_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "progress_db_path", str(tmp_path / "progress.db"))
    progress.init_db()
    yield


@pytest.fixture
def stored_question():
    """A real QuizQuestion in Neo4j, since grading looks the answer up there."""
    from app.services.neo4j_client import get_driver

    question = {
        "id": "pytest-progress-question",
        "topic": "Pytest Topic",
        "format": "multiple_choice",
        "question": "Which option is right?",
        "options": ["right one", "wrong one"],
        "answer": "right one",
        "explanation": "because",
    }
    with get_driver().session() as session:
        session.run(
            """
            CREATE (q:QuizQuestion {
                id: $id, topic: $topic, format: $format, question: $question,
                options: $options, answer: $answer, explanation: $explanation,
                created_at: datetime()
            })
            """,
            **question,
        )
    yield question
    with get_driver().session() as session:
        session.run("MATCH (q:QuizQuestion {id: $id}) DETACH DELETE q", id=question["id"])


def test_correct_multiple_choice_answer_is_graded_right(stored_question):
    response = client.post(
        "/progress/attempts",
        json={"question_id": stored_question["id"], "chosen_answer": "right one"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is True
    assert body["correct_answer"] == "right one"
    assert body["graded_by"] == "auto"


def test_wrong_multiple_choice_answer_is_graded_wrong(stored_question):
    response = client.post(
        "/progress/attempts",
        json={"question_id": stored_question["id"], "chosen_answer": "wrong one"},
    )

    assert response.json()["is_correct"] is False
    assert progress.topic_stats()[0]["correct"] == 0


def test_client_cannot_assert_its_own_correctness(stored_question):
    """Grading is the server's job — a client claiming success must not win."""
    client.post(
        "/progress/attempts",
        json={
            "question_id": stored_question["id"],
            "chosen_answer": "wrong one",
            "is_correct": True,
        },
    )

    assert progress.topic_stats()[0]["correct"] == 0


def test_short_answer_accepts_a_self_grade(stored_question):
    response = client.post(
        "/progress/attempts",
        json={"question_id": stored_question["id"], "self_grade": True},
    )

    assert response.status_code == 200
    assert response.json()["graded_by"] == "self"
    assert progress.recent_attempts()[0]["graded_by"] == "self"


def test_attempt_without_answer_or_self_grade_is_rejected(stored_question):
    response = client.post(
        "/progress/attempts", json={"question_id": stored_question["id"]}
    )
    assert response.status_code == 422


def test_unknown_question_returns_404():
    response = client.post(
        "/progress/attempts",
        json={"question_id": "does-not-exist", "chosen_answer": "x"},
    )
    assert response.status_code == 404


def test_topics_and_weak_endpoints(stored_question):
    for chosen in ("wrong one", "wrong one", "right one"):
        client.post(
            "/progress/attempts",
            json={"question_id": stored_question["id"], "chosen_answer": chosen},
        )

    topics = client.get("/progress/topics").json()
    assert topics[0]["topic"] == "Pytest Topic"
    assert topics[0]["attempted"] == 3
    assert topics[0]["correct"] == 1

    weak = client.get("/progress/weak", params={"min_attempts": 3}).json()
    assert weak[0]["topic"] == "Pytest Topic"
