"""The course's own teaching order, read out of the manifest.

The syllabus is a designed sequence: lecture 1 is taught before lecture 6
because someone decided it should be. That ordering is recorded here rather
than inferred, and it is the backbone every prerequisite edge is checked
against.
"""

SUPPORTED = {".pdf", ".ipynb", ".md"}


def lecture_positions(course: dict) -> dict[str, int]:
    """Document id to its position on the lecture spine.

    Only learning activities are placed. Labs and quizzes are practice for a
    lecture rather than a step of their own, so they take their position from
    the concepts they share with the spine.
    """
    positions: dict[str, int] = {}
    code = course["code"]

    for index, (activity_id, activity) in enumerate(
        (course.get("learning_activities") or {}).items()
    ):
        for file_name in activity.get("files") or []:
            if not any(file_name.lower().endswith(suffix) for suffix in SUPPORTED):
                continue
            positions[f"{code}::{activity_id}::{file_name}"] = index

    return positions


def place_activity(
    concepts: list[str],
    positions: dict[str, float],
    frequency: dict[str, int],
) -> float | None:
    """Where a lab or quiz sits relative to the lecture spine.

    Scored by the concepts it shares with lectures, weighted by how rare each
    concept is across the spine. A notebook mentions pandas and dataframes
    because it is a notebook; it mentions backreferences because it is the
    regex lab. Counting mentions puts every lab on whichever lecture introduced
    the plumbing, so each concept is weighted 1/lectures-that-mention-it and the
    distinctive ones decide.

    Returns a position half a step after the winning lecture, so practice never
    precedes the material it practises. None when nothing is shared.
    """
    scores: dict[float, float] = {}
    for concept in concepts:
        position = positions.get(concept)
        if position is None:
            continue
        weight = 1 / max(frequency.get(concept, 1), 1)
        scores[position] = scores.get(position, 0.0) + weight

    if not scores:
        return None

    best = max(scores.values())
    return min(position for position, score in scores.items() if score == best) + 0.5
