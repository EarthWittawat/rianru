import httpx
import pytest

from app.services.vllm_client import VLLMError, chat


def _mock_transport(handler):
    return httpx.MockTransport(handler)


def test_chat_returns_model_text():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"].startswith("Bearer ")
        payload = request.read().decode()
        assert "what is tf-idf" in payload.lower()
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "TF-IDF weights terms."}}]},
        )

    result = chat(
        [{"role": "user", "content": "What is TF-IDF?"}],
        transport=_mock_transport(handler),
    )
    assert result == "TF-IDF weights terms."


def test_chat_raises_typed_error_on_http_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream exploded")

    with pytest.raises(VLLMError) as exc:
        chat([{"role": "user", "content": "hi"}], transport=_mock_transport(handler))
    assert "500" in str(exc.value)


def test_chat_raises_typed_error_on_malformed_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    with pytest.raises(VLLMError):
        chat([{"role": "user", "content": "hi"}], transport=_mock_transport(handler))


def test_chat_raises_when_reasoning_consumed_the_whole_budget():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "reasoning_content": "thinking but never answered",
                        }
                    }
                ]
            },
        )

    with pytest.raises(VLLMError) as exc:
        chat([{"role": "user", "content": "hi"}], transport=_mock_transport(handler))
    assert "max_tokens" in str(exc.value)


def test_chat_retries_rate_limits_then_succeeds(monkeypatch):
    from app.services import vllm_client

    monkeypatch.setattr(vllm_client, "BACKOFF_SECONDS", 0.0)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, text="rate limit exceeded")
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "recovered"}}]}
        )

    result = chat(
        [{"role": "user", "content": "hi"}], transport=_mock_transport(handler)
    )

    assert result == "recovered"
    assert calls["n"] == 3


def test_chat_gives_up_after_repeated_rate_limits(monkeypatch):
    from app.services import vllm_client

    monkeypatch.setattr(vllm_client, "BACKOFF_SECONDS", 0.0)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="rate limit exceeded")

    with pytest.raises(VLLMError) as exc:
        chat([{"role": "user", "content": "hi"}], transport=_mock_transport(handler))
    assert "429" in str(exc.value)


def test_chat_raises_typed_error_on_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    with pytest.raises(VLLMError):
        chat([{"role": "user", "content": "hi"}], transport=_mock_transport(handler))
