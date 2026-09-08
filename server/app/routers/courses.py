from fastapi import APIRouter

from app.services.graph_store import list_courses

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
def get_courses() -> list[dict]:
    """Every ingested course. The client picks one and asks for it by name."""
    return list_courses()
