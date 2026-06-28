"""Structural graph checks."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact

from .models import Finding


def check_unique_node_ids(artifact: CatalogArtifact) -> list[Finding]:
    seen: set[str] = set()
    findings: list[Finding] = []
    for node in artifact.nodes:
        if node.id in seen:
            findings.append(
                Finding(
                    check_id="check.unique_node_ids",
                    node_id=node.id,
                    severity="error",
                    message=f"Duplicate node id {node.id!r}",
                    fix_hint="Ensure each logical node has a unique canonical id",
                )
            )
        seen.add(node.id)
    return findings


def check_edges_resolve(artifact: CatalogArtifact) -> list[Finding]:
    node_ids = {node.id for node in artifact.nodes}
    findings: list[Finding] = []
    for edge in artifact.edges:
        if edge.source_id not in node_ids:
            findings.append(
                Finding(
                    check_id="check.edges_resolve",
                    node_id=edge.source_id,
                    severity="error",
                    message=(
                        f"Edge {edge.kind} references missing source node "
                        f"{edge.source_id!r}"
                    ),
                    fix_hint="Remove or repair dangling edge endpoints",
                )
            )
        if edge.target_id not in node_ids:
            findings.append(
                Finding(
                    check_id="check.edges_resolve",
                    node_id=edge.target_id,
                    severity="error",
                    message=(
                        f"Edge {edge.kind} references missing target node "
                        f"{edge.target_id!r}"
                    ),
                    fix_hint="Remove or repair dangling edge endpoints",
                )
            )
    return findings
