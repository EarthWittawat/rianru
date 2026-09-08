"""Turning the manifest's own ordering into document positions."""

from app.services.learning_path import lecture_positions

COURSE = {
    "code": "DEMO",
    "learning_activities": {
        "a1": {"title": "First", "files": ["L1.pdf", "notes.md"]},
        "a2": {"title": "Second", "files": ["L2.pdf"]},
        "a3": {"title": "Third", "files": ["L3.pdf"]},
    },
    "assessment_activities": {
        "b1": {"title": "Lab 1", "files": ["lab1.ipynb"]},
    },
}


def test_lectures_are_numbered_in_manifest_order():
    positions = lecture_positions(COURSE)

    assert positions["DEMO::a1::L1.pdf"] == 0
    assert positions["DEMO::a2::L2.pdf"] == 1
    assert positions["DEMO::a3::L3.pdf"] == 2


def test_every_file_in_one_activity_shares_that_activity_position():
    positions = lecture_positions(COURSE)

    assert positions["DEMO::a1::notes.md"] == 0


def test_assessments_are_not_placed_on_the_lecture_spine():
    positions = lecture_positions(COURSE)

    assert not any(key.startswith("DEMO::b1") for key in positions), (
        "labs are practice for a lecture, not a step in the sequence; "
        "they are placed later from the concepts they share"
    )


def test_unsupported_files_are_skipped():
    course = {
        "code": "DEMO",
        "learning_activities": {"a1": {"title": "First", "files": ["slides.pptx"]}},
    }

    assert lecture_positions(course) == {}


from app.services.learning_path import place_activity  # noqa: E402


def test_a_lab_is_placed_by_its_distinctive_concepts_not_its_common_ones():
    # "pandas" is mentioned by every lecture; "backreference" only by lecture 1.
    positions = {"pandas": 0, "dataframe": 0, "backreference": 1, "regex": 1}
    frequency = {"pandas": 5, "dataframe": 5, "backreference": 1, "regex": 1}
    concepts = ["pandas", "dataframe", "dataframe", "backreference", "regex"]

    assert place_activity(concepts, positions, frequency) == 1.5


def test_placement_falls_back_to_none_without_a_single_known_concept():
    assert place_activity(["unknown"], {}, {}) is None


def test_ties_go_to_the_earlier_lecture():
    positions = {"a": 1, "b": 3}
    frequency = {"a": 1, "b": 1}

    assert place_activity(["a", "b"], positions, frequency) == 1.5
