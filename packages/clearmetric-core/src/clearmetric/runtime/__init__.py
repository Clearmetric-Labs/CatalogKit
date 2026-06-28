"""DuckDB query execution (experimental lab harness)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from clearmetric.core.contracts import require_compiled_query_sql
from clearmetric.core.errors import QueryExecutionError
from clearmetric.policy import require_allow
from clearmetric.policy.models import PolicyRulesFile

if TYPE_CHECKING:
    from clearmetric.core.models import Node


def execute_gated_query(
    node: Node,
    *,
    identity: str,
    rules: PolicyRulesFile,
    seed_sql_path: Path | None = None,
) -> list[dict]:
    """Gate a query node, require compiled SQL, then execute via DuckDB."""
    require_allow(node=node, identity=identity, rules=rules)
    sql = require_compiled_query_sql(node)
    return execute_query(sql, seed_sql_path=seed_sql_path)


def execute_query(
    sql: str,
    *,
    seed_sql_path: Path | None = None,
    connection: Any = None,
) -> list[dict]:
    """Execute SQL against DuckDB and return rows as dicts."""
    try:
        import duckdb
    except ImportError as exc:
        raise QueryExecutionError(
            "duckdb is required for query execution: pip install 'clearmetric-core[runtime]'"
        ) from exc

    owns_connection = connection is None
    conn = connection or duckdb.connect(database=":memory:")
    try:
        if seed_sql_path is not None and seed_sql_path.is_file():
            conn.execute(seed_sql_path.read_text(encoding="utf-8"))
        relation = conn.execute(sql)
        if relation.description is None:
            raise QueryExecutionError("query returned no result columns")
        columns = [col[0] for col in relation.description]
        return [dict(zip(columns, row, strict=True)) for row in relation.fetchall()]
    except QueryExecutionError:
        raise
    except Exception as exc:
        raise QueryExecutionError(f"query execution failed: {exc}") from exc
    finally:
        if owns_connection:
            conn.close()


__all__ = ["execute_gated_query", "execute_query"]
