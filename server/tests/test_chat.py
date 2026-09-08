from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import requires_ingested_corpus
from app.services import chat as chat_service

client = TestClient(app)

pytestmark = requires_ingested_corpus


def test_chat_answer_is_built_from_retrieved_chunks(monkeypatch):
    captured = {}

    def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return "Regular expressions describe character patterns."

    monkeypatch.setattr(chat_service, "chat", fake_chat)

    response = client.post(
        "/chat", json={"message": "What are regular expressions used for?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Regular expressions describe character patterns."
    assert body["sources"], "expected retrieved sources alongside the answer"
    assert {"chunk_id", "document_title", "topic"} <= set(body["sources"][0])

    user_message = captured["messages"][-1]["content"]
    for source in body["sources"]:
        assert source["document_title"] in user_message, (
            "retrieved chunks must be in the prompt, not just reported"
        )


def test_chat_retrieves_topically_relevant_material():
    """Retrieval, not the model, is what this asserts — so no mocking."""
    sources = chat_service.retrieve("regular expressions and pattern matching", top_k=5)

    assert sources
    combined = " ".join(s["text"].lower() for s in sources)
    assert "regex" in combined or "regular expression" in combined or "pattern" in combined


def test_chat_passes_conversation_history(monkeypatch):
    captured = {}

    def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return "answer"

    monkeypatch.setattr(chat_service, "chat", fake_chat)

    client.post(
        "/chat",
        json={
            "message": "And how is it different?",
            "history": [
                {"role": "user", "content": "What is stemming?"},
                {"role": "assistant", "content": "Stemming chops word endings."},
            ],
        },
    )

    roles = [m["role"] for m in captured["messages"]]
    contents = " ".join(m["content"] for m in captured["messages"])
    assert roles[0] == "system"
    assert "What is stemming?" in contents
    assert "Stemming chops word endings." in contents


def test_chat_surfaces_gateway_failure(monkeypatch):
    def boom(messages, **kwargs):
        raise chat_service.VLLMError("gateway down")

    monkeypatch.setattr(chat_service, "chat", boom)

    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 502
