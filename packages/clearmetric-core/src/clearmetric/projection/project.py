"""Projection filtering."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact, Edge, Node
from clearmetric.policy.evaluate import evaluate
from clearmetric.policy.models import PolicyRulesFile


def project_graph(
    artifact: CatalogArtifact,
    *,
    identity: str,
    rules: PolicyRulesFile,
) -> CatalogArtifact:
    allowed_ids = {
        node.id
        for node in artifact.nodes
        if evaluate(node=node, identity=identity, rules=rules) != "deny"
    }
    nodes: list[Node] = [node for node in artifact.nodes if node.id in allowed_ids]
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
