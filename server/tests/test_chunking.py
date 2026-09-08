from pathlib import Path

import pytest

from app.services.chunking import chunk_file

COURSE_ROOT = Path(__file__).resolve().parents[2] / "CPE393 - Text Analytics"
LECTURE_PDF = COURSE_ROOT / "Learning Activity" / "01 - Introduction to Text Analytics" / "L1 - Intro.pdf"
LAB_NOTEBOOK = COURSE_ROOT / "Assessment Activity" / "Lab 1 - RegEx" / "Lab1_regex.ipynb"

# These read the real course files, which are not in the repository.
pytestmark = pytest.mark.skipif(
    not (LECTURE_PDF.exists() and LAB_NOTEBOOK.exists()),
    reason="course material is not present; these tests parse the real files",
)


def test_pdf_chunks_carry_page_numbers():
    chunks = chunk_file(LECTURE_PDF)

    assert chunks, "expected non-empty chunks from the lecture PDF"
    assert all(c.text.strip() for c in chunks)
    assert all(c.page is not None for c in chunks)
    assert min(c.page for c in chunks) == 1
    assert all(c.cell_index is None for c in chunks)


def test_notebook_chunks_carry_cell_indexes():
    chunks = chunk_file(LAB_NOTEBOOK)

    assert chunks, "expected non-empty chunks from the lab notebook"
    assert all(c.cell_index is not None for c in chunks)
    assert all(c.page is None for c in chunks)
    assert {c.cell_type for c in chunks} <= {"markdown", "code"}


def test_chunk_size_is_configurable():
    small = chunk_file(LECTURE_PDF, max_chars=400, overlap_chars=0)
    large = chunk_file(LECTURE_PDF, max_chars=2000, overlap_chars=0)

    assert len(small) > len(large)
    assert all(len(c.text) <= 400 for c in small)


def test_chunks_overlap_when_requested():
    no_overlap = chunk_file(LECTURE_PDF, max_chars=500, overlap_chars=0)
    with_overlap = chunk_file(LECTURE_PDF, max_chars=500, overlap_chars=100)

    assert len(with_overlap) >= len(no_overlap)


def test_unsupported_extension_raises():
    with pytest.raises(ValueError):
        chunk_file(COURSE_ROOT / "Assessment Activity" / "Lab 1 - RegEx" / "books.txt")
