"""Proves LangChain's own path to the gateway supports tool calling.

Raw-HTTP tool calling was verified separately; this covers the LangChain
client, which handles the reasoning field differently. Hits the live gateway,
so it is marked slow.
"""

import pytest
from langchain.agents import create_agent
from langchain.tools import tool

from app.agents.llm import get_llm

pytestmark = pytest.mark.slow


@tool
def lookup_weak_topic(limit: int) -> str:
    """Return the topics the student scores worst on."""
    return '[{"topic": "Textual Feature Representation", "accuracy": 0.28}]'


def test_agent_calls_a_tool_and_uses_the_result():
    agent = create_agent(
        model=get_llm(),
        tools=[lookup_weak_topic],
        system_prompt="You are a study coach. Use the tools to get real data.",
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What am I weakest at? Use the tool."}]}
    )

    messages = result["messages"]
    assert any(getattr(m, "tool_calls", None) for m in messages), (
        "the model never issued a tool call"
    )
    assert any(type(m).__name__ == "ToolMessage" for m in messages)
    # The topic only exists in the tool's output, so quoting it proves the
    # result was actually consumed rather than invented.
    assert "Textual Feature Representation" in messages[-1].content
