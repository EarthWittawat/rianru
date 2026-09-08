"""Write the course's teaching order onto its documents.

Run after ingest, and again whenever the manifest's ordering changes:

    python scripts/set_positions.py --class CPE393

This does not touch chunks or entities. Re-ingesting would replace both, which
costs a full extraction pass, and the ordering is manifest data rather than
anything read out of the files.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.services.graph_store import (  # noqa: E402
    clear_document_positions,
    concept_frequency,
    concept_positions,
    document_concepts,
    set_document_positions,
)
from app.services.learning_path import lecture_positions, place_activity  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Position documents on the learning path.")
    parser.add_argument("--class", dest="course", required=True, help="Course code")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    course = _find_course(manifest, args.course)
    if course is None:
        print(f"No class with code {args.course} in manifest.json")
        return 1

    spine = lecture_positions(course)
    clear_document_positions(args.course)
    set_document_positions(spine)
    print(f"{len(spine)} lecture files placed on the spine")

    # Labs sit where their material sits: with the lectures whose concepts they
    # practise. Half a step later, so a lab never precedes what it builds on.
    # The median, not the maximum: one stray mention of a later concept should
    # not drag a regex lab to the end of the course.
    placed = concept_positions(args.course, document_ids=list(spine))

    # An activity is one unit of work: its description, notebook and data files
    # are placed together, from their pooled concepts. Placing each file alone
    # scatters one lab across the course, because a notebook's imports mention
    # concepts the lecture it practises never covers.
    by_activity: dict[str, list[str]] = {}
    files_of: dict[str, list[str]] = {}
    for doc_id, concepts in document_concepts(args.course).items():
        if doc_id in spine:
            continue
        activity = doc_id.rsplit("::", 1)[0]
        by_activity.setdefault(activity, []).extend(concepts)
        files_of.setdefault(activity, []).append(doc_id)

    frequency = concept_frequency(args.course, document_ids=list(spine))
    followers = {}
    for activity, concepts in by_activity.items():
        position = place_activity(concepts, placed, frequency)
        if position is None:
            continue
        for doc_id in files_of[activity]:
            followers[doc_id] = position

    set_document_positions(followers)
    print(f"{len(followers)} practice files placed against the lectures they follow")

    unplaced = len(document_concepts(args.course)) - len(spine) - len(followers)
    if unplaced:
        print(f"{unplaced} documents share no concept with any lecture and stay unplaced")
    return 0


def _find_course(manifest: dict, code: str) -> dict | None:
    for course in manifest["classes"].values():
        if course["code"].upper() == code.upper():
            return course
    return None


if __name__ == "__main__":
    raise SystemExit(main())
