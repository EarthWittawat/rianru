from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.neo4j_client import get_driver

router = APIRouter(prefix="/documents", tags=["documents"])

REPO_ROOT = Path(__file__).resolve().parents[3]


@router.get("")
def list_documents(course: str = "CPE393") -> list[dict]:
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (d:Document {course: $course})
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            RETURN d.id AS id, d.title AS title, d.topic AS topic,
                   d.course AS course, d.activity_type AS activity_type,
                   d.file_path AS file_path, count(c) AS chunk_count
            ORDER BY d.topic, d.title
            """,
            course=course,
        )
        return [_as_summary(record.data()) for record in result]


@router.get("/{document_id}")
def get_document(document_id: str) -> dict:
    with get_driver().session() as session:
        record = session.run(
            """
            MATCH (d:Document {id: $id})
            RETURN d.id AS id, d.title AS title, d.topic AS topic,
                   d.course AS course, d.activity_type AS activity_type,
                   d.file_path AS file_path
            """,
            id=document_id,
        ).single()
        if record is None:
            raise HTTPException(status_code=404, detail="Document not found")

        chunks = session.run(
            """
            MATCH (:Document {id: $id})-[:HAS_CHUNK]->(c:Chunk)
            RETURN c.id AS id, c.text AS text, c.page AS page,
                   c.cell_index AS cell_index, c.index AS index
            ORDER BY c.index
            """,
            id=document_id,
        )
        detail = _as_summary(record.data())
        detail["chunks"] = [chunk.data() for chunk in chunks]
        return detail


@router.get("/{document_id}/file")
def get_document_file(document_id: str):
    path = _resolve_path(document_id)
    media_type = "application/pdf" if path.suffix.lower() == ".pdf" else "text/plain"
    return FileResponse(path, media_type=media_type, filename=path.name)


def _resolve_path(document_id: str) -> Path:
    with get_driver().session() as session:
        record = session.run(
            "MATCH (d:Document {id: $id}) RETURN d.file_path AS file_path",
            id=document_id,
        ).single()

    if record is None:
        raise HTTPException(status_code=404, detail="Document not found")

    path = (REPO_ROOT / record["file_path"]).resolve()
    if not path.is_relative_to(REPO_ROOT) or not path.exists():
        raise HTTPException(status_code=404, detail="Source file not available")
    return path


def _as_summary(data: dict) -> dict:
    data["file_type"] = Path(data["file_path"]).suffix.lstrip(".").lower()
    return data
