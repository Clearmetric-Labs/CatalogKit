"""Public package surface for clearmetric.lineage — SQL/dbt artifact build."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact

from ._version import __version__
from .api import (
    build_catalog_artifact_from_project,
    build_lineage_map_from_project,
    render_json,
    render_text,
)
from .errors import LineageContractError, LineageError, LineageInputError
from .loaders import ProjectInput, load_project
from .models import LineageMap, LineageSummary

__all__ = [
    "__version__",
    "build_catalog_artifact_from_project",
    "build_lineage_map_from_project",
    "CatalogArtifact",
    "LineageContractError",
    "LineageError",
    "LineageInputError",
    "LineageMap",
    "LineageSummary",
    "ProjectInput",
    "load_project",
    "render_json",
    "render_text",
]
