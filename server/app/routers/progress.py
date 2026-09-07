from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from app.services import progress
from app.services.neo4j_client import get_driver

router = APIRouter(prefix="/progress", tags=["progress"])


class AttemptRequest(BaseModel):
    question_id: str
    chosen_answer: str | None = None
    self_grade: bool | None = None

    @model_validator(mode="after")
    def require_one_grading_signal(self):
        if self.chosen_answer is None and self.self_grade is None:
            raise ValueError("provide either chosen_answer or self_grade")
        return self


@router.post("/attempts")
def record_attempt(request: AttemptRequest) -> dict:
    question = _load_question(request.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    # Correctness is decided here, never taken from the client — the coach
    # reasons over this history, so a stray frontend bug must not poison it.
    if request.chosen_answer is not None:
        is_correct = request.chosen_answer.strip() == (question["answer"] or "").strip()
        graded_by = "auto"
    else:
        is_correct = bool(request.self_grade)
        graded_by = "self"

    progress.record_attempt(
        question_id=question["id"],
        topic=question["topic"],
        question_format=question["format"],
        chosen_answer=request.chosen_answer,
        is_correct=is_correct,
        graded_by=graded_by,
    )

    return {
        "is_correct": is_correct,
        "correct_answer": question["answer"],
        "graded_by": graded_by,
    }


@router.get("/topics")
def topics() -> list[dict]:
    return progress.topic_stats()


@router.get("/weak")
def weak(limit: int = 5, min_attempts: int = progress.MIN_ATTEMPTS_FOR_WEAKNESS):
    return progress.weak_topics(limit=limit, min_attempts=min_attempts)


def _load_question(question_id: str) -> dict | None:
    with get_driver().session() as session:
        record = session.run(
            """
            MATCH (q:QuizQuestion {id: $id})
            RETURN q.id AS id, q.topic AS topic, q.format AS format,
                   q.answer AS answer
            """,
            id=question_id,
        ).single()
    return record.data() if record else None
