import httpx

from app.config import settings

DEFAULT_TIMEOUT = 120.0


class VLLMError(RuntimeError):
    pass


def chat(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 4096,
    transport: httpx.BaseTransport | None = None,
) -> str:
    """Send a chat completion and return the assistant's content.

    The gateway model is a reasoning model: it spends tokens on
    `reasoning_content` before emitting any `content`, so a tight
    `max_tokens` yields a null content rather than a short answer.
    """
    payload = {
        "model": settings.vllm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {settings.vllm_api_key}"}

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT, transport=transport) as client:
            response = client.post(
                f"{settings.vllm_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise VLLMError(f"vLLM request failed: {exc}") from exc

    if response.status_code != 200:
        raise VLLMError(
            f"vLLM returned {response.status_code}: {response.text[:200]}"
        )

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise VLLMError(f"Unexpected vLLM response shape: {response.text[:200]}") from exc

    if not content:
        raise VLLMError(
            f"vLLM returned empty content (max_tokens={max_tokens}); the reasoning "
            "model likely spent the whole budget before answering — retry with more."
        )
    return content.strip()
