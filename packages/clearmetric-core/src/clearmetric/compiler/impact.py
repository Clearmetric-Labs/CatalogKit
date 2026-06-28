"""Impact orchestration."""

from __future__ import annotations

from pathlib import Path

from clearmetric.core import TraversalResult
from clearmetric.graph import (
    TraversalDirection,
    trace_downstream_from_artifact,
    trace_upstream_from_artifact,
    view_of,
)
from clearmetric.policy import gate, load_rules

from .compile import compile
from .models import CompiledGraph


def _filter_traversal_by_identity(
    result: TraversalResult,
    artifact,
    *,
    identity: str,
    rules_path: str | Path,
) -> TraversalResult:
    rules = load_rules(rules_path)
    view = view_of(artifact)
    filtered_ids: list[str] = []
    for node_id in result.related_ids:
        node = view.node(node_id)
        decision = gate(node=node, identity=identity, rules=rules)
        if decision not in {"deny", "filter"}:
            filtered_ids.append(node_id)
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
        result = _filter_traversal_by_identity(
            result,
            artifact,
            identity=identity,
            rules_path=compiled.project.policy.rules,
        )

    return compiled, result
