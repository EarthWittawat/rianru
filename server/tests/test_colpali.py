"""Page-image retrieval: keys, rendering, and what search hands back."""

import numpy as np
import pytest

from app.services import colpali_index
from app.services.multivector import maxsim, rank, save_index


def test_a_page_key_round_trips():
    key = colpali_index.page_key("CPE393::doc::L1.pdf", 7)

    assert colpali_index.parse_key(key) == ("CPE393::doc::L1.pdf", 7)


def test_a_key_that_is_not_a_page_is_rejected_rather_than_guessed():
    assert colpali_index.parse_key("CPE393::doc::L1.pdf") is None


def test_a_document_id_containing_the_separator_still_parses():
    # Document ids are course::activity::filename, so "::" is everywhere.
    key = colpali_index.page_key("CPE393::11005574::L1 - Intro.pdf", 12)

    assert colpali_index.parse_key(key) == ("CPE393::11005574::L1 - Intro.pdf", 12)


def test_search_returns_documents_and_pages(monkeypatch, tmp_path):
    index = {
        colpali_index.page_key("DEMO::doc", 1): np.array([[1.0, 0.0]]),
        colpali_index.page_key("DEMO::doc", 2): np.array([[0.0, 1.0]]),
    }
    path = tmp_path / "DEMO.npz"
    save_index(path, index)

    monkeypatch.setattr(colpali_index, "index_path", lambda course: path)
    colpali_index.cached_index.cache_clear()
    monkeypatch.setattr(colpali_index, "encode_query", lambda text: np.array([[0.0, 1.0]]))

    hits = colpali_index.search("a chart", "DEMO", top_k=1)

    assert hits == [{"document_id": "DEMO::doc", "page": 2, "score": pytest.approx(1.0)}]
    colpali_index.cached_index.cache_clear()


def test_search_without_an_index_is_empty_not_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr(colpali_index, "index_path", lambda course: tmp_path / "none.npz")
    colpali_index.cached_index.cache_clear()

    assert colpali_index.search("anything", "DEMO") == []
    colpali_index.cached_index.cache_clear()


def test_page_scoring_uses_the_same_late_interaction_rule():
    query = np.array([[1.0, 0.0]])
    page = np.array([[1.0, 0.0], [-1.0, 0.0]])

    assert maxsim(query, page) == pytest.approx(1.0)
    assert rank(query, {"a": page}, top_k=1)[0][0] == "a"
