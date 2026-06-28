"""Impact orchestration."""

from __future__ import annotations

from pathlib import Path

from clearmetric.core import TraversalResult
from clearmetric.core.models import CatalogArtifact
from clearmetric.graph import (
    TraversalDirection,
    trace_downstream_from_artifact,
    trace_upstream_from_artifact,
    view_of,
)
from clearmetric.policy import (
    filter_allow_only_ids,
    load_rules,
    require_allow,
    require_gated_identity,
)

from .compile import compile
from .models import CompiledGraph


def _filter_traversal_by_identity(
    result: TraversalResult,
    artifact: CatalogArtifact,
    *,
    identity: str,
    rules_path: str | Path,
) -> TraversalResult:
    rules = load_rules(rules_path)
    view = view_of(artifact)
    selection_node = view.node(result.selection_id)
    require_allow(node=selection_node, identity=identity, rules=rules)
    filtered_ids = filter_allow_only_ids(
        node_ids=result.related_ids,
        resolve_node=view.node,
        identity=identity,
        rules=rules,
    )
    return result.model_copy(update={"related_ids": filtered_ids})


def impact(
    project_dir: Path,
    *,
    selection: str,
    direction: TraversalDirection,
    identity: str | None = None,
) -> tuple[CompiledGraph, TraversalResult]:
    """Trace lineage impact on the full enforced graph."""
    compiled = compile(project_dir)
    artifact = compiled.artifact

    if direction == "upstream":
        result = trace_upstream_from_artifact(artifact, selection=selection)
    else:
        result = trace_downstream_from_artifact(artifact, selection=selection)

    if identity is not None:
        identity = require_gated_identity(identity)
        result = _filter_traversal_by_identity(
            result,
            artifact,
            identity=identity,
            rules_path=compiled.project.policy.rules,
        )

    return compiled, result
