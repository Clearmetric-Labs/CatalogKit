"""Frontend contract emitter."""

from __future__ import annotations

import json

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core.contracts import require_compiled_query_contract
from clearmetric.core.errors import CompilerError
from clearmetric.policy.models import PolicyRulesFile
from clearmetric.projection import project_for_emit


def emit_frontend_contract(
    compiled: CompiledGraph,
    *,
    identity: str,
    rules: PolicyRulesFile,
) -> str:
    gated = project_for_emit(
        compiled.artifact,
        identity=identity,
        rules=rules,
    )
    contracts: list[dict] = []
    violations: list[str] = []
    for node in gated.nodes:
        if node.kind != "query":
            continue
        try:
            sql, contract = require_compiled_query_contract(node)
        except CompilerError as exc:
            violations.append(str(exc))
            continue
        contracts.append(
            {
                "id": node.id,
                "name": node.name,
                "sql": sql,
                "parameters": contract.parameters,
            }
        )
    if violations:
        raise CompilerError("; ".join(violations))
    return json.dumps({"version": "1", "queries": contracts}, indent=2, sort_keys=False)
