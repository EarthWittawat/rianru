from fastapi.testclient import TestClient

from app.main import app
from app.services import explain as explain_service

client = TestClient(app)


def _pdf_document() -> dict:
    """The largest ingested PDF, so tests have several chunks to work with."""
    documents = client.get("/documents").json()
    pdf_doc = max(
        (d for d in documents if d["file_type"] == "pdf"),
        key=lambda d: d["chunk_count"],
    )
    return client.get(f"/documents/{pdf_doc['id']}").json()


def test_explain_returns_grounded_explanation(monkeypatch):
    captured = {}

    def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return "TF-IDF weights terms by how rare they are."

    monkeypatch.setattr(explain_service, "chat", fake_chat)

    document = _pdf_document()
    chunk = document["chunks"][2]
    snippet = " ".join(chunk["text"].split()[:6])

    response = client.post(
        "/explain",
        json={
            "document_id": document["id"],
            "selected_text": snippet,
            "page": chunk["page"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["explanation"] == "TF-IDF weights terms by how rare they are."
    assert body["selected_text"] == snippet
    assert body["chunk_id"] == chunk["id"]

    user_message = captured["messages"][-1]["content"]
    assert snippet in user_message
    assert len(user_message) > len(snippet) + 100, "surrounding context should be sent"


def test_resolve_chunk_prefers_the_chunk_containing_the_selection():
    document = _pdf_document()
    target = document["chunks"][3]
    snippet = " ".join(target["text"].split()[:8])

    resolved = explain_service.resolve_chunk(document["id"], snippet, target["page"])

    assert resolved == target["id"]


def test_explain_rejects_unknown_document():
    response = client.post(
        "/explain", json={"document_id": "nope", "selected_text": "x"}
    )
    assert response.status_code == 404


def test_explain_surfaces_gateway_failure(monkeypatch):
    def boom(messages, **kwargs):
        raise explain_service.VLLMError("gateway down")

    monkeypatch.setattr(explain_service, "chat", boom)

    document = _pdf_document()
    response = client.post(
        "/explain",
        json={"document_id": document["id"], "selected_text": "TF-IDF"},
    )
    assert response.status_code == 502
