"""Contract aspect models for metric and query nodes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from .errors import GraphError
from .errors import ValidationError as ArtifactValidationError
from .ids import parse_query_selection
from .models import CatalogArtifact, Node


class MetricContract(BaseModel):
    formula: str
    unit: str | None = None
    description: str | None = None
    depends_on: list[str] = Field(default_factory=list)


class QueryContract(BaseModel):
    sql: str
    parameters: dict[str, str] = Field(default_factory=dict)
    description: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    compiled_sql: str | None = None


def parse_metric_contract(aspects: dict[str, Any] | None) -> MetricContract | None:
    if not aspects:
        return None
    raw = aspects.get("metric")
    if raw is None:
        return None
    try:
        return MetricContract.model_validate(raw)
    except ValidationError as exc:
        raise ArtifactValidationError(f"Invalid metric contract aspect: {exc}") from exc


def parse_query_contract(aspects: dict[str, Any] | None) -> QueryContract | None:
    if not aspects:
        return None
    raw = aspects.get("query")
    if raw is None:
        return None
    try:
        return QueryContract.model_validate(raw)
    except ValidationError as exc:
        raise ArtifactValidationError(f"Invalid query contract aspect: {exc}") from exc


def contract_for_node(node: Node) -> MetricContract | QueryContract | None:
    if node.kind == "metric":
        return parse_metric_contract(node.aspects)
    if node.kind == "query":
        return parse_query_contract(node.aspects)
    return None


def require_compiled_query_contract(node: Node) -> tuple[str, QueryContract]:
    """Return compiled SQL and contract; loud failure if aspect or compiled_sql missing."""
    from .errors import CompilerError

    contract = parse_query_contract(node.aspects)
    if contract is None:
        raise CompilerError(f"{node.id} missing query contract aspect")
    compiled_sql = contract.compiled_sql
    if not compiled_sql or not compiled_sql.strip():
        raise CompilerError(f"{node.id} missing compiled_sql for query execution")
    return compiled_sql, contract


def require_compiled_query_sql(node: Node) -> str:
    """Return compiled_sql for runtime execution; loud failure if missing."""
    sql, _contract = require_compiled_query_contract(node)
    return sql


def _find_query_node(artifact: CatalogArtifact, query_id: str) -> Node | None:
    node = next((item for item in artifact.nodes if item.id == query_id), None)
    if node is None or node.kind != "query":
        return None
    return node


def resolve_query_node(artifact: CatalogArtifact, selection: str) -> Node:
    """Parse selection and locate a query node; loud failure if missing."""
    node_id = parse_query_selection(selection)
    node = _find_query_node(artifact, node_id)
    if node is None:
        raise GraphError(f"query not found: {selection!r}")
    return node


def contract_dependency_violations(
    artifact: CatalogArtifact,
    *,
    node_ids: set[str] | None = None,
) -> list[str]:
    known_ids = node_ids or {node.id for node in artifact.nodes}
    violations: list[str] = []
    for node in artifact.nodes:
        try:
            contract = contract_for_node(node)
        except ArtifactValidationError as exc:
            violations.append(f"{node.id} invalid contract aspect: {exc}")
            continue
        if contract is None:
            continue
        for dep_id in contract.depends_on:
            if dep_id not in known_ids:
                violations.append(
                    f"{node.id} depends_on references missing node {dep_id!r}"
                )
    return violations


__all__ = [
    "MetricContract",
    "QueryContract",
    "contract_dependency_violations",
    "contract_for_node",
    "parse_metric_contract",
    "parse_query_contract",
    "require_compiled_query_contract",
    "require_compiled_query_sql",
    "resolve_query_node",
]
