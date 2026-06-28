"""dbt manifest ingestion adapter."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact
from clearmetric.core.errors import AdapterError
from clearmetric.core.project import ClearMetricProject
from clearmetric.lineage import (
    LineageError,
    build_catalog_artifact_from_project,
    load_project,
)


def ingest_dbt(project: ClearMetricProject) -> CatalogArtifact:
    manifest = project.sources.dbt.manifest if project.sources.dbt else None
    if not manifest:
        raise AdapterError("dbt source is not configured")
    try:
        loaded = load_project(manifest, dialect=project.dialect)
        return build_catalog_artifact_from_project(loaded, dialect=project.dialect)
    except LineageError as exc:
        raise AdapterError(f"dbt ingestion failed: {exc}") from exc
