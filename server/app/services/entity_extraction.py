import json
import logging
import re

from app.prompts import ENTITY_EXTRACTION_SYSTEM
from app.services.vllm_client import VLLMError, chat

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_OBJECT = re.compile(r"\{.*\}", re.DOTALL)

VALID_ENTITY_TYPES = {"concept", "method", "tool", "library", "metric", "task"}


def extract_graph_from_text(text: str) -> tuple[list[dict], list[dict]]:
    """Extract entities and relations from a chunk. Never raises."""
    try:
        raw = chat(
            [
                {"role": "system", "content": ENTITY_EXTRACTION_SYSTEM},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
        )
    except VLLMError as exc:
        logger.warning("Entity extraction call failed, skipping chunk: %s", exc)
        return [], []

    return parse_extraction_response(raw)


def parse_extraction_response(raw: str) -> tuple[list[dict], list[dict]]:
    """Parse the model's JSON. Malformed output yields empty lists, not an error."""
    payload = load_json_object(raw)
    if payload is None:
        logger.warning("Entity extraction returned unparseable JSON: %.120s", raw)
        return [], []

    entities = []
    seen: set[str] = set()
    for item in payload.get("entities") or []:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        entity_type = (item.get("type") or "concept").strip().lower()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        entities.append(
            {
                "name": name,
                "type": entity_type if entity_type in VALID_ENTITY_TYPES else "concept",
            }
        )

    known = {e["name"] for e in entities}
    relations = []
    for item in payload.get("relations") or []:
        if not isinstance(item, dict):
            continue
        source = (item.get("source") or "").strip()
        target = (item.get("target") or "").strip()
        relation_type = (item.get("type") or "").strip()
        if source in known and target in known and relation_type and source != target:
            relations.append(
                {"source": source, "target": target, "type": relation_type}
            )

    return entities, relations


def load_json_object(raw: str) -> dict | None:
    """Pull a JSON object out of model output, fenced or surrounded by prose."""
    for candidate in _candidates(raw):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _candidates(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return
    yield raw
    fenced = _FENCE.search(raw)
    if fenced:
        yield fenced.group(1)
    obj = _OBJECT.search(raw)
    if obj:
        yield obj.group(0)
