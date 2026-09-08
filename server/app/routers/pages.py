from fastapi import APIRouter, HTTPException, Query

from app.services import colpali_index
from app.services.neo4j_client import get_driver

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("/search")
def search_pages(
    q: str = Query(min_length=2),
    course: str | None = None,
    top_k: int = 8,
) -> dict:
    """Find a page by what it looks like, not only by the words extracted from it.

    Returns places to open rather than passages to read: the gateway serves a
    text model, so a page image has nowhere else to go.
    """
    if not course:
        raise HTTPException(status_code=400, detail="A course is required")
    if not colpali_index.has_index(course):
        return {"indexed": False, "hits": []}

    hits = colpali_index.search(q, course, top_k=top_k)
    titles = _document_titles([hit["document_id"] for hit in hits])

    return {
        "indexed": True,
        "hits": [
            {
                **hit,
                "document_title": titles.get(hit["document_id"], hit["document_id"]),
            }
            for hit in hits
            if hit["document_id"] in titles
        ],
    }


def _document_titles(document_ids: list[str]) -> dict[str, str]:
    if not document_ids:
        return {}
    with get_driver().session() as session:
        result = session.run(
            "MATCH (d:Document) WHERE d.id IN $ids RETURN d.id AS id, d.title AS title",
            ids=document_ids,
        )
        return {record["id"]: record["title"] for record in result}
