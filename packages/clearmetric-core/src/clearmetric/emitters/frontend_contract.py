"""Frontend contract serializer."""

from __future__ import annotations

from clearmetric.core.contracts import require_compiled_query_contract
from clearmetric.core.errors import CompilerError
from clearmetric.core.models import CatalogArtifact


def serialize_frontend_contract(artifact: CatalogArtifact) -> dict:
    violations: list[str] = []
    queries: list[dict] = []
    for node in artifact.nodes:
        if node.kind != "query":
            continue
        try:
            sql, contract = require_compiled_query_contract(node)
        except CompilerError as exc:
            violations.append(str(exc))
            continue
        queries.append(
            {
                "id": node.id,
                "name": node.name,
                "sql": sql,
                "parameters": contract.parameters,
            }
        )
    if violations:
        raise CompilerError("; ".join(violations))
    return {"version": "1", "queries": queries}


__all__ = ["serialize_frontend_contract"]
