"""psycopg rows → JSON-safe dicts.

``Decimal``, ``datetime`` and ``time`` don't survive ``json.dumps``, which tool
output has to on its way to the model.
"""

from datetime import datetime, time
from decimal import Decimal
from typing import Any


def _to_json_safe(value: Any) -> Any:
    """Convert one psycopg value to a JSON-serializable one.

    Args:
        value: Raw column value.

    Returns:
        Any: ``float`` for Decimal, ISO string for datetime/time, else unchanged.
    """
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, time)):
        return value.isoformat()
    return value


def row_to_dict(columns: tuple[str, ...], row: tuple) -> dict:
    """Zip column names with a row into a JSON-safe dict.

    Args:
        columns: Column names in SELECT order.
        row: One fetched row.

    Returns:
        dict: Column -> JSON-safe value.
    """
    return {column: _to_json_safe(value) for column, value in zip(columns, row)}
