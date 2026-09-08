from fastapi import APIRouter, HTTPException

from app.services import concepts as service
from app.services.vllm_client import VLLMError

router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.get("/{name:path}")
def get_concept(name: str) -> dict:
    concept = service.get_concept(name)
    if concept is None:
        raise HTTPException(status_code=404, detail="No such concept")

    if not concept["summary"]:
        try:
            written = service.explain_concept(concept)
        except VLLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        if written is None:
            raise HTTPException(
                status_code=502,
                detail="The tutor did not return a usable explanation. Try again.",
            )
        service.cache_explanation(concept["name"], written["summary"], written["example"])
        concept.update(written)

    return service.as_response(concept)
