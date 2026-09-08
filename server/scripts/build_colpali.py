"""Build the page-image index for a course.

    python scripts/build_colpali.py --class CPE393

Renders every ingested PDF page and embeds it with ColQwen2, so a slide whose
meaning is a chart or a table becomes findable. Needs a GPU in practice: on CPU
this is hours rather than minutes.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.services.colpali_index import (  # noqa: E402
    MODEL_NAME,
    encode_pages,
    index_path,
    page_key,
    render_pdf,
)
from app.services.multivector import save_index  # noqa: E402
from app.services.neo4j_client import get_driver  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]

# One page at a time: a 620-vector page peaks near 9 GB of VRAM through the
# vision tower, and a stalled index is worse than a slow one.
BATCH = 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a ColPali page index.")
    parser.add_argument("--class", dest="course", required=True, help="Course code")
    args = parser.parse_args()

    with get_driver().session() as session:
        documents = [
            (record["id"], record["file_path"])
            for record in session.run(
                """
                MATCH (d:Document {course: $course})
                WHERE d.file_path ENDS WITH '.pdf'
                RETURN d.id AS id, d.file_path AS file_path
                ORDER BY d.position, d.id
                """,
                course=args.course,
            )
        ]

    if not documents:
        print(f"No PDFs ingested for {args.course}.")
        return 1

    index: dict = {}
    for document_id, file_path in documents:
        path = REPO_ROOT / file_path
        if not path.exists():
            print(f"  SKIP  {path.name} — file not found")
            continue

        pages = 0
        buffer: list = []
        keys: list[str] = []
        for number, image in render_pdf(path):
            buffer.append(image)
            keys.append(page_key(document_id, number))
            if len(buffer) >= BATCH:
                for key, vectors in zip(keys, encode_pages(buffer)):
                    index[key] = vectors
                pages += len(buffer)
                buffer, keys = [], []
        if buffer:
            for key, vectors in zip(keys, encode_pages(buffer)):
                index[key] = vectors
            pages += len(buffer)

        print(f"  OK    {path.name} — {pages} pages")

    path = index_path(args.course)
    save_index(path, index, model=MODEL_NAME)
    size = path.stat().st_size / 1e6
    print(f"\nWrote {path.name}: {len(index)} pages, {size:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
