from fastapi import APIRouter

from app.services.learning_path import dependency_depth
from app.services.neo4j_client import get_driver

router = APIRouter(prefix="/path", tags=["path"])

STAGES_QUERY = """
MATCH (d:Document {course: $course})-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
WHERE d.position IS NOT NULL
WITH d.topic AS topic, min(d.position) AS position, e, count(DISTINCT c) AS mentions
RETURN topic, position,
       collect({name: e.name, type: e.type, mentions: mentions,
                explained: e.summary IS NOT NULL}) AS concepts
ORDER BY position
"""

EDGES_QUERY = """
MATCH (a:Entity)-[r:REQUIRES]->(b:Entity)
WHERE EXISTS {
    MATCH (:Document {course: $course})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(a)
}
RETURN a.name AS source, b.name AS target, r.reason AS reason, r.origin AS origin
"""


@router.get("")
def get_path(course: str = "CPE393", min_mentions: int = 2) -> dict:
    """The course as an ordered path: stages in teaching order, concepts by depth.

    Concepts mentioned once are usually extraction noise — a stray library name
    in one cell — and burying the path in them helps nobody, so the floor is a
    parameter rather than a hidden constant.
    """
    with get_driver().session() as session:
        stage_records = list(session.run(STAGES_QUERY, course=course))
        edges = [record.data() for record in session.run(EDGES_QUERY, course=course)]

    stages = []
    for record in stage_records:
        concepts = [c for c in record["concepts"] if c["mentions"] >= min_mentions]
        if not concepts:
            continue
        depths = dependency_depth([c["name"] for c in concepts], edges)
        for concept in concepts:
            concept["depth"] = depths.get(concept["name"], 0)
        concepts.sort(key=lambda c: (c["depth"], -c["mentions"], c["name"]))
        stages.append(
            {
                "topic": record["topic"],
                "position": record["position"],
                "concepts": concepts,
            }
        )

    names = {concept["name"] for stage in stages for concept in stage["concepts"]}
    return {
        "stages": stages,
        "edges": [e for e in edges if e["source"] in names and e["target"] in names],
    }
