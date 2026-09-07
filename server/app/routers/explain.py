from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import explain as explain_service

router = APIRouter(prefix="/explain", tags=["explain"])


class ExplainRequest(BaseModel):
    document_id: str
    selected_text: str = Field(min_length=1)
    page: int | None = None


@router.post("")
def explain(request: ExplainRequest) -> dict:
    try:
        result = explain_service.explain_selection(
            request.document_id, request.selected_text, request.page
        )
    except explain_service.VLLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Document or chunk not found")
    return result
