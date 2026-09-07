from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatTurn] = []


@router.post("")
def chat(request: ChatRequest) -> dict:
    try:
        return chat_service.answer(
            request.message, [turn.model_dump() for turn in request.history]
        )
    except chat_service.VLLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
