"""Small sqlglot helpers local to catalogkit-lineage."""

from __future__ import annotations

from typing import Any

import sqlglot
from catalogkit.core import normalize_identifier
from sqlglot import exp

from .errors import LineageContractError, LineageInputError


def parse_single_statement(sql: str, *, dialect: str) -> Any:
    """Parse exactly one SQL statement for lineage package analysis."""
    cleaned = (sql or "").strip()
    if not cleaned:
        raise LineageInputError("SQL input is empty.")

    try:
        statements = [
            statement
            for statement in sqlglot.parse(cleaned, read=dialect)
            if statement is not None
        ]
    except Exception as exc:  # pragma: no cover - exercised by caller failure paths
        raise LineageInputError(
            f"Failed to parse SQL with dialect {dialect!r}: {exc}"
        ) from exc

    if not statements:
        raise LineageInputError("SQL input produced no parseable statements.")
    if len(statements) != 1:
        raise LineageContractError(
            "catalogkit-lineage accepts exactly one SQL statement per project file."
        )
    return statements[0]


def list_table_references(sql: str, *, dialect: str) -> list[str]:
    """Return normalized table references while excluding local CTE names."""
    statement = parse_single_statement(sql, dialect=dialect)
    cte_names = {
        normalize_identifier(cte.alias_or_name)
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    references: list[str] = []
    seen: set[str] = set()
    for table in statement.find_all(exp.Table):
        reference = normalize_identifier(table.sql(dialect=dialect))
        if reference in cte_names or reference in seen:
            continue
        seen.add(reference)
        references.append(reference)
    return references


def detect_select_star(sql: str, *, dialect: str) -> bool:
    """Return True when the statement includes any star projection."""
    statement = parse_single_statement(sql, dialect=dialect)
    return any(isinstance(node, exp.Star) for node in statement.walk())
