"""The tool layer must work without any model in the loop."""

import json

import pytest

from app.agents import tools
from app.config import settings
from app.services import progress


@pytest.fixture(autouse=True)
def temp_progress_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "progress_db_path", str(tmp_path / "progress.db"))
    progress.init_db()
    yield


def _attempt(topic, correct):
    progress.record_attempt(
        question_id="q",
        topic=topic,
        question_format="multiple_choice",
        is_correct=correct,
        graded_by="auto",
    )


def test_weak_topics_tool_returns_json():
    for _ in range(4):
        _attempt("Weak Topic", False)
    for _ in range(4):
        _attempt("Strong Topic", True)

    payload = json.loads(tools.get_weak_topics.invoke({"limit": 5}))

    assert payload[0]["topic"] == "Weak Topic"
    assert payload[0]["accuracy"] == 0.0


def test_topic_stats_tool_returns_json():
    _attempt("Pattern Matching", True)

    payload = json.loads(tools.get_topic_stats.invoke({}))

    assert payload[0]["topic"] == "Pattern Matching"


def test_recent_attempts_tool_filters_by_topic():
    _attempt("Pattern Matching", True)
    _attempt("Web Scraping", False)

    payload = json.loads(
        tools.get_recent_attempts.invoke({"topic": "Web Scraping", "limit": 10})
    )

    assert len(payload) == 1
    assert payload[0]["topic"] == "Web Scraping"


def test_search_tool_returns_citable_excerpts():
    payload = json.loads(
        tools.search_course_material.invoke({"query": "regular expressions", "limit": 3})
    )

    assert payload, "expected hits from the ingested course material"
    hit = payload[0]
    assert {"document_id", "document_title", "topic", "page", "excerpt"} <= set(hit)
    assert hit["excerpt"]


def test_list_topics_tool_covers_the_ingested_course():
    topics = json.loads(tools.list_topics.invoke({}))

    assert "Pattern Matching" in topics


def test_list_topic_documents_tool_returns_real_documents():
    payload = json.loads(tools.list_topic_documents.invoke({"topic": "Pattern Matching"}))

    assert payload
    assert all(d["document_id"] for d in payload)
    assert any(d["chunks"] > 0 for d in payload)


def test_every_tool_has_a_description_for_the_model():
    """A tool the model cannot understand is a tool it will not call."""
    for tool in tools.PROGRESS_TOOLS + tools.MATERIAL_TOOLS:
        assert tool.description.strip(), f"{tool.name} has no description"
