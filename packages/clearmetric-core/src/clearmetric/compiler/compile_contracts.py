"""Compile SQL contracts onto query nodes."""

from __future__ import annotations

from clearmetric.core.contracts import parse_query_contract
from clearmetric.core.errors import CompilerError
from clearmetric.core.errors import ValidationError as ArtifactValidationError
from clearmetric.core.models import CatalogArtifact, Node
from clearmetric.query.parser import parse_statement


def compile_query_contracts(
    artifact: CatalogArtifact,
    *,
    dialect: str,
) -> CatalogArtifact:
    """Parse and validate query SQL; attach compiled_sql to query aspects."""
    errors: list[str] = []
    compiled_sql_by_id: dict[str, str] = {}

    for node in artifact.nodes:
        if node.kind != "query":
            continue

        try:
            contract = parse_query_contract(node.aspects)
        except ArtifactValidationError as exc:
            errors.append(f"{node.id}: invalid aspects.query: {exc}")
            continue
        if contract is None:
            errors.append(f"{node.id}: query node missing aspects.query")
            continue

        try:
            parsed = parse_statement(contract.sql, dialect=dialect)
            compiled_sql_by_id[node.id] = parsed.root_expression.sql(dialect=dialect)
        except Exception as exc:
            errors.append(f"{node.id}: query SQL compile failure: {exc}")

    if errors:
        raise CompilerError("\n".join(errors))

    if not compiled_sql_by_id:
        return artifact

    new_nodes: list[Node] = []
    for node in artifact.nodes:
        compiled_sql = compiled_sql_by_id.get(node.id)
        if compiled_sql is None:
            new_nodes.append(node)
            continue

        aspects = dict(node.aspects or {})
        query_aspect = dict(aspects.get("query") or {})
        query_aspect = {**query_aspect, "compiled_sql": compiled_sql}
        new_nodes.append(
            node.model_copy(update={"aspects": {**aspects, "query": query_aspect}})
        )

    return CatalogArtifact(
        version=artifact.version,
        nodes=new_nodes,
        edges=artifact.edges,
        warnings=artifact.warnings,
    )
