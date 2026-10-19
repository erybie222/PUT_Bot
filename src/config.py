"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


_ROOT_PATH = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT_PATH / ".env", override=True)

# Checked at startup so a typo fails here, not as an API error mid eval run.
REASONING_EFFORTS = ("none", "low", "medium", "high", "xhigh", "max")


def _optional(name: str) -> str | None:
    """Read an env var, with blank meaning unset.

    An empty model parameter is an API error, not a default, so blank must
    mean "omit".

    Args:
        name: Env var name.

    Returns:
        str | None: Stripped value, or None if unset/blank.
    """
    return os.getenv(name, "").strip() or None


def _optional_float(name: str) -> float | None:
    """Read an optional numeric env var.

    Args:
        name: Env var name.

    Returns:
        float | None: Parsed value, or None if unset/blank.

    Raises:
        ValueError: Set but not a number.
    """
    value = _optional(name)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{name}={value!r} is not a number; set a value like 0 or leave it blank.")


def _reasoning_effort(name: str) -> str | None:
    """Read a reasoning_effort env var.

    Args:
        name: Env var name.

    Returns:
        str | None: A value from ``REASONING_EFFORTS``, or None.

    Raises:
        ValueError: Set to an unsupported value.
    """
    value = _optional(name)
    if value is not None and value not in REASONING_EFFORTS:
        raise ValueError(
            f"{name}={value!r} is not a valid reasoning effort; "
            f"use one of {', '.join(REASONING_EFFORTS)} or leave it blank."
        )
    return value


@dataclass
class DatabaseSettings:
    """PostgreSQL connection settings."""

    dbname: str = field(default_factory=lambda: os.getenv("DB_NAME", ""))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", 5432)))

    def to_dict(self) -> dict[str, str | int]:
        """Connection kwargs for the psycopg pool.

        Returns:
            dict[str, str | int]: ``dbname``, ``user``, ``password``, ``host``, ``port``.
        """
        return {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port,
        }

@dataclass
class LLMSettings:
    """Agent model settings. Which parameter fits which model family: ``.env.example``.

    ``reasoning_effort`` falls back to ``"none"``: Chat Completions allows
    function calling on reasoning models only at that level.
    """

    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-6-luna"))
    temperature: float | None = field(
        default_factory=lambda: _optional_float("OPENAI_TEMPERATURE")
    )
    reasoning_effort: str | None = field(
        default_factory=lambda: _reasoning_effort("OPENAI_REASONING_EFFORT") or "none"
    )

    def require_api_key(self) -> str:
        """Return the key, or raise now instead of as an opaque SDK auth error.

        Returns:
            str: The OpenAI API key.

        Raises:
            RuntimeError: OPENAI_API_KEY unset or empty.
        """
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set — copy it into .env (see .env.example)."
            )
        return self.api_key


@dataclass
class JudgeSettings:
    """Judge model settings, separate so the judge can differ from the agent's model.

    Unlike ``LLMSettings``, ``reasoning_effort`` has no forced fallback: the
    judge uses structured output, not function calling.
    """

    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("JUDGE_MODEL", "gpt-6-luna"))
    temperature: float | None = field(
        default_factory=lambda: _optional_float("JUDGE_TEMPERATURE")
    )
    reasoning_effort: str | None = field(
        default_factory=lambda: _reasoning_effort("JUDGE_REASONING_EFFORT")
    )

    def require_api_key(self) -> str:
        """Return the key, or raise now instead of as an opaque SDK auth error.

        Returns:
            str: The OpenAI API key.

        Raises:
            RuntimeError: OPENAI_API_KEY unset or empty.
        """
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set — copy it into .env (see .env.example)."
            )
        return self.api_key
