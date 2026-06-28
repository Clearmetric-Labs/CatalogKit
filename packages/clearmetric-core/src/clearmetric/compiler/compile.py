"""Compile orchestration."""

from __future__ import annotations

from pathlib import Path

from clearmetric.adapters.registry import enabled_sources, ingest_all
from clearmetric.adapters.warehouse import compare_warehouse_metadata
from clearmetric.cleaner import enforce_structural_checks
from clearmetric.core import merge
from clearmetric.core.project import load_project_config
from clearmetric.policy import load_rules, validate_security_floor

from .models import CompiledGraph


def compile(project_dir: Path) -> CompiledGraph:
    root = project_dir.expanduser().resolve()
    project = load_project_config(root)
    load_rules(Path(project.policy.rules))

    ingested = ingest_all(project)
    artifacts = [artifact for _kind, artifact in ingested]
    merged = merge(*artifacts) if len(artifacts) > 1 else artifacts[0]

    warehouse_artifact = next(
        (artifact for kind, artifact in ingested if kind == "warehouse"),
        None,
    )
    if warehouse_artifact is not None:
        drift = compare_warehouse_metadata(merged, warehouse_artifact)
        if drift:
            merged = merged.model_copy(update={"warnings": [*merged.warnings, *drift]})

    enforce_structural_checks(merged)
    validate_security_floor(merged)
    return CompiledGraph(
        artifact=merged,
        project=project,
        project_dir=root,
        sources_run=enabled_sources(project),
    )
