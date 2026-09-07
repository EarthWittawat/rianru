from app.prompts import CHAT_TUTOR_SYSTEM
from app.services.graph_store import similarity_search
from app.services.vllm_client import VLLMError, chat

TOP_K = 6
MAX_HISTORY_TURNS = 6


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    return similarity_search(question, top_k=top_k)


def answer(question: str, history: list[dict] | None = None) -> dict:
    sources = retrieve(question)
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
