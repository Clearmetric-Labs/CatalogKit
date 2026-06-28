"""Impact traversal over a compiled graph artifact."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact, TraversalResult, parse_impact_selection
from clearmetric.core.errors import GraphError

from .subjects import impact_dataset_name, impact_edge_kind, warnings_for_subject
from .traverse import TraversalDirection, build_traversal_subgraph, walk_related
from .view import GraphView, view_of


def _require_impact_selection(
    view: GraphView,
    *,
    selection: str,
    selection_id: str,
) -> None:
    if view.has_node(selection_id):
        return
    raise GraphError(f"Selection {selection!r} does not match any graph node.")


def _trace_from_artifact(
    artifact: CatalogArtifact,
    *,
    selection: str,
    direction: TraversalDirection,
) -> TraversalResult:
    selection_id = parse_impact_selection(selection)
    view = view_of(artifact)
    _require_impact_selection(view, selection=selection, selection_id=selection_id)
    edge_kind = impact_edge_kind(selection_id)
    _node_ids, traversed_edges = build_traversal_subgraph(
        view,
        selection_id,
        direction=direction,
        edge_kind=edge_kind,
    )
    return TraversalResult(
        selection=selection,
        selection_id=selection_id,
        related_ids=walk_related(
            view, selection_id, direction=direction, edge_kind=edge_kind
        ),
        traversed_edges=traversed_edges,
        warnings=warnings_for_subject(
            artifact,
            selection_id,
            dataset_name=impact_dataset_name(selection_id),
        ),
    )


def trace_upstream_from_artifact(
    artifact: CatalogArtifact,
    *,
    selection: str,
) -> TraversalResult:
    return _trace_from_artifact(artifact, selection=selection, direction="upstream")


def trace_downstream_from_artifact(
    artifact: CatalogArtifact,
    *,
    selection: str,
) -> TraversalResult:
    return _trace_from_artifact(artifact, selection=selection, direction="downstream")
