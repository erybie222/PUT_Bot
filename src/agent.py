
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from config import JudgeSettings, LLMSettings
from database.repository import TOOLS
from templates import SYSTEM_PROMPT


def build_model(settings: LLMSettings) -> ChatOpenAI:
    """Chat model for the agent.

    Args:
        settings: Built by the caller; nothing here reads the environment.

    Returns:
        ChatOpenAI: Configured model.

    Raises:
        RuntimeError: OPENAI_API_KEY unset.
    """
    return ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        reasoning_effort=settings.reasoning_effort,
        api_key=settings.require_api_key(),
    )


def build_judge_model(settings: JudgeSettings) -> ChatOpenAI:
    """Chat model for the eval judges, separate so it can differ from the model under test.

    Args:
        settings: Judge settings, built by the caller.

    Returns:
        ChatOpenAI: Configured model.

    Raises:
        RuntimeError: OPENAI_API_KEY unset.
    """
    return ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        reasoning_effort=settings.reasoning_effort,
        api_key=settings.require_api_key(),
    )


def build_agent(settings: LLMSettings) -> CompiledStateGraph:
    """WIiTek agent: chat model + read-only DB tools + system prompt.

    Args:
        settings: Model settings, built by the caller.

    Returns:
        CompiledStateGraph: Agent ready for ``.invoke``.

    Raises:
        RuntimeError: OPENAI_API_KEY unset.
    """
    return create_agent(
        model=build_model(settings),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def ask(agent: CompiledStateGraph, question: str) -> list[BaseMessage]:
    """Put one question to the agent and return the whole exchange.

    Args:
        agent: Agent from ``build_agent``.
        question: Question in Polish or English.

    Returns:
        list[BaseMessage]: Every message, answer last. Calls are in
            ``AIMessage.tool_calls``, their rows in ``ToolMessage.artifact``.
    """
    return agent.invoke({"messages": [HumanMessage(content=question)]})["messages"]
