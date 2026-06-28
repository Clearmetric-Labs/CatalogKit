"""Impact output emitters."""

from __future__ import annotations

import json

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core import TraversalResult
from clearmetric.graph import (
    TraversalDirection,
    render_traversal_mermaid,
    render_traversal_tree,
)


def emit_impact(
    compiled: CompiledGraph,
    result: TraversalResult,
    *,
    format: str,
    direction: TraversalDirection,
) -> str:
    if format == "json":
        payload = result.model_dump(mode="json")
        payload["derivation"] = _derivation_summary(compiled, result)
        return json.dumps(payload, indent=2, sort_keys=False)
    if format == "mermaid":
        return render_traversal_mermaid(
            result.selection_id,
            compiled.artifact,
            direction=direction,
        )
    return render_traversal_tree(
        result,
        compiled.artifact,
        direction=direction,
    )


def _derivation_summary(
    compiled: CompiledGraph,
    result: TraversalResult,
) -> list[dict[str, str | None]]:
    node_map = {node.id: node for node in compiled.artifact.nodes}
    summary: list[dict[str, str | None]] = []
    for node_id in result.related_ids:
        node = node_map.get(node_id)
        if node and node.derivation:
            summary.append(
                {
                    "id": node_id,
                    "status": node.derivation.status,
                    "confidence": node.derivation.confidence,
                }
            )
    for edge in result.traversed_edges:
        if edge.derivation:
            summary.append(
                {
                    "edge": f"{edge.source_id}->{edge.target_id}",
                    "status": edge.derivation.status,
                    "confidence": edge.derivation.confidence,
                }
            )
    return summary
