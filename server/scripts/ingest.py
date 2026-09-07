"""Ingest course material listed in manifest.json into Neo4j.

Run manually from the server/ directory:
    python scripts/ingest.py --class CPE393
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.services.chunking import chunk_file  # noqa: E402
from app.services.entity_extraction import extract_graph_from_text  # noqa: E402
from app.services.graph_store import (  # noqa: E402
    ensure_schema,
    write_document,
    write_entities,
)
from app.services.neo4j_client import get_driver  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "manifest.json"
SUPPORTED = {".pdf", ".ipynb", ".md"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest course material into Neo4j.")
    parser.add_argument("--class", dest="course", required=True, help="Course code, e.g. CPE393")
    parser.add_argument("--skip-entities", action="store_true", help="Chunk and embed only")
    # The gateway caps parallel requests per key at 3; more just triggers 429s.
    parser.add_argument("--workers", type=int, default=3, help="Parallel entity-extraction calls")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    course = _find_course(manifest, args.course)
    if course is None:
        print(f"No class with code {args.course} in manifest.json")
        return 1

    ensure_schema()
    course_folder = REPO_ROOT / course["folder"]

    documents = list(_documents(course, course_folder))
    print(f"{course['code']} — {len(documents)} files to ingest from {course['folder']}\n")

    total_chunks = 0
    total_entities = 0
    skipped: list[tuple[str, str]] = []

    for doc in documents:
        path = doc["path"]
        if not path.exists():
            skipped.append((path.name, "file not found"))
            print(f"  SKIP  {path.name} — file not found")
            continue

        try:
            chunks = chunk_file(path)
        except Exception as exc:
            skipped.append((path.name, str(exc)))
            print(f"  SKIP  {path.name} — {exc}")
            continue

        if not chunks:
            skipped.append((path.name, "no extractable text"))
            print(f"  SKIP  {path.name} — no extractable text")
            continue

        write_document(
            doc_id=doc["doc_id"],
            title=doc["title"],
            course=course["code"],
            topic=doc["topic"],
            activity_type=doc["activity_type"],
            file_path=str(path.relative_to(REPO_ROOT)),
            chunks=chunks,
        )
        total_chunks += len(chunks)
        print(f"  OK    {path.name} — {len(chunks)} chunks", end="", flush=True)

        if args.skip_entities:
            print()
            continue

        entity_count = _extract_entities(doc["doc_id"], chunks, args.workers)
        total_entities += entity_count
        print(f", {entity_count} entity mentions")

    print("\n" + "-" * 60)
    print(f"Documents ingested : {len(documents) - len(skipped)}")
    print(f"Chunks created     : {total_chunks}")
    print(f"Entity mentions    : {total_entities}")
    print(f"Skipped            : {len(skipped)}")
    for name, reason in skipped:
        print(f"  - {name}: {reason}")

    _print_graph_totals(course["code"])
    return 0


def _extract_entities(doc_id: str, chunks, workers: int) -> int:
    def work(index_chunk):
        index, chunk = index_chunk
        entities, relations = extract_graph_from_text(chunk.text)
        return f"{doc_id}::{index}", entities, relations

    written = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for chunk_id, entities, relations in pool.map(work, enumerate(chunks)):
            if entities:
                write_entities(chunk_id, entities, relations)
                written += len(entities)
    return written


def _find_course(manifest: dict, code: str) -> dict | None:
    for course in manifest["classes"].values():
        if course["code"].upper() == code.upper():
            return course
    return None


def _documents(course: dict, course_folder: Path):
    groups = [
        ("assessment", course.get("assessment_activities", {})),
        ("material", course.get("learning_activities", {})),
        ("other", course.get("other_files", {})),
    ]
    for group_type, activities in groups:
        for activity_id, activity in activities.items():
            for file_name in activity["files"]:
                if Path(file_name).suffix.lower() not in SUPPORTED:
                    continue
                yield {
                    "doc_id": f"{course['code']}::{activity_id}::{file_name}",
                    "title": f"{activity['title']} — {file_name}",
                    "topic": activity["title"],
                    "activity_type": activity.get("type", group_type),
                    "path": course_folder / activity["folder"] / file_name,
                }


def _print_graph_totals(course_code: str) -> None:
    with get_driver().session() as session:
        record = session.run(
            """
            MATCH (d:Document {course: $course})
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
            RETURN count(DISTINCT d) AS documents,
                   count(DISTINCT c) AS chunks,
                   count(DISTINCT e) AS entities
            """,
            course=course_code,
        ).single()
    print("-" * 60)
    print(
        f"In Neo4j now: {record['documents']} documents, "
        f"{record['chunks']} chunks, {record['entities']} distinct entities"
    )


if __name__ == "__main__":
    raise SystemExit(main())
