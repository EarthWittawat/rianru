import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.neo4j_client import get_driver

router = APIRouter(prefix="/highlights", tags=["highlights"])


class HighlightRequest(BaseModel):
    chunk_id: str
    selected_text: str = Field(min_length=1)
    explanation: str = ""


@router.post("")
def save_highlight(request: HighlightRequest) -> dict:
    highlight_id = str(uuid.uuid4())

    with get_driver().session() as session:
        record = session.run(
            """
            MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk {id: $chunk_id})
            CREATE (c)-[:HAS_HIGHLIGHT]->(h:Highlight {
                id: $id,
                selected_text: $selected_text,
                explanation: $explanation,
                page: c.page,
                created_at: datetime(),
                // Anchors so a re-ingest, which replaces every chunk, can
                // find this highlight again and re-attach it.
                document_id: d.id,
                chunk_index: c.index
            })
            RETURN h.id AS id, d.title AS document_title, d.id AS document_id
            """,
            chunk_id=request.chunk_id,
            id=highlight_id,
            selected_text=request.selected_text,
            explanation=request.explanation,
        ).single()

        if record is None:
            raise HTTPException(status_code=404, detail="Chunk not found")

        # Link the highlight to any known concept whose name appears in the
        # selection, so saved highlights land in the knowledge graph.
        session.run(
            """
            MATCH (h:Highlight {id: $id})
            MATCH (e:Entity)
            WHERE toLower($selected_text) CONTAINS toLower(e.name)
            MERGE (h)-[:MENTIONS]->(e)
            """,
            id=highlight_id,
            selected_text=request.selected_text,
        )

    return {
        "id": record["id"],
        "document_id": record["document_id"],
        "document_title": record["document_title"],
    }


@router.get("")
def list_highlights() -> list[dict]:
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:HAS_HIGHLIGHT]->(h:Highlight)
            RETURN h.id AS id, h.selected_text AS selected_text,
                   h.explanation AS explanation, h.page AS page,
                   c.id AS chunk_id, d.id AS document_id,
                   d.title AS document_title, d.topic AS topic
            ORDER BY h.created_at DESC
            """
        )
        return [record.data() for record in result]


@router.delete("/{highlight_id}")
def delete_highlight(highlight_id: str) -> dict:
    with get_driver().session() as session:
        summary = session.run(
            "MATCH (h:Highlight {id: $id}) DETACH DELETE h", id=highlight_id
        ).consume()

    if summary.counters.nodes_deleted == 0:
        raise HTTPException(status_code=404, detail="Highlight not found")
    return {"deleted": highlight_id}
