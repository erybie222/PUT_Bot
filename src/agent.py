"""Building the WIiTek agent and the evaluation judge model, and asking the agent a question.

The agent is a LangChain tool-calling agent: an OpenAI chat model, the
read-only database tools from ``database.repository`` and the system prompt
from ``templates``. It decides by itself which tools to call for a question.
"""

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from config import JudgeSettings, AgentSettings
from database.repository import TOOLS
from templates import SYSTEM_PROMPT


def build_agent_model(settings: AgentSettings) -> ChatOpenAI:
    """Create the OpenAI chat model the agent thinks with.

    Args:
        settings: Model name, temperature and reasoning effort; this function
            does not read the environment itself.

    Returns:
        ChatOpenAI: The configured model. Settings left as None are not sent
        to the API at all.

    Raises:
        RuntimeError: OPENAI_API_KEY is not set.
    """
    return ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        reasoning_effort=settings.reasoning_effort,
        api_key=settings.require_api_key(),
    )


def build_judge_model(settings: JudgeSettings) -> ChatOpenAI:
    """Create the chat model that scores answers during evaluation.

    It has its own settings so it can be a different model from the agent: a
    judge built on the same model tends to miss the same mistakes.

    Args:
        settings: The judge's model name, temperature and reasoning effort.

    Returns:
        ChatOpenAI: The configured model.

    Raises:
        RuntimeError: OPENAI_API_KEY is not set.
    """
    return ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        reasoning_effort=settings.reasoning_effort,
        api_key=settings.require_api_key(),
    )


def build_agent(settings: AgentSettings) -> CompiledStateGraph:
    """Create the WIiTek agent: the chat model, the database tools and the system prompt.

    Args:
        settings: Settings for the agent's chat model.

    Returns:
        CompiledStateGraph: The agent; pass it to ``ask``.

    Raises:
        RuntimeError: OPENAI_API_KEY is not set.
    """
    return create_agent(
        model=build_agent_model(settings),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def ask(agent: CompiledStateGraph, question: str) -> list[BaseMessage]:
    """Ask the agent one question and return the whole exchange, not just the answer.

    The full exchange is returned because the evaluation needs to see which
    tools were called and what they returned.

    Args:
        agent: The agent from ``build_agent``.
        question: The user's question, in Polish or English.

    Returns:
        list[BaseMessage]: Every message in order; the last one is the final
        answer. Tool calls the agent made are in ``AIMessage.tool_calls``, and
        the rows each tool returned are in ``ToolMessage.artifact``.
    """
    return agent.invoke({"messages": [HumanMessage(content=question)]})["messages"]
