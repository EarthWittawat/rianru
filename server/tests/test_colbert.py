"""Late-interaction scoring, and an index that survives a restart."""

import numpy as np
import pytest

from app.services import colbert_index


def test_maxsim_rewards_a_document_that_covers_every_query_token():
    query = np.array([[1.0, 0.0], [0.0, 1.0]])
    covers_both = np.array([[1.0, 0.0], [0.0, 1.0]])
    covers_one = np.array([[1.0, 0.0], [1.0, 0.0]])

    assert colbert_index.maxsim(query, covers_both) > colbert_index.maxsim(
        query, covers_one
    )


def test_maxsim_takes_the_best_match_per_query_token_not_the_average():
    query = np.array([[1.0, 0.0]])
    # One token matches exactly; the rest are noise that an average would punish.
    document = np.array([[1.0, 0.0], [-1.0, 0.0], [-1.0, 0.0]])

    assert colbert_index.maxsim(query, document) == pytest.approx(1.0)


def test_ranking_returns_the_best_documents_first():
    query = np.array([[1.0, 0.0]])
    documents = {
        "far": np.array([[0.0, 1.0]]),
        "near": np.array([[0.9, 0.1]]),
        "exact": np.array([[1.0, 0.0]]),
    }

    ranked = colbert_index.rank(query, documents, top_k=2)

    assert [chunk_id for chunk_id, _ in ranked] == ["exact", "near"]


def test_an_index_round_trips_through_disk(tmp_path):
    documents = {"a::0": np.array([[1.0, 0.0]]), "a::1": np.array([[0.0, 1.0]])}
    path = tmp_path / "DEMO.npz"

    colbert_index.save_index(path, documents)
    loaded = colbert_index.load_index(path)

    assert set(loaded) == set(documents)
    assert np.allclose(loaded["a::0"], documents["a::0"])


def test_a_missing_index_reads_as_empty_rather_than_raising(tmp_path):
    assert colbert_index.load_index(tmp_path / "nothing.npz") == {}


from app.services import chat as chat_service  # noqa: E402


def test_chat_prefers_late_interaction_when_the_course_has_an_index(monkeypatch):
    monkeypatch.setattr(colbert_index, "has_index", lambda course: True)
    monkeypatch.setattr(
        colbert_index, "search", lambda *_, **__: [("DEMO::0", 12.5)]
    )
    monkeypatch.setattr(
        chat_service,
        "chunks_by_id",
        lambda ids: {
            "DEMO::0": {
                "chunk_id": "DEMO::0",
                "text": "a chunk",
                "page": 2,
                "document_id": "DEMO",
                "document_title": "Demo",
                "topic": "Demo topic",
            }
        },
    )

    sources = chat_service.retrieve("a question", course="DEMO")

    assert [s["retrieval"] for s in sources] == ["colbert"]
    assert sources[0]["page"] == 2


def test_chat_falls_back_to_dense_without_an_index(monkeypatch):
    monkeypatch.setattr(colbert_index, "has_index", lambda course: False)
    monkeypatch.setattr(
        chat_service,
        "similarity_search",
        lambda *_, **__: [{"chunk_id": "DEMO::1", "text": "dense hit"}],
    )

    sources = chat_service.retrieve("a question", course="DEMO")

    assert [s["retrieval"] for s in sources] == ["dense"]


def test_an_index_that_returns_nothing_usable_falls_back(monkeypatch):
    monkeypatch.setattr(colbert_index, "has_index", lambda course: True)
    monkeypatch.setattr(colbert_index, "search", lambda *_, **__: [("gone::9", 1.0)])
    monkeypatch.setattr(chat_service, "chunks_by_id", lambda ids: {})
    monkeypatch.setattr(
        chat_service,
        "similarity_search",
        lambda *_, **__: [{"chunk_id": "DEMO::1", "text": "dense hit"}],
    )

    assert chat_service.retrieve("a question", course="DEMO")[0]["retrieval"] == "dense"
