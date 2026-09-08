from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import requires_ingested_corpus

client = TestClient(app)

pytestmark = requires_ingested_corpus


def test_lists_ingested_documents():
    response = client.get("/documents")
    assert response.status_code == 200

    documents = response.json()
    assert documents, "expected ingested CPE393 documents"
    first = documents[0]
    assert {"id", "title", "topic", "activity_type", "file_type"} <= set(first)
    assert all(d["course"] == "CPE393" for d in documents)


def test_serves_the_original_pdf_bytes():
    documents = client.get("/documents").json()
    pdf_doc = next(d for d in documents if d["file_type"] == "pdf")

    response = client.get(f"/documents/{pdf_doc['id']}/file")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_unknown_document_returns_404():
    assert client.get("/documents/does-not-exist/file").status_code == 404


def test_document_detail_includes_chunks():
    documents = client.get("/documents").json()
    pdf_doc = next(d for d in documents if d["file_type"] == "pdf")

    response = client.get(f"/documents/{pdf_doc['id']}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == pdf_doc["id"]
    assert detail["chunks"], "expected chunks for an ingested document"
    assert {"id", "text", "page"} <= set(detail["chunks"][0])
