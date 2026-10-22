"""Layer 1 of the evaluation: checking the agent's tool calls, without any LLM.

For each case the benchmark lists the tool calls a correct answer needs
(``expected_calls``). This module answers two questions about what the agent
actually did:

- did it call every tool the case needs? (``called_right_tools``)
- did those calls return the right data? (``got_right_data``) — checked by
  running the expected calls on the database and comparing results, so the
  exact wording of the agent's arguments does not matter.
"""

from . import _src_path  # noqa: F401  (puts src/ on sys.path)

from langchain_core.messages import BaseMessage

from database.repository import TOOLS
from .schemas import ToolCall, ToolScores

TOOLS_BY_NAME = {tool.name: tool for tool in TOOLS}

# Placeholder in benchmark arguments meaning "the id returned by the previous
# expected call". Staff ids change on every ingestion, so the benchmark cannot
# contain real ones.
PREV_ID = "$prev.id"


def fill_prev_id(args: dict, previous_rows: list | None) -> dict:
    """Replace ``$prev.id`` in an expected call's arguments with a real id.

    Staff ids change on every ingestion, so the benchmark chains calls with
    ``$prev.id`` instead of hard-coding an id.

    Args:
        args: Arguments of one expected call, as written in the benchmark.
        previous_rows: Rows returned by the preceding expected call, or None.

    Returns:
        dict: Copy of ``args`` with each ``$prev.id`` replaced by the ``id`` of
        the single row in ``previous_rows`` — or None when there are zero or
        several rows, since picking one would hide the ambiguity. Other values
        are unchanged.
    """
    resolved = {}
    for key, value in (args or {}).items():
        if value != PREV_ID:
            resolved[key] = value
        elif previous_rows and len(previous_rows) == 1:
            resolved[key] = previous_rows[0].get("id")
        else:
            resolved[key] = None
    return resolved


def run_expected_calls(calls: list[dict]) -> list[ToolCall]:
    """Run a case's expected calls on the live DB to get the correct data.

    This is the answer key for ``got_right_data``: ``score_tool_calls``
    compares the agent's results with these. It is computed on every run, not
    stored in the benchmark, because ids and data change between ingestions.
    Calls run in order; ``$prev.id`` resolves from the last call that
    returned a list.

    Args:
        calls: A case's ``expected_calls``, each ``{"tool", "args"}``.

    Returns:
        list[ToolCall]: One per expected call, in order. ``args`` are the
        arguments actually used (after ``fill_prev_id``), ``result`` is what
        the tool returned.

    Raises:
        Exception: Whatever the tool raises (a DB error, or ``KeyError`` for
            an unknown tool name); ``score_tool_calls`` catches it.
    """
    results = []
    previous_rows = None
    for call in calls:
        name = call["tool"]
        args = fill_prev_id(call.get("args"), previous_rows)
        # Bare args would return only the text; a tool_call returns the ToolMessage with the artifact.
        message = TOOLS_BY_NAME[name].invoke(
            {"type": "tool_call", "name": name, "args": args, "id": "expected"}
        )
        result = message.artifact
        results.append(ToolCall(name=name, args=args, result=result))
        if isinstance(result, list):
            previous_rows = result
    return results


def agent_tool_calls(messages: list[BaseMessage]) -> list[ToolCall]:
    """Extract the agent's tool calls from its messages, each with its result.

    Calls and results are joined by ``tool_call_id``, not position: a batched
    turn interleaves them. A failure is detected by ``status``, not
    ``artifact is None``, since ``get_department`` returns None legitimately.

    Args:
        messages: The message list returned by ``agent.ask``.

    Returns:
        list[ToolCall]: One per agent tool call, in call order. ``result`` is
        what the tool returned, the error text if the call failed, or None if
        no result message was found.
    """
    results = {
        message.tool_call_id: message.content if message.status == "error" else message.artifact
        for message in messages
        if message.type == "tool"
    }
    return [
        ToolCall(name=call["name"], args=call["args"], result=results.get(call["id"]))
        for message in messages
        if message.type == "ai"
        for call in message.tool_calls
    ]


def score_tool_calls(expected: list[dict], agent_calls: list[ToolCall]) -> ToolScores:
    """Score the agent's tool calls on one case against its expected calls (no LLM).

    Two questions, answered separately so a failure says which one went wrong:

    - ``called_right_tools`` — did the agent call every tool the case needs?
      Only tool names count. Extra calls do not fail it; they are counted
      once, in ``extra_calls``, instead of being punished twice.
    - ``got_right_data`` — did those calls return the right data? The
      expected calls are run on the DB (``run_expected_calls``) and each
      result must equal the result of some agent call to the same tool.
      Arguments are never compared, so "Informatyka" vs "informatyka" costs
      nothing as long as the data is the same. Caveat: if the right result is
      empty, a wrong call that also finds nothing passes too.

    Args:
        expected: A case's ``expected_calls``; empty means the case needs no tools.
        agent_calls: The agent's calls with results, from ``agent_tool_calls``.

    Returns:
        ToolScores: The case's layer-1 result. What each field means is
        described on the ``ToolScores`` model.
    """
    called_tools = [call.name for call in agent_calls]
    expected_tools = [call["tool"] for call in expected]
    extra_calls = max(0, len(called_tools) - len(expected_tools))

    # Case needs no tools (out of scope, greeting, ...): the only right move is
    # to call nothing, so both called_right_tools and called_no_tools mean
    # "nothing was called", and every call counts as extra. There are no
    # expected calls to run, so got_right_data is not scored.
    if not expected:
        return ToolScores(
            called_right_tools=not called_tools,
            got_right_data=None,
            called_no_tools=not called_tools,
            extra_calls=len(called_tools),
            expected_tools=[],
            called_tools=called_tools,
            wrong_data_tools=[],
            expected_calls_error=None,
        )

    # Right tools: tick off each needed tool against the agent's calls; one
    # call can only cover one needed tool.
    missing_tools = []
    unclaimed = list(called_tools)
    for name in expected_tools:
        if name in unclaimed:
            unclaimed.remove(name)
        else:
            missing_tools.append(name)

    # Right data, step 1: run the expected calls now to get the correct rows.
    try:
        correct_results = run_expected_calls(expected)
    except Exception as error:
        return ToolScores(
            called_right_tools=not missing_tools,
            got_right_data=None,
            called_no_tools=None,
            extra_calls=extra_calls,
            expected_tools=expected_tools,
            called_tools=called_tools,
            wrong_data_tools=[],
            expected_calls_error=f"could not run an expected call: {error}",
        )

    # Right data, step 2: each correct result needs an agent call to the same
    # tool with an equal result. A matched agent call is used up so it cannot
    # cover two expected calls.
    wrong_data_tools = []
    unused_agent_calls = list(agent_calls)
    for correct in correct_results:
        agent_call = next(
            (call for call in unused_agent_calls
             if call.name == correct.name and call.result == correct.result),
            None,
        )
        if agent_call is None:
            wrong_data_tools.append(correct.name)
        else:
            unused_agent_calls.remove(agent_call)

    return ToolScores(
        called_right_tools=not missing_tools,
        got_right_data=not wrong_data_tools,
        called_no_tools=None,
        extra_calls=extra_calls,
        expected_tools=expected_tools,
        called_tools=called_tools,
        wrong_data_tools=wrong_data_tools,
        expected_calls_error=None,
    )
