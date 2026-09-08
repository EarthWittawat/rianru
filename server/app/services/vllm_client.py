import logging
import time

import httpx

from app.config import settings

DEFAULT_TIMEOUT = 120.0

# The gateway caps concurrent requests per API key (max_parallel_requests: 3).
# Over that it returns 429, which is transient — retry rather than dropping work.
MAX_RETRIES = 6
BACKOFF_SECONDS = 2.0

logger = logging.getLogger(__name__)


class VLLMError(RuntimeError):
    pass


def chat(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 4096,
    transport: httpx.BaseTransport | None = None,
    timeout: float = DEFAULT_TIMEOUT,
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

    url = f"{settings.vllm_url.rstrip('/')}/chat/completions"

    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=timeout, transport=transport) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise VLLMError(f"vLLM request failed: {exc}") from exc

        # 429 is the per-key concurrency cap; 5xx is the gateway itself, most
        # often a 524 when a long reasoning call outlives its edge timeout.
        # Both are transient and worth waiting out.
        retryable = response.status_code == 429 or response.status_code >= 500
        if retryable and attempt < MAX_RETRIES - 1:
            delay = BACKOFF_SECONDS * (2**attempt)
            logger.info("vLLM returned %d, retrying in %.0fs", response.status_code, delay)
            time.sleep(delay)
            continue
        break

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
