"""Layer 2 of the evaluation: two LLM judges that score the agent's final answer.

- **Faithfulness** — is every claim in the answer backed by the data the
  agent's tools returned? The judge never sees the reference answer, so this
  measures made-up content (hallucination) on its own.
- **Correctness** — does the answer match the benchmark's verified reference?

They are two separate calls on purpose: one judge seeing both the tool data
and the reference would mix the two questions up.
"""

import json

import eval._src_path  # noqa: F401  (puts src/ on sys.path)

from langchain_core.runnables import Runnable

from .benchmark_loader import reference_text
from .schemas import Correctness, Faithfulness, ToolCall
from templates import CORRECTNESS_PROMPT, FAITHFULNESS_PROMPT


def judge_faithfulness(
    judge: Runnable, case: dict, answer: str, tool_calls: list[ToolCall]
) -> Faithfulness:
    """Ask the judge whether every claim in the answer is backed by the tool output.

    The judge sees the question, the agent's tool calls with results, and the
    answer — never the reference, so it measures hallucination, not correctness.

    Args:
        judge: The judge model, set up to reply in the ``Faithfulness`` format.
        case: One benchmark case; only its question is used.
        answer: The agent's final answer — what gets checked.
        tool_calls: The agent's calls with results — the evidence every
            claim in the answer must be backed by.

    Returns:
        Faithfulness: ``claims`` — every claim in the answer, each marked
        supported / contradicted / unsupported by the tool data — and a
        ``score``: 2 all supported, 1 nothing contradicted but something
        vague, 0 a contradiction or an invented detail.
    """
    tool_output = json.dumps(
        [call.model_dump(mode="json") for call in tool_calls], ensure_ascii=False, indent=2
    )
    prompt = FAITHFULNESS_PROMPT.format(
        question=case["question"],
        tool_output=tool_output if tool_calls else "(nie wywolano zadnego narzedzia)",
        answer=answer,
    )
    return judge.invoke(prompt)


def judge_correctness(judge: Runnable, case: dict, answer: str) -> Correctness:
    """Ask the judge whether the answer is right against the verified reference.

    The judge sees the question, the case's ``expected_data`` as key facts,
    ``reference_text`` and the answer — not the tool output.

    Args:
        judge: The judge model, set up to reply in the ``Correctness`` format.
        case: One benchmark case — its question, key facts and reference.
        answer: The agent's final answer — what gets checked.

    Returns:
        Correctness: ``facts`` — each key fact of the reference, marked
        present / missing / contradicted in the answer — and a ``score``:
        2 all present, 1 some missing but nothing wrong, 0 something wrong
        or a critical fact missing.
    """
    prompt = CORRECTNESS_PROMPT.format(
        question=case["question"],
        key_facts=json.dumps(case.get("expected_data"), ensure_ascii=False, indent=2),
        reference=reference_text(case),
        answer=answer,
    )
    return judge.invoke(prompt)
