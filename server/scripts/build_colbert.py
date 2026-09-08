"""Build the late-interaction index for a course.

    python scripts/build_colbert.py --class CPE393

Reads the chunks already in Neo4j, so it costs one GPU pass and no re-ingest.
Rerun after ingesting new material; the index is a cache, not a source.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.services.colbert_index import (  # noqa: E402
    MODEL_NAME,
    encode_documents,
    index_path,
    save_index,
)
from app.services.neo4j_client import get_driver  # noqa: E402

BATCH = 32


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a ColBERT index for one course.")
    parser.add_argument("--class", dest="course", required=True, help="Course code")
    args = parser.parse_args()

    with get_driver().session() as session:
        rows = [
            (record["id"], record["text"])
            for record in session.run(
                """
                MATCH (d:Document {course: $course})-[:HAS_CHUNK]->(c:Chunk)
                RETURN c.id AS id, c.text AS text
                ORDER BY c.id
                """,
                course=args.course,
            )
        ]

    if not rows:
        print(f"No chunks for {args.course}. Ingest it first.")
        return 1

    print(f"Encoding {len(rows)} chunks…")
    documents = {}
    for start in range(0, len(rows), BATCH):
        batch = rows[start : start + BATCH]
        for (chunk_id, _), vectors in zip(batch, encode_documents([text for _, text in batch])):
            documents[chunk_id] = vectors
        print(f"  {min(start + BATCH, len(rows))}/{len(rows)}")

    path = index_path(args.course)
    save_index(path, documents, model=MODEL_NAME)
    size = path.stat().st_size / 1e6
    tokens = sum(v.shape[0] for v in documents.values())
    print(f"Wrote {path.name}: {len(documents)} chunks, {tokens} token vectors, {size:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
