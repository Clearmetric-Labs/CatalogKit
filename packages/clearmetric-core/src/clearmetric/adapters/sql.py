"""SQL folder ingestion adapter."""

from __future__ import annotations

from clearmetric.core import CatalogArtifact, merge
from clearmetric.core.errors import AdapterError
from clearmetric.core.project import ClearMetricProject
from clearmetric.lineage import (
    LineageError,
    build_catalog_artifact_from_project,
    load_project,
)


def ingest_sql(project: ClearMetricProject) -> CatalogArtifact:
    paths = project.sources.sql.paths if project.sources.sql else []
    if not paths:
        raise AdapterError("sql source is not configured")
    artifacts: list[CatalogArtifact] = []
    for path in paths:
        try:
            loaded = load_project(path, dialect=project.dialect)
            artifacts.append(
                build_catalog_artifact_from_project(loaded, dialect=project.dialect)
            )
        except LineageError as exc:
            raise AdapterError(f"sql ingestion failed for {path}: {exc}") from exc
    if len(artifacts) == 1:
        return artifacts[0]
    return merge(*artifacts)
