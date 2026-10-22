"""Reading the benchmark (``eval/benchmark.yaml``) and deriving values from its cases.

A case is one question with what a correct answer must contain and which
tool calls should produce it. The YAML file itself explains its format.
"""

from pathlib import Path

import yaml


def load_cases(path: Path) -> list[dict]:
    """Read benchmark.yaml into one flat list of cases.

    Every top-level list except ``meta`` is a category; its name is copied
    into each of its cases.

    Args:
        path: Path to benchmark.yaml.

    Returns:
        list[dict]: Cases in file order. Each is its YAML entry as written,
        plus one added key. The keys the evaluation reads:
            ``id`` (str) — unique case name, used in output and ``--only``.
            ``category`` (str) — added here: the top-level list it came from.
            ``question`` (str) — what the agent is asked.
            ``expected_calls`` (list[dict] | None) — ``{"tool", "args"}`` per
                needed call; empty or missing means no tools are needed.
            ``expected_answer`` (str | None) — reference answer for the judge.
            ``expected_data`` (dict | None) — key facts for the judge.
            ``expected_behavior`` (str | None) — what the agent should do
                instead of answering, e.g. ask back.
    """
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = []
    for category, entries in document.items():
        if category == "meta" or not isinstance(entries, list):
            continue
        for entry in entries:
            cases.append({**entry, "category": category})
    return cases


def case_kind(case: dict) -> str:
    """Say what kind of response the case expects; shown in the console and the report.

    Args:
        case: One benchmark case.

    Returns:
        str: ``"clarify"`` if it has ``expected_behavior`` (the agent should
        ask the user something back), ``"lookup"`` if it has ``expected_data``
        (the agent should answer from the database), otherwise ``"refusal"``
        (the agent should say it does not know or cannot help).
    """
    if case.get("expected_behavior"):
        return "clarify"
    if case.get("expected_data"):
        return "lookup"
    return "refusal"


def reference_text(case: dict) -> str:
    """Build the reference text the correctness judge compares the answer with.

    Args:
        case: One benchmark case.

    Returns:
        str: ``expected_answer`` and/or ``expected_behavior``, one per line;
        for a case with neither, a note that the right answer is "I don't know".
    """
    parts = []
    if case.get("expected_answer"):
        parts.append(str(case["expected_answer"]))
    if case.get("expected_behavior"):
        parts.append(f"Oczekiwane zachowanie: {case['expected_behavior']}")
    if not parts:
        parts.append('Poprawna reakcja to "nie wiem" - brak danych w bazie.')
    return "\n".join(parts)
