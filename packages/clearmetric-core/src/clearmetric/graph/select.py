"""Graph selection — slice nodes and edges by selector or kind set."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact, Edge, Node, Warning

from .selector import SelectorPredicate, matches_selector, parse_selector
from .view import GraphView


def _filter_warnings(
    warnings: list[Warning],
    allowed_ids: set[str],
    *,
    clear_warnings: bool,
) -> list[Warning]:
    if clear_warnings:
        return []
    filtered: list[Warning] = []
    for warning in warnings:
        if warning.subject_id is None:
            filtered.append(warning)
        elif warning.subject_id in allowed_ids:
            filtered.append(warning)
    return filtered


def _artifact_from_nodes(
    view: GraphView,
    nodes: list[Node],
    *,
    clear_warnings: bool,
) -> CatalogArtifact:
    allowed_ids = {node.id for node in nodes}
    edges: list[Edge] = [
        edge
        for edge in view.edges()
        if edge.source_id in allowed_ids and edge.target_id in allowed_ids
    ]
    warnings = _filter_warnings(
        view.artifact.warnings, allowed_ids, clear_warnings=clear_warnings
    )
    return CatalogArtifact(
        version=view.artifact.version,
        nodes=nodes,
        edges=edges,
        warnings=warnings,
    )


def select(view: GraphView, predicate: str | SelectorPredicate) -> CatalogArtifact:
    """Return a subgraph whose nodes match the selector; prune edges to the slice."""
    pred = parse_selector(predicate) if isinstance(predicate, str) else predicate
    nodes = [node for node in view.nodes() if matches_selector(pred, node)]
    return _artifact_from_nodes(view, nodes, clear_warnings=False)


def select_kinds(
    view: GraphView,
    kinds: frozenset[str],
    *,
    clear_warnings: bool = False,
) -> CatalogArtifact:
    """Return a subgraph containing only nodes whose kind is in kinds."""
    nodes = [node for node in view.nodes() if node.kind in kinds]
    return _artifact_from_nodes(view, nodes, clear_warnings=clear_warnings)


__all__ = ["select", "select_kinds"]
