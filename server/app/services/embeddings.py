from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = _model().encode(texts, normalize_embeddings=True)
    return [[float(x) for x in vector] for vector in vectors]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
