"""Tools the study-coach agents call.

Every tool is a thin wrapper over a service that already exists. They return
JSON strings because the model reads them as text, and each is callable
directly in tests without a model.
"""

import json

from langchain.tools import tool

from app.services import progress
from app.services.graph_store import similarity_search
from app.services.neo4j_client import get_driver


@tool
def get_weak_topics(limit: int = 5) -> str:
    """Topics the student answers worst, weakest first, with accuracy and attempt counts.

    Only counts topics with enough attempts to be meaningful.
    """
    return json.dumps(progress.weak_topics(limit=limit))


@tool
def get_topic_stats() -> str:
    """Every topic the student has attempted, with accuracy and attempt counts."""
    return json.dumps(progress.topic_stats())


@tool
def get_recent_attempts(topic: str | None = None, limit: int = 10) -> str:
    """The student's most recent quiz attempts, optionally for one topic."""
    return json.dumps(progress.recent_attempts(topic=topic, limit=limit))


@tool
def search_course_material(query: str, limit: int = 5) -> str:
    """Search the course material for passages about a subject.

    Returns matching excerpts with their document title, topic and page number.
    """
    hits = similarity_search(query, top_k=limit)
    return json.dumps(
        [
            {
                "document_id": hit["document_id"],
                "document_title": hit["document_title"],
                "topic": hit["topic"],
                "page": hit["page"],
                "excerpt": hit["text"][:400],
            }
            for hit in hits
        ]
    )


@tool
def list_topic_documents(topic: str) -> str:
    """List the documents that belong to a course topic."""
    with get_driver().session() as session:
        rows = session.run(
            """
            MATCH (d:Document {topic: $topic})
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            RETURN d.id AS document_id, d.title AS title,
                   d.activity_type AS activity_type, count(c) AS chunks
            ORDER BY d.title
            """,
            topic=topic,
        )
        return json.dumps([row.data() for row in rows])


@tool
def list_topics() -> str:
    """Every topic in the course, whether or not the student has studied it."""
    with get_driver().session() as session:
        return json.dumps(
            session.run(
                "MATCH (d:Document) RETURN DISTINCT d.topic AS topic ORDER BY topic"
            ).value()
        )


PROGRESS_TOOLS = [get_weak_topics, get_topic_stats, get_recent_attempts]
MATERIAL_TOOLS = [search_course_material, list_topic_documents, list_topics]
