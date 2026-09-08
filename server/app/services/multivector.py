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


def save_index(path: Path, documents: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # float16 halves the file for a difference well below the noise floor of
    # the ranking itself.
    np.savez_compressed(
        path,
        **{key: vectors.astype(np.float16) for key, vectors in documents.items()},
    )


def load_index(path: Path) -> dict[str, np.ndarray]:
    if not path.exists():
        return {}
    with np.load(path) as archive:
        return {name: archive[name].astype(np.float32) for name in archive.files}
