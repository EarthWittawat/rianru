"""Turning related concepts into an ordered prerequisite, using the spine."""

from app.services.learning_path import timeline_requirements

POSITIONS = {"regex": 1.0, "tokenization": 4.0, "tf-idf": 5.0, "orphan": 5.0}


def test_the_later_concept_requires_the_earlier_one():
    edges = timeline_requirements([("regex", "tokenization")], POSITIONS)

    assert edges == [
        {
            "source": "tokenization",
            "target": "regex",
            "origin": "timeline",
            "reason": "regex is taught before tokenization in the course.",
        }
    ]


def test_direction_does_not_depend_on_the_order_of_the_pair():
    assert timeline_requirements([("tokenization", "regex")], POSITIONS) == (
        timeline_requirements([("regex", "tokenization")], POSITIONS)
    )


def test_concepts_taught_at_the_same_point_have_no_prerequisite():
    assert timeline_requirements([("tf-idf", "orphan")], POSITIONS) == []


def test_a_concept_without_a_position_is_skipped():
    assert timeline_requirements([("regex", "unplaced")], POSITIONS) == []


def test_pairs_are_deduplicated():
    pairs = [("regex", "tf-idf"), ("tf-idf", "regex"), ("regex", "tf-idf")]

    assert len(timeline_requirements(pairs, POSITIONS)) == 1
