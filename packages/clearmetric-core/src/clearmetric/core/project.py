"""Project configuration loading for ClearMetric Core."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from .errors import ProjectConfigError
from .errors import ValidationError as ArtifactValidationError
from .validate import validate_project_dict

Posture = Literal["strict", "standard", "permissive"]
WarehouseKind = Literal["information_schema", "snowflake"]

_RUNTIME_WAREHOUSE_KEYS = frozenset(
    {"execute", "query", "runtime", "connection_string"}
)


class WarehouseSource(BaseModel):
    kind: WarehouseKind
    path: str | None = None
    profile: str | None = None
    database: str | None = None
    schema_name: str | None = Field(default=None, alias="schema")

    @model_validator(mode="after")
    def _validate_kind_fields(self) -> WarehouseSource:
        if self.kind == "information_schema":
            if not self.path:
                raise ValueError(
                    "sources.warehouse.kind information_schema requires path"
                )
        elif self.kind == "snowflake":
            if not self.profile:
                raise ValueError("sources.warehouse.kind snowflake requires profile")
        return self


class DbtSource(BaseModel):
    manifest: str | None = None


class SqlSource(BaseModel):
    paths: list[str] = Field(default_factory=list)


class ProjectSources(BaseModel):
    warehouse: WarehouseSource | None = None
    dbt: DbtSource | None = None
    sql: SqlSource | None = None


class PolicyConfig(BaseModel):
    rules: str


class ClearMetricProject(BaseModel):
    version: Literal[1]
    dialect: str
    sources: ProjectSources
    posture: Posture
    policy: PolicyConfig


def load_project_config(project_dir: Path) -> ClearMetricProject:
    """Load and validate clearmetric.yaml from a project directory."""
    root = project_dir.expanduser().resolve()
    config_path = root / "clearmetric.yaml"
    if not config_path.is_file():
        raise ProjectConfigError(f"Project config not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ProjectConfigError(
            f"Project config is not valid YAML: {config_path}"
        ) from exc

    if not isinstance(raw, dict):
        raise ProjectConfigError(
            f"Project config must be a YAML mapping: {config_path}"
        )

    _reject_runtime_warehouse_keys(raw)

    try:
        validate_project_dict(raw)
        project = ClearMetricProject.model_validate(raw)
    except (ArtifactValidationError, ValidationError) as exc:
        raise ProjectConfigError(
            f"Project config failed validation: {config_path}: {exc}"
        ) from exc

    _resolve_project_paths(root, project)
    return project


def _reject_runtime_warehouse_keys(raw: dict) -> None:
    warehouse = (raw.get("sources") or {}).get("warehouse")
    if not isinstance(warehouse, dict):
        return
    runtime_keys = sorted(key for key in warehouse if key in _RUNTIME_WAREHOUSE_KEYS)
    if runtime_keys:
        raise ProjectConfigError(
            "Warehouse runtime/query execution config is not supported in v0: "
            + ", ".join(runtime_keys)
        )


def _resolve_project_paths(root: Path, project: ClearMetricProject) -> None:
    sources = project.sources
    has_source = False

    if sources.warehouse is not None:
        has_source = True
        if sources.warehouse.kind == "information_schema":
            assert sources.warehouse.path is not None
            resolved = _resolve_path(root, sources.warehouse.path)
            sources.warehouse.path = str(resolved)

    if sources.dbt is not None and sources.dbt.manifest:
        has_source = True
        resolved = _resolve_path(root, sources.dbt.manifest)
        sources.dbt.manifest = str(resolved)

    if sources.sql is not None and sources.sql.paths:
        has_source = True
        resolved_paths: list[str] = []
        for path in sources.sql.paths:
            resolved_paths.append(str(_resolve_path(root, path)))
        sources.sql.paths = resolved_paths

    if not has_source:
        raise ProjectConfigError(
            "Project must configure at least one source: warehouse, dbt.manifest, or sql.paths"
        )

    rules_path = _resolve_path(root, project.policy.rules)
    if not rules_path.is_file():
        raise ProjectConfigError(f"Policy rules file not found: {rules_path}")
    project.policy.rules = str(rules_path)


def _resolve_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.exists():
        raise ProjectConfigError(f"Configured path does not exist: {candidate}")
    return candidate
