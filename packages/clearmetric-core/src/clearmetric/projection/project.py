"""Policy projection — gate and mask nodes; no kind selection."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact, Edge, Node
from clearmetric.policy import gate
from clearmetric.policy.models import PolicyRulesFile, strip_sensitive_aspects


def _apply_mask(node: Node) -> Node:
    aspects = strip_sensitive_aspects(node.aspects or {})
    aspects["_policy_masked"] = True
    return node.model_copy(update={"aspects": aspects})


def apply_policy(
    artifact: CatalogArtifact,
    *,
    identity: str,
    rules: PolicyRulesFile,
) -> CatalogArtifact:
    """Policy-gated projection: filter nodes through gate, mask sensitive aspects."""
    nodes: list[Node] = []
    allowed_ids: set[str] = set()

    for node in artifact.nodes:
        decision = gate(node=node, identity=identity, rules=rules)
        if decision in {"deny", "filter"}:
            continue
        if decision == "mask":
            nodes.append(_apply_mask(node))
        else:
            nodes.append(node)
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
        warnings=artifact.warnings,
    )


__all__ = ["apply_policy"]
