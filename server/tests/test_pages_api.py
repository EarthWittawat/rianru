from fastapi.testclient import TestClient

from app.main import app
from app.services import colpali_index
from app.routers import pages as pages_router

client = TestClient(app)


def test_a_course_is_required():
    assert client.get("/pages/search", params={"q": "a chart"}).status_code == 400


def test_a_course_without_an_index_says_so_rather_than_failing(monkeypatch):
    monkeypatch.setattr(colpali_index, "has_index", lambda course: False)

    body = client.get("/pages/search", params={"q": "a chart", "course": "DEMO"}).json()

    assert body == {"indexed": False, "hits": []}


def test_hits_carry_the_document_title_and_page(monkeypatch):
    monkeypatch.setattr(colpali_index, "has_index", lambda course: True)
    monkeypatch.setattr(
        colpali_index,
        "search",
        lambda *_, **__: [{"document_id": "DEMO::doc", "page": 4, "score": 9.5}],
    )
    monkeypatch.setattr(
        pages_router, "_document_titles", lambda ids: {"DEMO::doc": "Demo lecture"}
    )

    body = client.get("/pages/search", params={"q": "a chart", "course": "DEMO"}).json()

    assert body["indexed"] is True
    assert body["hits"] == [
        {
            "document_id": "DEMO::doc",
            "page": 4,
            "score": 9.5,
            "document_title": "Demo lecture",
        }
    ]


def test_a_hit_whose_document_has_gone_is_dropped(monkeypatch):
    monkeypatch.setattr(colpali_index, "has_index", lambda course: True)
    monkeypatch.setattr(
        colpali_index,
        "search",
        lambda *_, **__: [{"document_id": "deleted::doc", "page": 1, "score": 3.0}],
    )
    monkeypatch.setattr(pages_router, "_document_titles", lambda ids: {})

    body = client.get("/pages/search", params={"q": "a chart", "course": "DEMO"}).json()

    assert body["hits"] == []
