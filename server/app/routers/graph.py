from fastapi import APIRouter

from app.services.neo4j_client import get_driver

router = APIRouter(prefix="/graph", tags=["graph"])

# Chunks are an implementation detail of retrieval — 500+ of them would drown
# the canvas — so the graph is projected over Documents, Entities and
# Highlights, with chunk hops collapsed into direct edges.
GRAPH_QUERY = """
MATCH (d:Document)
WHERE $topic IS NULL OR d.topic = $topic
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(:Chunk)-[:HAS_HIGHLIGHT]->(h:Highlight)
WITH collect(DISTINCT d) AS documents,
     collect(DISTINCT e) AS entities,
     collect(DISTINCT h) AS highlights
RETURN documents, entities, highlights
"""

COVERS_QUERY = """
MATCH (d:Document)-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(e:Entity)
WHERE $topic IS NULL OR d.topic = $topic
RETURN DISTINCT d.id AS source, e.name AS target, count(*) AS weight
"""

RELATES_QUERY = """
MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity)
WHERE $topic IS NULL OR EXISTS {
    MATCH (d:Document {topic: $topic})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(a)
}
RETURN DISTINCT a.name AS source, b.name AS target, r.type AS label
"""

HIGHLIGHT_QUERY = """
MATCH (d:Document)-[:HAS_CHUNK]->(:Chunk)-[:HAS_HIGHLIGHT]->(h:Highlight)
WHERE $topic IS NULL OR d.topic = $topic
OPTIONAL MATCH (h)-[:MENTIONS]->(e:Entity)
RETURN d.id AS document_id, h.id AS highlight_id, collect(e.name) AS entities
"""


@router.get("")
def get_graph(topic: str | None = None) -> dict:
    with get_driver().session() as session:
        record = session.run(GRAPH_QUERY, topic=topic).single()

        nodes = []
        for document in record["documents"]:
            nodes.append(
                {
                    "id": document["id"],
                    "label": document["title"],
                    "type": "Document",
                    "topic": document["topic"],
                }
            )
        for entity in record["entities"]:
            nodes.append(
                {
                    "id": entity["name"],
                    "label": entity["name"],
                    "type": "Entity",
                    "entity_type": entity.get("type"),
                }
            )
        for highlight in record["highlights"]:
            nodes.append(
                {
                    "id": highlight["id"],
                    "label": _truncate(highlight["selected_text"]),
                    "type": "Highlight",
                    "explanation": highlight["explanation"],
                }
            )

        node_ids = {n["id"] for n in nodes}
        edges = []

        for row in session.run(COVERS_QUERY, topic=topic):
            if row["source"] in node_ids and row["target"] in node_ids:
                edges.append(
                    {
                        "source": row["source"],
                        "target": row["target"],
                        "label": "covers",
                    }
                )

        for row in session.run(RELATES_QUERY, topic=topic):
            if row["source"] in node_ids and row["target"] in node_ids:
                edges.append(
                    {
                        "source": row["source"],
                        "target": row["target"],
                        "label": row["label"],
                    }
                )

        for row in session.run(HIGHLIGHT_QUERY, topic=topic):
            if row["highlight_id"] not in node_ids:
                continue
            if row["document_id"] in node_ids:
                edges.append(
                    {
                        "source": row["document_id"],
                        "target": row["highlight_id"],
                        "label": "highlighted",
                    }
                )
            for entity_name in row["entities"]:
                if entity_name in node_ids:
                    edges.append(
                        {
                            "source": row["highlight_id"],
                            "target": entity_name,
                            "label": "mentions",
                        }
                    )

    return {"nodes": nodes, "edges": edges}


@router.get("/topics")
def list_topics(course: str | None = None) -> list[str]:
    with get_driver().session() as session:
        return session.run(
            "MATCH (d:Document) WHERE $course IS NULL OR d.course = $course "
            "RETURN DISTINCT d.topic AS topic ORDER BY topic",
            course=course,
        ).value()


def _truncate(text: str, limit: int = 60) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else f"{text[:limit]}…"
