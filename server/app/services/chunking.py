from dataclasses import dataclass
from pathlib import Path

import nbformat
import pdfplumber

DEFAULT_MAX_CHARS = 1500
DEFAULT_OVERLAP_CHARS = 200


@dataclass(frozen=True)
class Chunk:
    text: str
    source_path: str
    page: int | None = None
    cell_index: int | None = None
    cell_type: str | None = None


def chunk_file(
    path: Path,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[Chunk]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _chunk_pdf(path, max_chars, overlap_chars)
    if suffix == ".ipynb":
        return _chunk_notebook(path, max_chars, overlap_chars)
    if suffix == ".md":
        return _chunk_markdown(path, max_chars, overlap_chars)
    raise ValueError(f"Unsupported file type for chunking: {path.suffix} ({path})")


def _chunk_pdf(path: Path, max_chars: int, overlap_chars: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for piece in _split(text, max_chars, overlap_chars):
                chunks.append(
                    Chunk(text=piece, source_path=str(path), page=page_number)
                )
    return chunks


def _chunk_notebook(path: Path, max_chars: int, overlap_chars: int) -> list[Chunk]:
    notebook = nbformat.read(path, as_version=4)
    chunks: list[Chunk] = []
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type not in ("markdown", "code"):
            continue
        for piece in _split(cell.source, max_chars, overlap_chars):
            chunks.append(
                Chunk(
                    text=piece,
                    source_path=str(path),
                    cell_index=index,
                    cell_type=cell.cell_type,
                )
            )
    return chunks


def _chunk_markdown(path: Path, max_chars: int, overlap_chars: int) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    return [
        Chunk(text=piece, source_path=str(path))
        for piece in _split(text, max_chars, overlap_chars)
    ]


def _split(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    step = max(1, max_chars - overlap_chars)
    pieces = []
    for start in range(0, len(text), step):
        piece = text[start : start + max_chars].strip()
        if piece:
            pieces.append(piece)
        if start + max_chars >= len(text):
            break
    return pieces
