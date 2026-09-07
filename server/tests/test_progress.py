import pytest

from app.config import settings
from app.services import progress


@pytest.fixture(autouse=True)
def temp_progress_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "progress_db_path", str(tmp_path / "progress.db"))
    progress.init_db()
    yield


def _record(topic, correct, question_id="q", graded_by="auto"):
    return progress.record_attempt(
        question_id=question_id,
        topic=topic,
        question_format="multiple_choice",
        chosen_answer="whatever",
        is_correct=correct,
        graded_by=graded_by,
    )


def test_init_db_is_safe_to_run_twice():
    progress.init_db()
    assert progress.topic_stats() == []


def test_record_attempt_persists_a_row():
    _record("Pattern Matching", True)

    stats = progress.topic_stats()

    assert len(stats) == 1
    assert stats[0]["topic"] == "Pattern Matching"
    assert stats[0]["attempted"] == 1
    assert stats[0]["correct"] == 1
    assert stats[0]["accuracy"] == 1.0


def test_topic_stats_aggregates_per_topic():
    _record("Pattern Matching", True)
    _record("Pattern Matching", False)
    _record("Web Scraping", True)

    stats = {s["topic"]: s for s in progress.topic_stats()}

    assert stats["Pattern Matching"]["attempted"] == 2
    assert stats["Pattern Matching"]["correct"] == 1
    assert stats["Pattern Matching"]["accuracy"] == 0.5
    assert stats["Web Scraping"]["accuracy"] == 1.0


def test_weak_topics_orders_worst_first():
    for _ in range(4):
        _record("Strong Topic", True)
    for _ in range(4):
        _record("Weak Topic", False)
    for i in range(4):
        _record("Middling Topic", i < 2)

    weak = [t["topic"] for t in progress.weak_topics(min_attempts=3)]

    assert weak[0] == "Weak Topic"
    assert weak.index("Middling Topic") < weak.index("Strong Topic")


def test_weak_topics_ignores_topics_below_the_attempt_threshold():
    """One unlucky answer should not brand a topic as your weakest."""
    _record("Barely Tried", False)
    for i in range(5):
        _record("Genuinely Weak", i < 1)

    weak = [t["topic"] for t in progress.weak_topics(min_attempts=3)]

    assert "Barely Tried" not in weak
    assert weak == ["Genuinely Weak"]


def test_weak_topics_respects_limit():
    for topic in ("A", "B", "C"):
        for _ in range(3):
            _record(topic, False)

    assert len(progress.weak_topics(limit=2, min_attempts=3)) == 2


def test_self_graded_attempts_are_distinguishable():
    _record("Pattern Matching", True, graded_by="self")
    _record("Pattern Matching", True, graded_by="auto")

    recent = progress.recent_attempts()

    assert {a["graded_by"] for a in recent} == {"self", "auto"}


def test_recent_attempts_can_filter_by_topic():
    _record("Pattern Matching", True)
    _record("Web Scraping", False)

    scoped = progress.recent_attempts(topic="Web Scraping")

    assert len(scoped) == 1
    assert scoped[0]["topic"] == "Web Scraping"
    assert scoped[0]["is_correct"] == 0
