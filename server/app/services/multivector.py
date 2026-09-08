"""Shared machinery for late-interaction retrieval.

Both retrievers — ColBERT over text, ColPali over page images — produce a
matrix of vectors per item and score with the same maximum-similarity rule, so
the scoring and the on-disk format live here once.
"""

from pathlib import Path

import numpy as np


def maxsim(query: np.ndarray, document: np.ndarray) -> float:
    """Late interaction: each query vector takes its best match, and those sum.

    The maximum rather than the mean is the whole point. An item that answers
    one part of the query perfectly and ignores the rest should not be dragged
    down by its own length.
    """
    if query.size == 0 or document.size == 0:
        return 0.0
    return float(np.max(query @ document.T, axis=1).sum())


def rank(
    query: np.ndarray, documents: dict[str, np.ndarray], top_k: int = 6
) -> list[tuple[str, float]]:
    scored = ((key, maxsim(query, vectors)) for key, vectors in documents.items())
    return sorted(scored, key=lambda pair: pair[1], reverse=True)[:top_k]


# Vectors from two different models share no space at all, so an index built by
# one and queried by another returns confident nonsense. The producing model is
# stored with the vectors so that mismatch can be detected rather than ranked.
MODEL_KEY = "__model__"


def save_index(path: Path, documents: dict[str, np.ndarray], model: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # float16 halves the file for a difference well below the noise floor of
    # the ranking itself.
    payload = {key: vectors.astype(np.float16) for key, vectors in documents.items()}
    payload[MODEL_KEY] = np.array(model)
    np.savez_compressed(path, **payload)


def load_index(path: Path) -> dict[str, np.ndarray]:
    if not path.exists():
        return {}
    with np.load(path) as archive:
        return {
            name: archive[name].astype(np.float32)
            for name in archive.files
            if name != MODEL_KEY
        }


def index_model(path: Path) -> str | None:
    """The model an index was built with, or None for one written before this."""
    if not path.exists():
        return None
    with np.load(path) as archive:
        if MODEL_KEY not in archive.files:
            return None
        # An empty tag carries no more information than a missing one.
        return str(archive[MODEL_KEY]) or None
