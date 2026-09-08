"""Build the learning path's prerequisite edges.

    python scripts/build_path.py --class CPE393              # timeline only
    python scripts/build_path.py --class CPE393 --refine     # plus the model pass

Two origins, kept separate so either can be rebuilt alone:

- `timeline`: two concepts the material already connects, taught at different
  points, ordered by which comes first. Derived, never guessed.
- `model`: prerequisites the timeline cannot see, because both concepts appear
  in the same lecture or in none. One call per topic, and every edge it returns
  is checked against concepts that actually exist.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.services.graph_store import (  # noqa: E402
    clear_requirements,
    concept_positions,
    related_concept_pairs,
    write_requirements,
)
from app.services.learning_path import timeline_requirements  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build learning-path prerequisites.")
    parser.add_argument("--class", dest="course", required=True, help="Course code")
    parser.add_argument(
        "--refine",
        action="store_true",
        help="Ask the model for prerequisites the timeline cannot see",
    )
    args = parser.parse_args()

    positions = concept_positions(args.course)
    if not positions:
        print("No positioned documents. Run scripts/set_positions.py first.")
        return 1

    pairs = related_concept_pairs(args.course)
    edges = timeline_requirements(pairs, positions)

    clear_requirements(origin="timeline")
    written = write_requirements(edges)
    print(f"{len(pairs)} related pairs → {len(edges)} timeline prerequisites ({written} new)")

    if args.refine:
        from app.services.path_refine import refine_course  # noqa: PLC0415

        added = refine_course(args.course)
        print(f"{added} prerequisites added by the model")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
