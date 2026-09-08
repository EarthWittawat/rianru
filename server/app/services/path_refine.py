"""The model pass over the learning path.

The timeline can only order concepts taught at different points. Everything
inside one lecture, and every concept the spine never places, is invisible to
it. This asks the model to fill that in, one call per topic, and treats its
answer as a proposal: an edge survives only if both concepts already exist in
the course and it carries a reason a student can read.
"""

import logging

from app.prompts import PREREQUISITE_SYSTEM
from app.services.entity_extraction import load_json_object
from app.services.graph_store import (
    clear_requirements,
    concepts_by_topic,
    write_requirements,
)
from app.services.vllm_client import VLLMError, chat

logger = logging.getLogger(__name__)

# Enough concepts for the model to see a topic whole, few enough to answer well.
MAX_CONCEPTS_PER_CALL = 60


def parse_requirements(raw: str, known: set[str]) -> list[dict]:
    """Validate the model's proposals against concepts that actually exist."""
    payload = load_json_object(raw)
    if payload is None:
        logger.warning("Prerequisite pass returned unparseable JSON: %.120s", raw)
        return []

    canonical = {name.lower(): name for name in known}
    edges: dict[tuple[str, str], dict] = {}

    for item in payload.get("requirements") or []:
        if not isinstance(item, dict):
            continue
        concept = canonical.get((item.get("concept") or "").strip().lower())
        requires = canonical.get((item.get("requires") or "").strip().lower())
        reason = (item.get("reason") or "").strip()
        if not concept or not requires or not reason or concept == requires:
            continue
        edges[(concept, requires)] = {
            "source": concept,
            "target": requires,
            "origin": "model",
            "reason": reason,
        }

    return list(edges.values())


def refine_course(course: str) -> int:
    """Ask the model for the prerequisites inside each topic. Returns edges written."""
    by_topic = concepts_by_topic(course)
    known = {name for names in by_topic.values() for name in names}
    clear_requirements(origin="model")

    written = 0
    for topic, concepts in by_topic.items():
        if len(concepts) < 2:
            continue
        subset = concepts[:MAX_CONCEPTS_PER_CALL]
        try:
            raw = chat(
                [
                    {"role": "system", "content": PREREQUISITE_SYSTEM},
                    {
                        "role": "user",
                        "content": f"Topic: {topic}\nConcepts:\n"
                        + "\n".join(f"- {name}" for name in subset),
                    },
                ],
                temperature=0.0,
            )
        except VLLMError as exc:
            logger.warning("Prerequisite pass failed for %s: %s", topic, exc)
            continue

        edges = parse_requirements(raw, known)
        written += write_requirements(edges)
        print(f"  {topic[:44]:<44} {len(subset):>3} concepts → {len(edges)} prerequisites")

    return written
