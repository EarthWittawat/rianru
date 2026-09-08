"""An index knows which model built it, because two models share no vector space."""

import numpy as np

from app.services import colpali_index
from app.services.multivector import index_model, load_index, save_index


def test_an_index_records_the_model_that_built_it(tmp_path):
    path = tmp_path / "DEMO.npz"
    save_index(path, {"a": np.array([[1.0, 0.0]])}, model="vidore/colSmol-500M")

    assert index_model(path) == "vidore/colSmol-500M"


def test_the_model_tag_is_not_returned_as_a_document(tmp_path):
    path = tmp_path / "DEMO.npz"
    save_index(path, {"a": np.array([[1.0, 0.0]])}, model="vidore/colSmol-500M")

    assert list(load_index(path)) == ["a"]


def test_an_index_from_another_model_is_refused_rather_than_ranked(tmp_path, monkeypatch):
    path = tmp_path / "DEMO.npz"
    save_index(path, {"a": np.array([[1.0, 0.0]])}, model="vidore/colqwen2-v1.0")

    monkeypatch.setattr(colpali_index, "index_path", lambda course: path)
    monkeypatch.setattr(colpali_index, "MODEL_NAME", "vidore/colSmol-500M")
    colpali_index.cached_index.cache_clear()

    assert colpali_index.cached_index("DEMO") == ((), ()), (
        "querying one model's vectors with another's produces confident nonsense"
    )
    colpali_index.cached_index.cache_clear()


def test_an_index_from_the_configured_model_is_used(tmp_path, monkeypatch):
    path = tmp_path / "DEMO.npz"
    save_index(path, {"a": np.array([[1.0, 0.0]])}, model="vidore/colSmol-500M")

    monkeypatch.setattr(colpali_index, "index_path", lambda course: path)
    monkeypatch.setattr(colpali_index, "MODEL_NAME", "vidore/colSmol-500M")
    colpali_index.cached_index.cache_clear()

    keys, _ = colpali_index.cached_index("DEMO")
    assert keys == ("a",)
    colpali_index.cached_index.cache_clear()


def test_an_index_predating_the_tag_is_still_usable(tmp_path, monkeypatch):
    path = tmp_path / "DEMO.npz"
    np.savez_compressed(path, a=np.array([[1.0, 0.0]], dtype=np.float16))

    monkeypatch.setattr(colpali_index, "index_path", lambda course: path)
    colpali_index.cached_index.cache_clear()

    keys, _ = colpali_index.cached_index("DEMO")
    assert keys == ("a",), "an untagged index is old, not wrong"
    colpali_index.cached_index.cache_clear()
