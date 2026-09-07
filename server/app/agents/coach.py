import logging

from langchain.agents import create_agent

from app.agents.llm import get_llm
from app.agents.specialists import SUBAGENT_TOOLS
from app.prompts import STUDY_COACH_SYSTEM
from app.services.entity_extraction import load_json_object

logger = logging.getLogger(__name__)

DEFAULT_REQUEST = (
    "Plan what I should study next. Check my quiz results first, then find "
    "where the weak topics are covered in my material."
)


def plan_study(request: str = DEFAULT_REQUEST) -> list[dict]:
    """Run the coach and return concrete study tasks.

    The model's JSON is parsed rather than requested via response_format:
    structured output is silently skipped when reasoning content is present
    unless the server enables it, and this gateway does not.
    """
    coach = create_agent(
        model=get_llm(max_tokens=6144),
        tools=SUBAGENT_TOOLS,
        system_prompt=STUDY_COACH_SYSTEM,
    )
    result = coach.invoke({"messages": [{"role": "user", "content": request}]})
    raw = result["messages"][-1].content or ""

    payload = load_json_object(raw)
    if payload is None:
        logger.warning("Coach returned unparseable JSON: %.200s", raw)
        return []

    return [task for task in (_validate(t) for t in payload.get("tasks") or []) if task]


def _validate(item: object) -> dict | None:
    if not isinstance(item, dict):
        return None

    action = (item.get("action") or "").strip()
    topic = (item.get("topic") or "").strip()
    if not action or not topic:
        return None

    return {
        "action": action,
        "topic": topic,
        "source": _validate_source(item.get("source")),
        "why": (item.get("why") or "").strip(),
        "est_minutes": _positive_int(item.get("est_minutes")),
    }


def _validate_source(source: object) -> dict | None:
    if not isinstance(source, dict):
        return None
    title = (source.get("document_title") or "").strip()
    if not title:
        return None
    return {"document_title": title, "page": _positive_int(source.get("page"))}


def _positive_int(value: object) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
