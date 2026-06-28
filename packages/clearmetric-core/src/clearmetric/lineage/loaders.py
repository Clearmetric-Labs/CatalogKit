"""Project input loaders for clearmetric-core."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from clearmetric.core import leaf_name, normalize_identifier

from .errors import LineageInputError
from .sql_analyzer import list_table_references

ProjectDatasetKind = Literal["local", "root"]
InputKind = Literal["dbt_manifest", "sql_folder"]


@dataclass(frozen=True)
class ProjectDataset:
    name: str
    kind: ProjectDatasetKind
    sql: str | None
    dependency_names: tuple[str, ...]
    declared_columns: tuple[str, ...]
    evidence_file: str | None
    unique_id: str | None = None
    package_name: str | None = None
    manifest_name: str | None = None
    alias: str | None = None
    database: str | None = None
    schema_name: str | None = None
    relation_name: str | None = None
    resource_type: str | None = None


@dataclass(frozen=True)
class ManifestCompileReport:
    models_total: int
    models_with_compiled_sql: int
    models_missing_compiled_sql: tuple[str, ...]


@dataclass(frozen=True)
class ProjectInput:
    input_kind: InputKind
    label: str
    datasets: dict[str, ProjectDataset]
    manifest_compile_report: ManifestCompileReport | None = None

    def local_dataset_names(self) -> set[str]:
        return {
            dataset.name
            for dataset in self.datasets.values()
            if dataset.kind == "local"
        }

    def root_schema(self) -> dict[str, dict[str, str]]:
        schema: dict[str, dict[str, str]] = {}
        for dataset in self.datasets.values():
            if dataset.kind != "root" or not dataset.declared_columns:
                continue
            schema[dataset.name] = {
                column_name: "text" for column_name in dataset.declared_columns
            }
        return schema

    def sources_for(self, dataset_name: str) -> dict[str, str]:
        local_names = self.local_dataset_names()
        visited: set[str] = set()
        stack = list(self.datasets[dataset_name].dependency_names)
        while stack:
            dependency_name = stack.pop()
            if dependency_name not in local_names or dependency_name in visited:
                continue
            visited.add(dependency_name)
            stack.extend(self.datasets[dependency_name].dependency_names)
        return {
            dependency_name: self.datasets[dependency_name].sql or ""
            for dependency_name in sorted(visited)
        }


def load_project(path: str | Path, *, dialect: str) -> ProjectInput:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise LineageInputError(f"Project input does not exist: {target}")
    if target.is_file():
        if target.name != "manifest.json":
            raise LineageInputError(
                "clearmetric-core file input must be a dbt manifest.json."
            )
        return _load_manifest_project(target)
    if target.is_dir():
        return _load_sql_folder_project(target, dialect=dialect)
    raise LineageInputError(f"Unsupported project input path: {target}")


def _load_manifest_project(path: Path) -> ProjectInput:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LineageInputError(f"Manifest is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise LineageInputError(f"Manifest root must be an object: {path}")
    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, dict):
        raise LineageInputError(f"Manifest is missing a nodes object: {path}")

    node_payloads = _collect_manifest_node_payloads(payload)
    unique_id_to_identity = _build_unique_id_to_identity(node_payloads)

    datasets: dict[str, ProjectDataset] = {}
    models_total = 0
    models_with_compiled_sql = 0
    for unique_id, node_payload in node_payloads.items():
        resource_type = str(node_payload.get("resource_type") or "").strip().lower()
        if resource_type not in {"model", "seed", "source"}:
            continue
        identity = unique_id_to_identity[unique_id]
        dbt_fields = _dbt_metadata_fields(node_payload, unique_id=unique_id)
        if resource_type == "model":
            models_total += 1
            sql = _read_compiled_sql(path, node_payload)
            models_with_compiled_sql += 1
            depends_on = _resolve_manifest_dependencies(
                node_payload,
                unique_id_to_identity=unique_id_to_identity,
            )
            datasets[identity] = ProjectDataset(
                name=identity,
                kind="local",
                sql=sql,
                dependency_names=depends_on,
                declared_columns=_columns_from_manifest_node(node_payload),
                evidence_file=_compiled_path_label(node_payload),
                **dbt_fields,
            )
        else:
            datasets[identity] = ProjectDataset(
                name=identity,
                kind="root",
                sql=None,
                dependency_names=(),
                declared_columns=_columns_from_manifest_node(node_payload),
                evidence_file=None,
                **dbt_fields,
            )

    if not datasets:
        raise LineageInputError(f"Manifest produced no usable datasets: {path}")

    datasets = _ensure_root_dependencies(datasets)

    project_name = _manifest_project_name(payload)
    label = project_name or path.parent.name
    compile_report = ManifestCompileReport(
        models_total=models_total,
        models_with_compiled_sql=models_with_compiled_sql,
        models_missing_compiled_sql=(),
    )
    return ProjectInput(
        input_kind="dbt_manifest",
        label=label,
        datasets=datasets,
        manifest_compile_report=compile_report,
    )


def _collect_manifest_node_payloads(payload: dict) -> dict[str, dict]:
    collected: dict[str, dict] = {}
    for section in ("nodes", "sources"):
        section_payload = payload.get(section)
        if section_payload is None and section == "sources":
            continue
        if not isinstance(section_payload, dict):
            raise LineageInputError(f"Manifest {section!r} section must be an object")
        for unique_id, node_payload in section_payload.items():
            if not isinstance(node_payload, dict):
                raise LineageInputError(
                    f"Manifest {section!r} entry {unique_id!r} must be an object"
                )
            collected[str(unique_id)] = node_payload
    return collected


def _manifest_project_name(payload: dict) -> str:
    metadata = payload.get("metadata", {})
    if metadata is None:
        return ""
    if not isinstance(metadata, dict):
        raise LineageInputError("Manifest metadata must be an object")
    return str(metadata.get("project_name") or "").strip()


def _build_unique_id_to_identity(node_payloads: dict[str, dict]) -> dict[str, str]:
    unique_id_to_identity: dict[str, str] = {}
    identity_to_unique_id: dict[str, str] = {}
    for unique_id, node_payload in node_payloads.items():
        resource_type = str(node_payload.get("resource_type") or "").strip().lower()
        if resource_type not in {"model", "seed", "source"}:
            continue
        identity = resolve_dbt_dataset_identity(node_payload)
        existing = identity_to_unique_id.get(identity)
        if existing is not None and existing != unique_id:
            raise LineageInputError(f"Duplicate dbt dataset identity {identity!r}")
        unique_id_to_identity[unique_id] = identity
        identity_to_unique_id[identity] = unique_id
    return unique_id_to_identity


def resolve_dbt_dataset_identity(node_payload: dict) -> str:
    relation_name = str(node_payload.get("relation_name") or "").strip()
    if relation_name:
        return normalize_identifier(relation_name)
    database = str(node_payload.get("database") or "").strip()
    schema = str(node_payload.get("schema") or "").strip()
    alias = str(node_payload.get("alias") or "").strip()
    name = str(node_payload.get("name") or "").strip()
    if database and schema and alias:
        return normalize_identifier(f"{database}.{schema}.{alias}")
    if schema and alias:
        return normalize_identifier(f"{schema}.{alias}")
    if alias:
        return normalize_identifier(alias)
    if database and schema and name:
        return normalize_identifier(f"{database}.{schema}.{name}")
    if schema and name:
        return normalize_identifier(f"{schema}.{name}")
    if name:
        return normalize_identifier(name)
    raise LineageInputError("dbt manifest node is missing a usable identity")


def dbt_aspect_for_dataset(dataset: ProjectDataset) -> dict[str, str] | None:
    if dataset.unique_id is None:
        return None
    aspect = {
        "unique_id": dataset.unique_id,
        "package_name": dataset.package_name or "",
        "name": dataset.manifest_name or leaf_name(dataset.name),
        "alias": dataset.alias or "",
        "database": dataset.database or "",
        "schema": dataset.schema_name or "",
        "relation_name": dataset.relation_name or "",
        "resource_type": dataset.resource_type or "",
    }
    return {key: value for key, value in aspect.items() if value}


def _dbt_metadata_fields(
    node_payload: dict, *, unique_id: str
) -> dict[str, str | None]:
    return {
        "unique_id": unique_id,
        "package_name": _optional_string(node_payload.get("package_name")),
        "manifest_name": _optional_string(node_payload.get("name")),
        "alias": _optional_string(node_payload.get("alias")),
        "database": _optional_string(node_payload.get("database")),
        "schema_name": _optional_string(node_payload.get("schema")),
        "relation_name": _optional_string(node_payload.get("relation_name")),
        "resource_type": _optional_string(node_payload.get("resource_type")),
    }


def _optional_string(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _resolve_manifest_dependencies(
    node_payload: dict,
    *,
    unique_id_to_identity: dict[str, str],
) -> tuple[str, ...]:
    depends_on: list[str] = []
    for dependency_unique_id in _manifest_dependency_ids(node_payload):
        resolved = unique_id_to_identity.get(dependency_unique_id)
        if resolved is None:
            if dependency_unique_id.startswith("source."):
                resolved = normalize_identifier(dependency_unique_id.split(".")[-1])
            else:
                raise LineageInputError(
                    f"Unresolved dbt dependency {dependency_unique_id!r}"
                )
        depends_on.append(resolved)
    return tuple(depends_on)


def _manifest_dependency_ids(node_payload: dict) -> tuple[str, ...]:
    depends_on = node_payload.get("depends_on", {})
    if depends_on is None:
        return ()
    if not isinstance(depends_on, dict):
        raise LineageInputError("Manifest depends_on must be an object")
    nodes = depends_on.get("nodes", [])
    if nodes is None:
        return ()
    if not isinstance(nodes, list):
        raise LineageInputError("Manifest depends_on.nodes must be a list")

    dependency_ids: list[str] = []
    for dependency in nodes:
        if not isinstance(dependency, str):
            raise LineageInputError("Manifest dependency ids must be strings")
        dependency_unique_id = dependency.strip()
        if dependency_unique_id:
            dependency_ids.append(dependency_unique_id)
    return tuple(dependency_ids)


def _ensure_root_dependencies(
    datasets: dict[str, ProjectDataset],
) -> dict[str, ProjectDataset]:
    updated = dict(datasets)
    for dataset in list(updated.values()):
        if dataset.kind != "local":
            continue
        for dependency_name in dataset.dependency_names:
            if dependency_name in updated:
                continue
            updated[dependency_name] = ProjectDataset(
                name=dependency_name,
                kind="root",
                sql=None,
                dependency_names=(),
                declared_columns=(),
                evidence_file=None,
            )
    return updated


def _read_compiled_sql(manifest_path: Path, node_payload: dict) -> str:
    compiled_code = str(node_payload.get("compiled_code") or "").strip()
    if compiled_code:
        return compiled_code
    compiled_sql = str(node_payload.get("compiled_sql") or "").strip()
    if compiled_sql:
        return compiled_sql

    compiled_path = str(node_payload.get("compiled_path") or "").strip()
    if compiled_path:
        candidate = _resolve_manifest_relative_path(manifest_path, compiled_path)
        sql = candidate.read_text(encoding="utf-8").strip()
        if sql:
            return sql

    raise LineageInputError(
        f"Manifest model {node_payload.get('name')!r} is missing compiled SQL."
    )


def _compiled_path_label(node_payload: dict) -> str | None:
    compiled_path = str(node_payload.get("compiled_path") or "").strip()
    if compiled_path:
        return compiled_path
    name = str(node_payload.get("name") or "").strip()
    return f"{name}.sql" if name else None


def _resolve_manifest_relative_path(manifest_path: Path, relative_path: str) -> Path:
    manifest_root = manifest_path.parent.resolve()
    candidate = (manifest_root / relative_path).resolve()
    if not candidate.is_relative_to(manifest_root):
        raise LineageInputError(
            f"Manifest compiled_path escapes the manifest directory: {relative_path!r}"
        )
    if not candidate.is_file():
        raise LineageInputError(
            f"Manifest compiled_path is not a readable file: {relative_path!r}"
        )
    return candidate


def _columns_from_manifest_node(node_payload: dict) -> tuple[str, ...]:
    columns = node_payload.get("columns", {})
    if columns is None:
        return ()
    if not isinstance(columns, dict):
        raise LineageInputError("Manifest columns must be an object")

    column_names: list[str] = []
    for column_name, column_payload in columns.items():
        if not isinstance(column_payload, dict):
            raise LineageInputError(
                f"Manifest column entry {column_name!r} must be an object"
            )
        name = str(column_payload.get("name") or "").strip()
        if name:
            column_names.append(name)
    return tuple(column_names)


def _load_sql_folder_project(path: Path, *, dialect: str) -> ProjectInput:
    sql_files = sorted(path.rglob("*.sql"))
    if not sql_files:
        raise LineageInputError(f"SQL folder contains no .sql files: {path}")

    datasets: dict[str, ProjectDataset] = {}
    raw_sql_by_name: dict[str, str] = {}
    for sql_file in sql_files:
        relative_parts = sql_file.relative_to(path).with_suffix("").parts
        dataset_name = normalize_identifier(".".join(relative_parts))
        if dataset_name in datasets:
            raise LineageInputError(
                f"SQL folder produced duplicate dataset name {dataset_name!r}."
            )
        sql = sql_file.read_text(encoding="utf-8").strip()
        if not sql:
            raise LineageInputError(f"SQL file is empty: {sql_file}")
        raw_sql_by_name[dataset_name] = sql
        datasets[dataset_name] = ProjectDataset(
            name=dataset_name,
            kind="local",
            sql=sql,
            dependency_names=(),
            declared_columns=(),
            evidence_file=str(sql_file.relative_to(path)),
        )

    local_names = set(raw_sql_by_name)
    for dataset_name, sql in raw_sql_by_name.items():
        try:
            dependency_names = sorted(
                {
                    normalize_identifier(reference)
                    for reference in list_table_references(sql, dialect=dialect)
                    if normalize_identifier(reference) in local_names
                }
            )
        except LineageInputError:
            # Unparseable files still load; build emits lineage_resolution_failed per dataset.
            dependency_names = ()
        current = datasets[dataset_name]
        datasets[dataset_name] = ProjectDataset(
            name=current.name,
            kind=current.kind,
            sql=current.sql,
            dependency_names=tuple(dependency_names),
            declared_columns=current.declared_columns,
            evidence_file=current.evidence_file,
        )

    return ProjectInput(
        input_kind="sql_folder",
        label=path.name,
        datasets=datasets,
    )
