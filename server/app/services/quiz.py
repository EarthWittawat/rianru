import uuid

from app.prompts import QUIZ_GENERATION_SYSTEM
from app.services.entity_extraction import load_json_object
from app.services.neo4j_client import get_driver
from app.services.vllm_client import VLLMError, chat

MAX_EXCERPT_CHUNKS = 12


class QuizGenerationError(RuntimeError):
    pass


def topic_excerpts(topic: str, limit: int = MAX_EXCERPT_CHUNKS) -> list[dict]:
    with get_driver().session() as session:
        return [
            record.data()
            for record in session.run(
                """
                MATCH (d:Document {topic: $topic})-[:HAS_CHUNK]->(c:Chunk)
                WHERE size(c.text) > 200
                RETURN c.id AS chunk_id, c.text AS text, c.page AS page,
                       d.title AS document_title
                ORDER BY size(c.text) DESC
                LIMIT $limit
                """,
                topic=topic,
                limit=limit,
            )
        ]


def generate(topic: str, count: int = 6) -> list[dict]:
    excerpts = topic_excerpts(topic)
    if not excerpts:
        return []

    context = "\n\n".join(
        f"[{e['document_title']}"
        + (f", page {e['page']}" if e["page"] else "")
        + f"]\n{e['text']}"
        for e in excerpts
    )
    raw = chat(
        [
            {"role": "system", "content": QUIZ_GENERATION_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\nCourse excerpts:\n{context}\n\n"
                    f"Write {count} questions."
                ),
            },
        ],
        max_tokens=6144,
    )

    payload = load_json_object(raw)
    if payload is None:
        raise QuizGenerationError(f"Model did not return JSON: {raw[:200]}")

    questions = [
        q for q in (_validate(item) for item in payload.get("questions") or []) if q
    ]
    _persist(topic, questions, excerpts[0]["chunk_id"])
    return questions


def _validate(item: object) -> dict | None:
    if not isinstance(item, dict):
        return None

    question = (item.get("question") or "").strip()
    answer = (item.get("answer") or "").strip()
    if not question or not answer:
        return None

    fmt = item.get("format")
    if fmt == "multiple_choice":
        options = [str(o).strip() for o in item.get("options") or [] if str(o).strip()]
        # A choice whose answer is not on the list is unanswerable, so drop it.
        if len(options) < 2 or answer not in options:
            return None
        return {
            "id": str(uuid.uuid4()),
            "format": "multiple_choice",
            "question": question,
            "options": options,
            "answer": answer,
            "explanation": (item.get("explanation") or "").strip(),
        }

    if fmt == "short_answer":
        return {
            "id": str(uuid.uuid4()),
            "format": "short_answer",
            "question": question,
            "options": [],
            "answer": answer,
            "explanation": (item.get("explanation") or "").strip(),
        }

    return None


def _persist(topic: str, questions: list[dict], source_chunk_id: str) -> None:
    if not questions:
        return
    with get_driver().session() as session:
        session.run(
            """
            MATCH (c:Chunk {id: $chunk_id})
            UNWIND $questions AS q
            CREATE (question:QuizQuestion {
                id: q.id,
                topic: $topic,
                format: q.format,
                question: q.question,
                options: q.options,
                answer: q.answer,
                explanation: q.explanation,
                created_at: datetime()
            })
            MERGE (question)-[:FROM_CHUNK]->(c)
            """,
            chunk_id=source_chunk_id,
            topic=topic,
            questions=questions,
        )


def stored_questions(topic: str | None = None) -> list[dict]:
    with get_driver().session() as session:
        return [
            record.data()
            for record in session.run(
                """
                MATCH (q:QuizQuestion)
                WHERE $topic IS NULL OR q.topic = $topic
                RETURN q.id AS id, q.topic AS topic, q.format AS format,
                       q.question AS question, q.options AS options,
                       q.answer AS answer, q.explanation AS explanation
                ORDER BY q.created_at DESC
                """,
                topic=topic,
            )
        ]


__all__ = [
    "generate",
    "stored_questions",
    "topic_excerpts",
    "chat",
    "VLLMError",
    "QuizGenerationError",
]
