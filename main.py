"""Terminal chat with the WIiTek agent.

Run with ``uv run main.py``. Needs the database running and OPENAI_API_KEY set.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# The application code lives in src/ and imports itself by module name
# (``from config import ...``), so src/ has to be on the import path.
sys.path.insert(0, str(_ROOT / "src"))

from agent import ask, build_agent  # noqa: E402
from config import AgentSettings  # noqa: E402
from database.connection import close_pool  # noqa: E402


def main() -> None:
    """Read questions from the terminal and print the agent's answers until the user quits.

    Each question is sent on its own: the agent does not see earlier questions
    or answers, so a follow-up like "and in 2024?" is not understood yet.
    Quit with ``exit``, ``quit``, ``koniec`` or Ctrl+C.
    """
    agent = build_agent(AgentSettings())
    print("WIiTek — zapytaj o progi, przedmioty lub konsultacje. Ctrl+C kończy.\n")
    try:
        while True:
            question = input("> ").strip()
            if not question:
                continue
            if question.lower() in {"exit", "quit", "koniec"}:
                break
            messages = ask(agent, question)
            # Show which tools the agent called and with what, for debugging.
            for message in messages:
                for call in getattr(message, "tool_calls", None) or []:
                    print(f"  [{call['name']}({call['args']})]")
            print(f"\n{messages[-1].content}\n")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        close_pool()


if __name__ == "__main__":
    main()
