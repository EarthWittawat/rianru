from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents import coach as coach_agent
from app.services import study_plan
from app.services.vllm_client import VLLMError

router = APIRouter(prefix="/coach", tags=["coach"])


class DoneRequest(BaseModel):
    done: bool


@router.post("/plan")
def generate_plan() -> dict:
    try:
        tasks = coach_agent.plan_study()
    except VLLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not tasks:
        raise HTTPException(
            status_code=502,
            detail="The coach did not return a usable plan. Try again.",
        )
    return study_plan.save_plan(tasks)


@router.get("/plan/latest")
def get_latest_plan() -> dict:
    plan = study_plan.latest_plan()
    if plan is None:
        raise HTTPException(status_code=404, detail="No plan generated yet")
    return plan


@router.patch("/tasks/{task_id}")
def set_done(task_id: str, request: DoneRequest) -> dict:
    if not study_plan.set_task_done(task_id, request.done):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": task_id, "done": request.done}
