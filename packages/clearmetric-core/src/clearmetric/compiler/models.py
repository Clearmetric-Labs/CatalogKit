"""Compiler models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clearmetric.core.models import CatalogArtifact
from clearmetric.core.project import ClearMetricProject


@dataclass(frozen=True)
class CompiledGraph:
    artifact: CatalogArtifact
    project: ClearMetricProject
    project_dir: Path
    sources_run: list[str]


@dataclass(frozen=True)
class ResolvedSource:
    kind: str
    path: str | None = None


@dataclass(frozen=True)
class DiscoverReport:
    config_path: str
    dialect: str
    sources: list[ResolvedSource]
