"""DuckDB query execution (experimental lab harness)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from clearmetric.core.contracts import require_compiled_query_sql, resolve_query_node
from clearmetric.core.errors import QueryExecutionError
from clearmetric.policy import load_rules, require_allow

if TYPE_CHECKING:
    from clearmetric.core.models import CatalogArtifact


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
        if seed_sql_path is not None:
            if not seed_sql_path.is_file():
                raise QueryExecutionError(f"fixture seed not found: {seed_sql_path}")
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


def execute_project_query(
    artifact: CatalogArtifact,
    *,
    identity: str,
    rules_path: str | Path,
    query_selection: str,
    project_dir: Path,
) -> list[dict]:
    """Gate, resolve, and execute a project query contract via DuckDB fixtures."""
    rules = load_rules(rules_path)
    node = resolve_query_node(artifact, query_selection)
    require_allow(node=node, identity=identity, rules=rules)
    sql = require_compiled_query_sql(node)
    return execute_query(sql, seed_sql_path=project_dir / "fixtures" / "seed.sql")


__all__ = ["execute_project_query", "execute_query"]
