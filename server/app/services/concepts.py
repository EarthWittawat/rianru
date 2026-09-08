"""What a concept is, written from the chunks that teach it.

Explanations are generated on first request and cached on the node. Writing all
of them at ingest would be hundreds of model calls for concepts nobody opens,
and re-running on every ingest; writing them fresh every time would make the
page slow forever. This pays once, for what is actually read.
"""

import logging
from datetime import datetime, timezone

from app.prompts import CONCEPT_SYSTEM
from app.services.entity_extraction import load_json_object
from app.services.neo4j_client import get_driver
from app.services.vllm_client import chat

logger = logging.getLogger(__name__)

# Enough of the course's own words to ground an explanation, few enough to keep
# the call quick.
CONTEXT_CHUNKS = 5

CONCEPT_QUERY = """
MATCH (e:Entity {name: $name})
OPTIONAL MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e)
WITH e, d, c
ORDER BY d.position, c.index
WITH e, collect({document_id: d.id, document_title: d.title, topic: d.topic,
                 page: c.page, text: c.text, position: d.position})[..$limit] AS sources
OPTIONAL MATCH (e)-[r:REQUIRES]->(prerequisite:Entity)
RETURN e.name AS name, e.type AS type, e.summary AS summary, e.example AS example,
       sources,
       collect(DISTINCT {name: prerequisite.name, reason: r.reason,
                         origin: r.origin}) AS requires
"""


def get_concept(name: str) -> dict | None:
    with get_driver().session() as session:
        record = session.run(CONCEPT_QUERY, name=name, limit=CONTEXT_CHUNKS).single()

    if record is None:
        return None

    sources = [s for s in record["sources"] if s["document_id"]]
    requires = [r for r in record["requires"] if r["name"]]
    return {
        "name": record["name"],
        "type": record["type"],
        "summary": record["summary"],
        "example": record["example"],
        "requires": requires,
        "sources": [
            {
                "document_id": s["document_id"],
                "document_title": s["document_title"],
                "topic": s["topic"],
                "page": s["page"],
            }
            for s in sources
        ],
        "context": [s["text"] for s in sources],
    }


def explain_concept(concept: dict) -> dict | None:
    """Write the summary and example, from the course's own words. None if unusable."""
    if not concept["context"]:
        return None

    prerequisites = ", ".join(r["name"] for r in concept["requires"]) or "none recorded"
    raw = chat(
        [
            {"role": "system", "content": CONCEPT_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Concept: {concept['name']}\n"
                    f"Already understood: {prerequisites}\n\n"
                    "Course material:\n\n" + "\n\n---\n\n".join(concept["context"])
                ),
            },
        ],
        temperature=0.2,
    )

    payload = load_json_object(raw)
    if payload is None:
        logger.warning("Concept explanation was not JSON: %.120s", raw)
        return None

    summary = (payload.get("summary") or "").strip()
    example = (payload.get("example") or "").strip()
    if not summary:
        return None

    return {"summary": summary, "example": example}


def cache_explanation(name: str, summary: str, example: str) -> None:
    with get_driver().session() as session:
        session.run(
            """
            MATCH (e:Entity {name: $name})
            SET e.summary = $summary, e.example = $example, e.explained_at = $at
            """,
            name=name,
            summary=summary,
            example=example,
            at=datetime.now(timezone.utc).isoformat(),
        )


def as_response(concept: dict) -> dict:
    """The shape the API returns: everything except the raw context."""
    return {key: value for key, value in concept.items() if key != "context"}
