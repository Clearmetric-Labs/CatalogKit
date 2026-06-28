"""Policy projection — gate and mask nodes; no kind selection."""

from __future__ import annotations

from clearmetric.core.models import (
    CatalogArtifact,
    Edge,
    Node,
    filter_warnings_for_ids,
)
from clearmetric.policy import gate
from clearmetric.policy.models import PolicyRulesFile, strip_sensitive_aspects


def _consumer_safe_node(node: Node, *, masked: bool) -> Node:
    aspects = strip_sensitive_aspects(node.aspects or {})
    if masked:
        aspects["_policy_masked"] = True
    return node.model_copy(update={"aspects": aspects})


def apply_policy(
    artifact: CatalogArtifact,
    *,
    identity: str,
    rules: PolicyRulesFile,
) -> CatalogArtifact:
    """Policy-gated projection: consumer-safe nodes and filtered warnings."""
    nodes: list[Node] = []
    allowed_ids: set[str] = set()

    for node in artifact.nodes:
        decision = gate(node=node, identity=identity, rules=rules)
        if decision in {"deny", "filter"}:
            continue
        nodes.append(_consumer_safe_node(node, masked=decision == "mask"))
        allowed_ids.add(node.id)

    edges: list[Edge] = [
        edge
        for edge in artifact.edges
        if edge.source_id in allowed_ids and edge.target_id in allowed_ids
    ]
    return CatalogArtifact(
        version=artifact.version,
        nodes=nodes,
        edges=edges,
        warnings=filter_warnings_for_ids(artifact.warnings, allowed_ids),
    )


__all__ = ["apply_policy"]
