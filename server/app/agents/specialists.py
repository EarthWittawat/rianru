"""Specialist agents, exposed to the supervisor as tools.

Subagents-as-tools is the pattern LangChain currently recommends over the
deprecated supervisor package.
"""

from functools import lru_cache

from langchain.agents import create_agent
from langchain.tools import tool

from app.agents.llm import get_llm
from app.agents.tools import MATERIAL_TOOLS, PROGRESS_TOOLS

PROGRESS_AGENT_PROMPT = """You report on a student's quiz performance.

Use the tools to read their real results. Never guess a score or invent a
topic. Answer with the topic names, their accuracy, and how many attempts
each is based on. If they have not attempted anything, say so plainly."""

MATERIAL_AGENT_PROMPT = """You locate where a subject is covered in a student's
course material.

Use the tools to search the real material. For anything you recommend, give the
document title and the page number. Never invent a document, a page, or a topic
name — only report what the tools return."""


@lru_cache(maxsize=1)
def progress_agent():
    return create_agent(
        model=get_llm(), tools=PROGRESS_TOOLS, system_prompt=PROGRESS_AGENT_PROMPT
    )


@lru_cache(maxsize=1)
def material_agent():
    return create_agent(
        model=get_llm(), tools=MATERIAL_TOOLS, system_prompt=MATERIAL_AGENT_PROMPT
    )


def _ask(agent, question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content or ""


@tool
def ask_progress(question: str) -> str:
    """Ask about the student's quiz performance: what they are weak at, their
    accuracy per topic, or their recent attempts."""
    return _ask(progress_agent(), question)


@tool
def ask_material(question: str) -> str:
    """Ask where a subject is covered in the course material. Returns document
    titles and page numbers."""
    return _ask(material_agent(), question)


SUBAGENT_TOOLS = [ask_progress, ask_material]
