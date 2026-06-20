"""Artifact assembly for catalogkit-lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from catalogkit.core import (
    CatalogArtifact,
    Edge,
    Evidence,
    Node,
    Warning,
    column_id,
    leaf_name,
    merge,
    schema_name,
    split_qualified_identifier,
    table_id,
)
from sqlglot.lineage import Node as SqlglotLineageNode
from sqlglot.lineage import lineage

from .errors import LineageContractError, LineageInputError
from .loaders import ProjectDataset, ProjectInput
from .models import LineageMap, LineageSummary, TraversalResult
from .sql_analyzer import detect_select_star


@dataclass(frozen=True)
class BuiltLineage:
    artifact: CatalogArtifact
    summary: LineageSummary


def build_catalog_artifact_from_project(
    project: ProjectInput,
    *,
    dialect: str,
) -> CatalogArtifact:
    return _build_lineage(project, dialect=dialect).artifact


def build_lineage_map_from_project(
    project: ProjectInput,
    *,
    dialect: str,
) -> LineageMap:
    built = _build_lineage(project, dialect=dialect)
    return LineageMap(
        version=built.artifact.version,
        summary=built.summary,
        nodes=built.artifact.nodes,
        edges=built.artifact.edges,
        warnings=built.artifact.warnings,
    )


def trace_upstream_from_project(
    project: ProjectInput,
    *,
    dialect: str,
    selection: str,
) -> TraversalResult:
    artifact = build_catalog_artifact_from_project(project, dialect=dialect)
    selection_id = _selection_to_column_id(selection)
    _require_column_selection(artifact, selection=selection, selection_id=selection_id)
    return TraversalResult(
        selection=selection,
        selection_id=selection_id,
        related_ids=_walk_upstream(artifact, selection_id),
    )


def trace_downstream_from_project(
    project: ProjectInput,
    *,
    dialect: str,
    selection: str,
) -> TraversalResult:
    artifact = build_catalog_artifact_from_project(project, dialect=dialect)
    selection_id = _selection_to_column_id(selection)
    _require_column_selection(artifact, selection=selection, selection_id=selection_id)
    return TraversalResult(
        selection=selection,
        selection_id=selection_id,
        related_ids=_walk_downstream(artifact, selection_id),
    )


def build_openlineage_export_from_project(
    project: ProjectInput,
    *,
    dialect: str,
) -> dict[str, Any]:
    artifact = build_catalog_artifact_from_project(project, dialect=dialect)
    column_edges = [edge for edge in artifact.edges if edge.kind == "derives_from"]
    input_fields_by_output: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    for edge in column_edges:
        output_dataset, output_column = _column_selection_from_id(edge.source_id)
        input_dataset, input_column = _column_selection_from_id(edge.target_id)
        input_fields_by_output.setdefault((output_dataset, output_column), set()).add(
            ("catalogkit", input_dataset, input_column)
        )

    export_entries = [
        {
            "dataset": output_dataset,
            "column": output_column,
            "inputFields": [
                {
                    "namespace": namespace,
                    "name": input_dataset,
                    "field": input_column,
                }
                for namespace, input_dataset, input_column in sorted(input_fields)
            ],
        }
        for (output_dataset, output_column), input_fields in sorted(
            input_fields_by_output.items()
        )
    ]

    datasets = [
        {
            "namespace": "catalogkit",
            "name": node.qualified_name or node.name,
            "kind": node.kind,
        }
        for node in sorted(
            artifact.nodes, key=lambda item: item.qualified_name or item.name
        )
        if node.kind == "table"
    ]

    return {
        "job": {
            "namespace": "catalogkit",
            "name": project.label,
        },
        "datasets": datasets,
        "columnLineage": export_entries,
    }


def _build_lineage(project: ProjectInput, *, dialect: str) -> BuiltLineage:
    nodes_by_id: dict[str, Node] = {}
    edges: list[Edge] = []
    warnings: list[Warning] = []

    for dataset in project.datasets.values():
        _add_dataset_node(nodes_by_id, dataset)
        for column_name in dataset.declared_columns:
            _add_column_node(
                nodes_by_id, dataset.name, column_name, dataset.evidence_file
            )

    for dataset in project.datasets.values():
        if dataset.kind != "local":
            continue
        _add_dependency_edges(edges, dataset)
        _add_query_warnings(warnings, dataset, dialect=dialect)
        _add_lineage_edges(
            nodes_by_id,
            edges,
            warnings,
            dataset,
            project=project,
            dialect=dialect,
        )

    artifact = merge(
        CatalogArtifact(
            nodes=sorted(nodes_by_id.values(), key=lambda item: item.id),
            edges=edges,
            warnings=warnings,
        )
    )
    column_count = sum(1 for node in artifact.nodes if node.kind == "column")
    dataset_count = sum(1 for node in artifact.nodes if node.kind == "table")
    root_dataset_count = sum(
        1 for dataset in project.datasets.values() if dataset.kind == "root"
    )
    summary = LineageSummary(
        dialect=dialect,
        input_kind=project.input_kind,
        dataset_count=dataset_count,
        root_dataset_count=root_dataset_count,
        column_count=column_count,
        warning_count=len(artifact.warnings),
    )
    return BuiltLineage(artifact=artifact, summary=summary)


def _add_dataset_node(nodes_by_id: dict[str, Node], dataset: ProjectDataset) -> None:
    dataset_id = table_id(dataset.name)
    if dataset_id in nodes_by_id:
        return
    nodes_by_id[dataset_id] = Node(
        id=dataset_id,
        kind="table",
        name=leaf_name(dataset.name),
        qualified_name=dataset.name,
        schema=schema_name(dataset.name),
        evidence=_dataset_evidence(dataset),
    )


def _dataset_evidence(dataset: ProjectDataset) -> list[Evidence]:
    if not dataset.evidence_file:
        return []
    return [
        Evidence(
            file=dataset.evidence_file,
            expression=dataset.name,
            confidence="high",
        )
    ]


def _add_column_node(
    nodes_by_id: dict[str, Node],
    dataset_name: str,
    column_name: str,
    evidence_file: str | None,
) -> None:
    node_id = column_id(dataset_name, column_name)
    if node_id in nodes_by_id:
        return
    evidence = []
    if evidence_file:
        evidence.append(
            Evidence(
                file=evidence_file,
                expression=f"{dataset_name}.{column_name}",
                confidence="high",
            )
        )
    nodes_by_id[node_id] = Node(
        id=node_id,
        kind="column",
        name=column_name,
        qualified_name=f"{dataset_name}.{column_name}",
        schema=schema_name(dataset_name),
        evidence=evidence,
    )


def _add_dependency_edges(edges: list[Edge], dataset: ProjectDataset) -> None:
    source_id = table_id(dataset.name)
    for dependency_name in dataset.dependency_names:
        edges.append(
            Edge(
                kind="depends_on",
                source_id=source_id,
                target_id=table_id(dependency_name),
                label="depends_on",
                evidence=[
                    Evidence(
                        file=dataset.evidence_file,
                        expression=dependency_name,
                        confidence="high",
                    )
                ]
                if dataset.evidence_file
                else [],
            )
        )


def _add_query_warnings(
    warnings: list[Warning],
    dataset: ProjectDataset,
    *,
    dialect: str,
) -> None:
    if detect_select_star(dataset.sql or "", dialect=dialect):
        warnings.append(
            Warning(
                code="select_star",
                message="SELECT * was detected; output mapping may stay warning-rich.",
                location=dataset.evidence_file,
            )
        )


def _add_lineage_edges(
    nodes_by_id: dict[str, Node],
    edges: list[Edge],
    warnings: list[Warning],
    dataset: ProjectDataset,
    *,
    project: ProjectInput,
    dialect: str,
) -> None:
    try:
        output_map = lineage(
            None,
            dataset.sql or "",
            schema=project.root_schema(),
            sources=project.sources_for(dataset.name),
            dialect=dialect,
        )
    except Exception as exc:  # pragma: no cover - exercised via failure-path tests
        warnings.append(
            Warning(
                code="lineage_resolution_failed",
                message=(
                    f"Lineage resolution failed for dataset {dataset.name!r}: {exc}"
                ),
                location=dataset.evidence_file,
            )
        )
        return

    if not isinstance(output_map, dict):
        raise LineageContractError(
            "catalogkit-lineage expected sqlglot.lineage(None, ...) to return a dict."
        )

    for output_name, root in sorted(output_map.items(), key=lambda item: item[0]):
        _add_column_node(nodes_by_id, dataset.name, output_name, dataset.evidence_file)
        source_id = column_id(dataset.name, output_name)
        all_refs = {
            ref
            for ref in _collect_all_refs(root)
            if ref != output_name and ref != f"{dataset.name}.{output_name}"
        }
        local_refs = {
            ref
            for ref in all_refs
            if _is_local_ref(ref, project=project, current_dataset=dataset.name)
        }
        selected_refs = local_refs or _collect_leaf_refs(root)
        if not selected_refs:
            warnings.append(
                Warning(
                    code="unresolved_output_source",
                    message=(
                        f"Lineage resolved no upstream leaves for output column {dataset.name}.{output_name}."
                    ),
                    location=dataset.evidence_file,
                )
            )
            continue
        for leaf_ref in sorted(selected_refs):
            if leaf_ref == "*":
                warnings.append(
                    Warning(
                        code="unresolved_star_source",
                        message=(
                            f"Lineage leaf expansion stayed at '*' for output column {dataset.name}.{output_name}."
                        ),
                        location=dataset.evidence_file,
                    )
                )
                continue
            parent_name, source_column = _split_ref(leaf_ref)
            _add_dataset_node(
                nodes_by_id,
                ProjectDataset(
                    name=parent_name,
                    kind="root"
                    if parent_name not in project.datasets
                    else project.datasets[parent_name].kind,
                    sql=None,
                    dependency_names=(),
                    declared_columns=(),
                    evidence_file=None,
                ),
            )
            _add_column_node(nodes_by_id, parent_name, source_column, None)
            edges.append(
                Edge(
                    kind="derives_from",
                    source_id=source_id,
                    target_id=column_id(parent_name, source_column),
                    label="derives_from",
                    evidence=[
                        Evidence(
                            file=dataset.evidence_file,
                            expression=leaf_ref,
                            confidence="medium",
                        )
                    ]
                    if dataset.evidence_file
                    else [],
                )
            )


def _collect_leaf_refs(node: SqlglotLineageNode) -> set[str]:
    if not node.downstream:
        return {node.name}
    refs: set[str] = set()
    for child in node.downstream:
        refs.update(_collect_leaf_refs(child))
    return refs


def _collect_all_refs(node: SqlglotLineageNode) -> set[str]:
    refs = {node.name}
    for child in node.downstream:
        refs.update(_collect_all_refs(child))
    return refs


def _is_local_ref(
    reference: str,
    *,
    project: ProjectInput,
    current_dataset: str,
) -> bool:
    if reference == "*":
        return False
    try:
        parent_name, _column_name = _split_ref(reference)
    except LineageContractError:
        return False
    if parent_name == current_dataset or parent_name not in project.datasets:
        return False
    return project.datasets[parent_name].kind == "local"


def _split_ref(reference: str) -> tuple[str, str]:
    parts = split_qualified_identifier(reference)
    if len(parts) < 2:
        raise LineageContractError(
            f"Expected qualified lineage reference, got {reference!r}."
        )
    return ".".join(parts[:-1]), parts[-1]


def _selection_to_column_id(selection: str) -> str:
    parent_name, column_name = _split_ref(selection)
    return column_id(parent_name, column_name)


def _column_selection_from_id(node_id: str) -> tuple[str, str]:
    if not node_id.startswith("column:"):
        raise LineageContractError(f"Expected column node id, got {node_id!r}")
    qualified_name = node_id[len("column:") :]
    return _split_ref(qualified_name)


def _require_column_selection(
    artifact: CatalogArtifact,
    *,
    selection: str,
    selection_id: str,
) -> None:
    if any(
        node.id == selection_id and node.kind == "column" for node in artifact.nodes
    ):
        return
    raise LineageInputError(
        f"Selection {selection!r} does not match any resolved lineage column."
    )


def _walk_upstream(artifact: CatalogArtifact, selection_id: str) -> list[str]:
    adjacency: dict[str, list[str]] = {}
    for edge in artifact.edges:
        adjacency.setdefault(edge.source_id, []).append(edge.target_id)

    visited: set[str] = set()
    stack = [selection_id]
    related: list[str] = []
    while stack:
        current = stack.pop()
        for target_id in adjacency.get(current, []):
            if target_id in visited:
                continue
            visited.add(target_id)
            related.append(target_id)
            stack.append(target_id)
    return related


def _walk_downstream(artifact: CatalogArtifact, selection_id: str) -> list[str]:
    adjacency: dict[str, list[str]] = {}
    for edge in artifact.edges:
        adjacency.setdefault(edge.target_id, []).append(edge.source_id)

    visited: set[str] = set()
    stack = [selection_id]
    related: list[str] = []
    while stack:
        current = stack.pop()
        for source_id in adjacency.get(current, []):
            if source_id in visited:
                continue
            visited.add(source_id)
            related.append(source_id)
            stack.append(source_id)
    return related
