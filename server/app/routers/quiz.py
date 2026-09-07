from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import quiz as quiz_service

router = APIRouter(prefix="/quiz", tags=["quiz"])


class GenerateRequest(BaseModel):
    topic: str
    count: int = Field(default=6, ge=1, le=12)


@router.post("/generate")
def generate(request: GenerateRequest) -> dict:
    if not quiz_service.topic_excerpts(request.topic, limit=1):
        raise HTTPException(status_code=404, detail="No material for that topic")

    try:
        questions = quiz_service.generate(request.topic, request.count)
    except (quiz_service.VLLMError, quiz_service.QuizGenerationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"topic": request.topic, "questions": questions}


@router.get("")
def list_questions(topic: str | None = None) -> dict:
    return {"topic": topic, "questions": quiz_service.stored_questions(topic)}
