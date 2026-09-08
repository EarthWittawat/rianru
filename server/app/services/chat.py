from app.prompts import CHAT_TUTOR_SYSTEM
from app.services import colbert_index
from app.services.graph_store import chunks_by_id, similarity_search
from app.services.vllm_client import VLLMError, chat

TOP_K = 6
MAX_HISTORY_TURNS = 6


def retrieve(question: str, top_k: int = TOP_K, course: str | None = None) -> list[dict]:
    """Late interaction where the course has an index, dense everywhere else.

    A dense vector averages a chunk into one point, which loses the exact term a
    student typed. ColBERT keeps a vector per token and cannot average it away,
    so it is preferred — but it needs an index built per course, and a course
    without one still has to answer.
    """
    if course and colbert_index.has_index(course):
        hits = colbert_index.search(question, course, top_k=top_k)
        hydrated = chunks_by_id([chunk_id for chunk_id, _ in hits])
        sources = []
        for chunk_id, score in hits:
            chunk = hydrated.get(chunk_id)
            if chunk:
                sources.append({**chunk, "score": score, "retrieval": "colbert"})
        if sources:
            return sources

    return [
        {**hit, "retrieval": "dense"}
        for hit in similarity_search(question, top_k=top_k, course=course)
    ]


def answer(
    question: str, history: list[dict] | None = None, course: str | None = None
) -> dict:
    sources = retrieve(question, course=course)
    context = "\n\n".join(
        f"[{s['document_title']} — {s['topic']}"
        + (f", page {s['page']}" if s["page"] else "")
        + f"]\n{s['text']}"
        for s in sources
    )

    messages = [{"role": "system", "content": CHAT_TUTOR_SYSTEM}]
    for turn in (history or [])[-MAX_HISTORY_TURNS:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append(
        {
            "role": "user",
            "content": (
                f"Course excerpts:\n{context}\n\n"
                f"Student's question: {question}"
            ),
        }
    )

    return {
        "answer": chat(messages),
        "sources": [
            {
                "chunk_id": s["chunk_id"],
                "document_id": s["document_id"],
                "document_title": s["document_title"],
                "topic": s["topic"],
                "page": s["page"],
                "score": s["score"],
            }
            for s in sources
        ],
    }


__all__ = ["answer", "retrieve", "chat", "VLLMError"]
