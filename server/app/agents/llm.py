from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import settings

# The gateway model reasons before answering, so a tight budget produces an
# empty reply rather than a short one — see app/services/vllm_client.py.
DEFAULT_MAX_TOKENS = 4096


@lru_cache(maxsize=4)
def get_llm(max_tokens: int = DEFAULT_MAX_TOKENS, temperature: float = 0.2) -> ChatOpenAI:
    """The gateway, as a LangChain chat model.

    Verified to support native tool calling: the agent loop issues a tool call,
    consumes the result, and produces a final answer.
    """
    return ChatOpenAI(
        model=settings.vllm_model,
        base_url=settings.vllm_url,
        api_key=settings.vllm_api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )
