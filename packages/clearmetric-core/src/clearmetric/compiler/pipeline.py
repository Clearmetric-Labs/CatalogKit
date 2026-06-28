"""Compile pipeline stages — wedge v1."""

from __future__ import annotations

from pathlib import Path

from clearmetric.adapters.registry import enabled_sources, ingest_all
from clearmetric.core import attach_warehouse_bindings, merge
from clearmetric.core.project import load_project_aliases, load_project_config

from .models import CompiledGraph

PIPELINE_STAGES = ("discover", "ingest", "merge", "bind")


def run_build(project_dir: Path) -> CompiledGraph:
    """Run wedge build stages through bind (no enforce)."""
    root = project_dir.expanduser().resolve()
    project = load_project_config(root)
    alias_map = load_project_aliases(project)

    ingested = ingest_all(project)
    artifacts = [artifact for _kind, artifact in ingested]
    merged = merge(*artifacts) if len(artifacts) > 1 else artifacts[0]

    warehouse_artifact = next(
        (artifact for kind, artifact in ingested if kind == "warehouse"),
        None,
    )
    if warehouse_artifact is not None:
        merged = attach_warehouse_bindings(
            merged=merged,
            warehouse_artifact=warehouse_artifact,
            alias_map=alias_map,
        )

    return CompiledGraph(
        artifact=merged,
        project=project,
        project_dir=root,
        sources_run=enabled_sources(project),
    )
