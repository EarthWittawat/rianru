"""The model pass: prerequisites the timeline cannot see, checked before storing."""

from app.services.path_refine import parse_requirements

KNOWN = {"tokenization", "tf-idf", "bag of words", "stemming"}


def test_valid_pairs_become_edges_with_their_reason():
    raw = """{"requirements": [
        {"concept": "tf-idf", "requires": "bag of words",
         "reason": "TF-IDF weights the counts a bag-of-words model produces."}
    ]}"""

    assert parse_requirements(raw, KNOWN) == [
        {
            "source": "tf-idf",
            "target": "bag of words",
            "origin": "model",
            "reason": "TF-IDF weights the counts a bag-of-words model produces.",
        }
    ]


def test_a_concept_the_course_does_not_contain_is_dropped():
    raw = """{"requirements": [
        {"concept": "tf-idf", "requires": "word2vec", "reason": "invented"}
    ]}"""

    assert parse_requirements(raw, KNOWN) == []


def test_a_concept_cannot_require_itself():
    raw = """{"requirements": [
        {"concept": "tf-idf", "requires": "tf-idf", "reason": "circular"}
    ]}"""

    assert parse_requirements(raw, KNOWN) == []


def test_an_edge_without_a_reason_is_dropped():
    raw = """{"requirements": [
        {"concept": "tf-idf", "requires": "tokenization"}
    ]}"""

    assert parse_requirements(raw, KNOWN) == []


def test_matching_ignores_case_and_returns_the_courses_own_spelling():
    raw = """{"requirements": [
        {"concept": "TF-IDF", "requires": "Tokenization", "reason": "counts need tokens"}
    ]}"""

    edges = parse_requirements(raw, KNOWN)

    assert edges[0]["source"] == "tf-idf"
    assert edges[0]["target"] == "tokenization"


def test_unparseable_output_yields_nothing_rather_than_raising():
    assert parse_requirements("the model felt chatty today", KNOWN) == []
