from app.prompts import EXPLAIN_SYSTEM
from app.services.neo4j_client import get_driver
from app.services.vllm_client import VLLMError, chat

CONTEXT_NEIGHBOURS = 1


def resolve_chunk(document_id: str, selected_text: str, page: int | None) -> str | None:
    """Find the chunk a selection came from.

    The browser knows the page and the selected text, not our chunk ids, so
    the match happens here: prefer a chunk on the same page that literally
    contains the selection, then fall back to word overlap.
    """
    with get_driver().session() as session:
        chunks = [
            record.data()
            for record in session.run(
                """
                MATCH (:Document {id: $document_id})-[:HAS_CHUNK]->(c:Chunk)
                RETURN c.id AS id, c.text AS text, c.page AS page, c.index AS index
                ORDER BY c.index
                """,
                document_id=document_id,
            )
        ]

    if not chunks:
        return None

    same_page = [c for c in chunks if page and c["page"] == page] or chunks
    needle = " ".join(selected_text.split())

    for chunk in same_page:
        if needle and needle in " ".join(chunk["text"].split()):
            return chunk["id"]

    selection_words = set(needle.lower().split())
    if not selection_words:
        return same_page[0]["id"]

    best = max(
        same_page,
        key=lambda c: len(selection_words & set(c["text"].lower().split())),
    )
    return best["id"]


def get_chunk_context(chunk_id: str) -> dict | None:
    """Return the chunk plus its immediate neighbours in the same document."""
    with get_driver().session() as session:
        record = session.run(
            """
            MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk {id: $chunk_id})
            WITH d, c
            MATCH (d)-[:HAS_CHUNK]->(neighbour:Chunk)
            WHERE abs(neighbour.index - c.index) <= $window
            WITH d, c, neighbour ORDER BY neighbour.index
            RETURN d.title AS document_title,
                   d.topic AS topic,
                   c.page AS page,
                   collect(neighbour.text) AS context_texts
            """,
            chunk_id=chunk_id,
            window=CONTEXT_NEIGHBOURS,
        ).single()

    return record.data() if record else None


def explain_selection(
    document_id: str, selected_text: str, page: int | None = None
) -> dict:
    chunk_id = resolve_chunk(document_id, selected_text, page)
    if chunk_id is None:
        return {}

    context = get_chunk_context(chunk_id)
    if context is None:
        return {}

    joined = "\n\n".join(context["context_texts"])
    user_message = (
        f"Course material — {context['topic']} ({context['document_title']}):\n"
        f'"""\n{joined}\n"""\n\n'
        f'The student selected this passage:\n"{selected_text}"\n\n'
        "Explain the selected passage."
    )

    explanation = chat(
        [
            {"role": "system", "content": EXPLAIN_SYSTEM},
            {"role": "user", "content": user_message},
        ]
    )

    return {
        "explanation": explanation,
        "selected_text": selected_text,
        "chunk_id": chunk_id,
        "document_title": context["document_title"],
        "topic": context["topic"],
        "page": context["page"],
    }


__all__ = [
    "explain_selection",
    "get_chunk_context",
    "resolve_chunk",
    "chat",
    "VLLMError",
]
