"""Helpers for turning raw psycopg rows into JSON-safe dicts.

psycopg returns ``Decimal`` for NUMERIC columns and ``datetime``/``time`` for
timestamp/time columns — none of those survive ``json.dumps`` unchanged, which
matters once these rows are returned from a LangChain tool to an LLM.
"""

from datetime import datetime, time
from decimal import Decimal
from typing import Any


def _to_json_safe(value: Any) -> Any:
    """Convert one psycopg-returned value into a JSON-serializable one."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, time)):
        return value.isoformat()
    return value


def row_to_dict(columns: tuple[str, ...], row: tuple) -> dict:
    """
    Zip column names with a psycopg row into a JSON-safe dict.

    Args:
        columns: Column names, in the same order as the SELECT list.
        row: One row as returned by cursor.fetchone()/fetchall().

    Returns:
        dict: Mapping of column name to value, with Decimal/datetime/time
            values converted to float/isoformat strings.
    """
    return {column: _to_json_safe(value) for column, value in zip(columns, row)}
