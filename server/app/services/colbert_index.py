"""Late-interaction retrieval over the course material.

A dense embedding squeezes a whole chunk into one vector, which is why it
struggles with the exact terms a student searches for. ColBERT keeps a vector
per token and scores a document by how well its best token answers each query
token, so a rare term the chunk actually contains cannot be averaged away.

The corpus is a course, not the web: a few hundred chunks. Every document
vector fits in memory, so this scores all of them directly rather than
maintaining an approximate index. No PLAID, no clustering, nothing to rebuild
when it drifts.
"""

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.services.multivector import load_index, maxsim, rank, save_index

logger = logging.getLogger(__name__)

__all__ = [
    "cached_index",
    "encode_documents",
    "encode_query",
    "has_index",
    "index_path",
    "load_index",
    "maxsim",
    "rank",
    "save_index",
    "search",
]

MODEL_NAME = "lightonai/GTE-ModernColBERT-v1"
INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "colbert"


def index_path(course: str) -> Path:
    return INDEX_DIR / f"{course}.npz"


@lru_cache(maxsize=4)
def cached_index(course: str) -> tuple[tuple[str, ...], tuple[np.ndarray, ...]]:
    """Loaded once per course. Tuples because lru_cache needs a hashable return."""
    index = load_index(index_path(course))
    return tuple(index.keys()), tuple(index.values())


@lru_cache(maxsize=1)
def get_model():
    from pylate import models  # noqa: PLC0415 — several seconds and a GPU allocation

    import torch  # noqa: PLC0415

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Loading ColBERT on %s", device)
    return models.ColBERT(model_name_or_path=MODEL_NAME, device=device)


def encode_documents(texts: list[str]) -> list[np.ndarray]:
    encoded = get_model().encode(texts, is_query=False, show_progress_bar=False)
    return [np.asarray(vectors, dtype=np.float32) for vectors in encoded]


def encode_query(text: str) -> np.ndarray:
    encoded = get_model().encode([text], is_query=True, show_progress_bar=False)
    return np.asarray(encoded[0], dtype=np.float32)


def search(query: str, course: str, top_k: int = 6) -> list[tuple[str, float]]:
    """Chunk ids and scores, best first. Empty when the course has no index."""
    chunk_ids, vectors = cached_index(course)
    if not chunk_ids:
        return []
    return rank(encode_query(query), dict(zip(chunk_ids, vectors)), top_k=top_k)


def has_index(course: str) -> bool:
    return index_path(course).exists()
