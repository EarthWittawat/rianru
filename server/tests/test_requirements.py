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


from app.services.learning_path import dependency_depth  # noqa: E402


def test_a_concept_with_no_prerequisites_sits_at_depth_zero():
    assert dependency_depth(["a"], []) == {"a": 0}


def test_depth_counts_the_longest_chain_of_prerequisites():
    edges = [
        {"source": "b", "target": "a"},
        {"source": "c", "target": "b"},
    ]

    assert dependency_depth(["a", "b", "c"], edges) == {"a": 0, "b": 1, "c": 2}


def test_a_cycle_does_not_hang_or_raise():
    edges = [
        {"source": "a", "target": "b"},
        {"source": "b", "target": "a"},
    ]

    depths = dependency_depth(["a", "b"], edges)

    assert set(depths) == {"a", "b"}


def test_edges_pointing_outside_the_given_concepts_are_ignored():
    edges = [{"source": "a", "target": "elsewhere"}]

    assert dependency_depth(["a"], edges) == {"a": 0}
