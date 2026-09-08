"""Retrieval over the page as an image.

Text retrieval only ever sees text. A slide whose meaning is a bar chart, a
table, or an annotated diagram is nearly invisible to it: the extracted text is
a handful of axis labels. ColPali embeds the rendered page instead, so "the
slide with the word-frequency chart" is findable by what it looks like.

The answer is a place, not a passage. The gateway serves a text model, so a
page image cannot be fed to the tutor — what this returns is a document and a
page number to open, which is what a student wants from a visual search anyway.
"""

import logging
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.config import settings
from app.services.multivector import index_model, load_index, rank, save_index

logger = logging.getLogger(__name__)

# Each checkpoint family needs its own model and processor classes, so the
# choice of checkpoint is not free-form: this is the set that is wired up.
MODEL_CLASSES = {
    "vidore/colSmol-256M": ("ColIdefics3", "ColIdefics3Processor"),
    "vidore/colSmol-500M": ("ColIdefics3", "ColIdefics3Processor"),
    "vidore/colqwen2-v0.1": ("ColQwen2", "ColQwen2Processor"),
    "vidore/colqwen2-v1.0": ("ColQwen2", "ColQwen2Processor"),
}

MODEL_NAME = settings.colpali_model
INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "colpali"

# 2x the PDF's own size: enough for slide text to survive rasterising, small
# enough that a lecture deck fits through the model without thrashing VRAM.
RENDER_SCALE = 2.0

KEY = re.compile(r"^(?P<document>.+)::page::(?P<page>\d+)$")


def index_path(course: str) -> Path:
    return INDEX_DIR / f"{course}.npz"


def page_key(document_id: str, page: int) -> str:
    return f"{document_id}::page::{page}"


def parse_key(key: str) -> tuple[str, int] | None:
    """Split a stored key back into the document and the page it points at."""
    match = KEY.match(key)
    if match is None:
        return None
    return match.group("document"), int(match.group("page"))


def render_pdf(path: Path, scale: float = RENDER_SCALE):
    """Every page of a PDF as an image, one at a time.

    A generator because a deck rendered eagerly is hundreds of megabytes of
    bitmap for no reason: each page is embedded and dropped.
    """
    import pypdfium2  # noqa: PLC0415 — native library, loaded only when indexing

    document = pypdfium2.PdfDocument(str(path))
    try:
        for number in range(len(document)):
            page = document[number]
            yield number + 1, page.render(scale=scale).to_pil()
    finally:
        document.close()


@lru_cache(maxsize=1)
def get_model():
    import colpali_engine.models as models  # noqa: PLC0415
    import torch  # noqa: PLC0415

    if MODEL_NAME not in MODEL_CLASSES:
        raise ValueError(
            f"Unsupported colpali_model {MODEL_NAME!r}. "
            f"Wired up: {', '.join(sorted(MODEL_CLASSES))}."
        )
    model_class, processor_class = (
        getattr(models, name) for name in MODEL_CLASSES[MODEL_NAME]
    )

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    logger.info("Loading %s on %s", MODEL_NAME, device)
    model = model_class.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16 if device.startswith("cuda") else torch.float32,
        device_map=device,
    ).eval()
    return model, processor_class.from_pretrained(MODEL_NAME)


def encode_pages(images: list) -> list[np.ndarray]:
    import torch  # noqa: PLC0415

    model, processor = get_model()
    with torch.no_grad():
        batch = processor.process_images(images).to(model.device)
        embeddings = model(**batch)
    return [vectors.to(torch.float32).cpu().numpy() for vectors in embeddings]


def encode_query(text: str) -> np.ndarray:
    import torch  # noqa: PLC0415

    model, processor = get_model()
    with torch.no_grad():
        batch = processor.process_queries([text]).to(model.device)
        embeddings = model(**batch)
    return embeddings[0].to(torch.float32).cpu().numpy()


@lru_cache(maxsize=4)
def cached_index(course: str) -> tuple[tuple[str, ...], tuple[np.ndarray, ...]]:
    path = index_path(course)
    built_by = index_model(path)
    if built_by is not None and built_by != MODEL_NAME:
        # Ranking one model's queries against another's pages produces confident
        # nonsense, which is worse than saying there is no index.
        logger.warning(
            "%s was built with %s but %s is configured; rebuild it.",
            path.name,
            built_by,
            MODEL_NAME,
        )
        return (), ()
    index = load_index(path)
    return tuple(index.keys()), tuple(index.values())


def search(query: str, course: str, top_k: int = 6) -> list[dict]:
    """Pages that look like the query, best first. Empty without an index."""
    keys, vectors = cached_index(course)
    if not keys:
        return []

    hits = []
    for key, score in rank(encode_query(query), dict(zip(keys, vectors)), top_k=top_k):
        parsed = parse_key(key)
        if parsed:
            document_id, page = parsed
            hits.append({"document_id": document_id, "page": page, "score": score})
    return hits


def has_index(course: str) -> bool:
    return index_path(course).exists()


__all__ = [
    "cached_index",
    "encode_pages",
    "encode_query",
    "has_index",
    "index_path",
    "page_key",
    "parse_key",
    "render_pdf",
    "save_index",
    "search",
]
