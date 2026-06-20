"""Step 0 kill-test for catalogkit-lineage.

This is intentionally a throwaway prototype, not package code.
It compares:

1. Raw ``sqlglot.lineage`` used directly with manual ``sources`` + ``schema`` glue.
2. A tiny project resolver that loads a vendored dbt fixture, normalizes IDs with
   ``catalogkit-core``, emits a ``CatalogArtifact``, and answers upstream /
   downstream questions over the whole project graph.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
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
    render_json,
    schema_name,
    table_id,
)
from catalogkit.query import build_catalog_artifact as build_query_catalog_artifact
from catalogkit.query import build_query_map
from sqlglot.lineage import Node as LineageNode
from sqlglot.lineage import lineage

DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "jaffle_shop"


@dataclass(frozen=True)
class FixtureNode:
    unique_id: str
    resource_type: str
    name: str
    compiled_path: str | None
    depends_on: tuple[str, ...]
    columns: tuple[str, ...]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_fixture(
    fixture_dir: Path,
) -> tuple[dict[str, Any], dict[str, FixtureNode], dict[str, str]]:
    manifest = _read_json(fixture_dir / "manifest.json")
    nodes: dict[str, FixtureNode] = {}
    sql_by_name: dict[str, str] = {}
    for unique_id, payload in manifest["nodes"].items():
        depends_on = tuple(payload.get("depends_on", {}).get("nodes", []))
        columns = tuple(
            column_payload["name"]
            for column_payload in payload.get("columns", {}).values()
        )
        compiled_path = payload.get("compiled_path")
        nodes[unique_id] = FixtureNode(
            unique_id=unique_id,
            resource_type=payload["resource_type"],
            name=payload["name"],
            compiled_path=compiled_path,
            depends_on=depends_on,
            columns=columns,
        )
        if compiled_path:
            sql_by_name[payload["name"]] = (fixture_dir / compiled_path).read_text(
                encoding="utf-8"
            )
    return manifest, nodes, sql_by_name


def build_sources_by_name(
    nodes: dict[str, FixtureNode], sql_by_name: dict[str, str]
) -> dict[str, str]:
    return {
        node.name: sql_by_name[node.name]
        for node in nodes.values()
        if node.resource_type == "model"
    }


def build_upstream_model_names(
    nodes: dict[str, FixtureNode],
    *,
    target_unique_id: str,
) -> set[str]:
    discovered: set[str] = set()
    stack = list(nodes[target_unique_id].depends_on)
    while stack:
        dependency_unique_id = stack.pop()
        dependency_node = nodes[dependency_unique_id]
        if dependency_node.resource_type != "model":
            continue
        if dependency_node.name in discovered:
            continue
        discovered.add(dependency_node.name)
        stack.extend(dependency_node.depends_on)
    return discovered


def sources_for_target(
    nodes: dict[str, FixtureNode],
    sources_by_name: dict[str, str],
    *,
    target_unique_id: str,
) -> dict[str, str]:
    allowed_names = build_upstream_model_names(nodes, target_unique_id=target_unique_id)
    return {
        source_name: sql
        for source_name, sql in sources_by_name.items()
        if source_name in allowed_names
    }


def build_root_schema(nodes: dict[str, FixtureNode]) -> dict[str, dict[str, str]]:
    schema: dict[str, dict[str, str]] = {}
    for node in nodes.values():
        if node.resource_type != "seed":
            continue
        schema[node.name] = {column_name: "text" for column_name in node.columns}
    return schema


def lineage_column_ref(ref_name: str) -> tuple[str, str]:
    parts = ref_name.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Expected qualified lineage column reference, got {ref_name!r}"
        )
    return parts[0], parts[1]


def collect_leaf_refs(node: LineageNode) -> set[str]:
    if not node.downstream:
        return {node.name}
    refs: set[str] = set()
    for child in node.downstream:
        refs.update(collect_leaf_refs(child))
    return refs


def collect_all_refs(node: LineageNode) -> set[str]:
    refs = {node.name}
    for child in node.downstream:
        refs.update(collect_all_refs(child))
    return refs


def build_raw_upstream(
    *,
    nodes: dict[str, FixtureNode],
    model_unique_id: str,
    model_name: str,
    column_name: str,
    sql_by_name: dict[str, str],
    root_schema: dict[str, dict[str, str]],
    sources_by_name: dict[str, str],
    dialect: str,
) -> dict[str, Any]:
    root = lineage(
        column_name,
        sql_by_name[model_name],
        schema=root_schema,
        sources=sources_for_target(
            nodes,
            sources_by_name,
            target_unique_id=model_unique_id,
        ),
        dialect=dialect,
    )
    leaf_refs = sorted(collect_leaf_refs(root))
    all_refs = sorted(ref for ref in collect_all_refs(root) if ref != column_name)
    return {
        "output": f"{model_name}.{column_name}",
        "leaf_refs": leaf_refs,
        "all_refs": all_refs,
    }


def build_raw_downstream_index(
    *,
    nodes: dict[str, FixtureNode],
    sql_by_name: dict[str, str],
    root_schema: dict[str, dict[str, str]],
    sources_by_name: dict[str, str],
    dialect: str,
) -> dict[str, list[str]]:
    downstream: dict[str, set[str]] = {}
    for node in nodes.values():
        if node.resource_type != "model":
            continue
        for column_name in node.columns:
            root = lineage(
                column_name,
                sql_by_name[node.name],
                schema=root_schema,
                sources=sources_for_target(
                    nodes,
                    sources_by_name,
                    target_unique_id=node.unique_id,
                ),
                dialect=dialect,
            )
            for leaf_ref in collect_leaf_refs(root):
                downstream.setdefault(leaf_ref, set()).add(f"{node.name}.{column_name}")
    return {
        key: sorted(value)
        for key, value in sorted(downstream.items(), key=lambda item: item[0])
    }


class ProjectLineageResolver:
    def __init__(
        self,
        *,
        manifest: dict[str, Any],
        nodes: dict[str, FixtureNode],
        sql_by_name: dict[str, str],
        dialect: str,
    ) -> None:
        self.manifest = manifest
        self.nodes = nodes
        self.sql_by_name = sql_by_name
        self.dialect = dialect
        self.sources_by_name = build_sources_by_name(nodes, sql_by_name)
        self.root_schema = build_root_schema(nodes)

    def build_artifact(self) -> CatalogArtifact:
        nodes_by_id: dict[str, Node] = {}
        edges: list[Edge] = []
        warnings: list[Warning] = []

        for fixture_node in self.nodes.values():
            dataset_qualified_name = fixture_node.name
            dataset_id = table_id(dataset_qualified_name)
            nodes_by_id[dataset_id] = Node(
                id=dataset_id,
                kind="table",
                name=leaf_name(dataset_qualified_name),
                qualified_name=dataset_qualified_name,
                schema=schema_name(dataset_qualified_name),
                evidence=[
                    Evidence(
                        file=fixture_node.compiled_path,
                        expression=fixture_node.name,
                        confidence="high",
                    )
                ],
            )
            for column_name in fixture_node.columns:
                column_node_id = column_id(dataset_qualified_name, column_name)
                nodes_by_id[column_node_id] = Node(
                    id=column_node_id,
                    kind="column",
                    name=column_name,
                    qualified_name=f"{dataset_qualified_name}.{column_name}",
                    schema=schema_name(dataset_qualified_name),
                    evidence=[
                        Evidence(
                            file=fixture_node.compiled_path,
                            expression=column_name,
                            confidence="high",
                        )
                    ],
                )

        for fixture_node in self.nodes.values():
            if fixture_node.resource_type != "model":
                continue
            target_id = table_id(fixture_node.name)
            for dependency in fixture_node.depends_on:
                dependency_node = self.nodes[dependency]
                edges.append(
                    Edge(
                        kind="depends_on",
                        source_id=target_id,
                        target_id=table_id(dependency_node.name),
                        label="depends_on",
                        evidence=[
                            Evidence(
                                file=fixture_node.compiled_path,
                                expression=dependency_node.name,
                                confidence="high",
                            )
                        ],
                    )
                )

            query_map = build_query_map(
                self.sql_by_name[fixture_node.name],
                dialect=self.dialect,
            )
            for warning in query_map.warnings:
                warnings.append(
                    Warning(
                        code=warning.code,
                        message=warning.message,
                        location=warning.location,
                    )
                )

            for output_column in fixture_node.columns:
                output_id = column_id(fixture_node.name, output_column)
                root = lineage(
                    output_column,
                    self.sql_by_name[fixture_node.name],
                    schema=self.root_schema,
                    sources=sources_for_target(
                        self.nodes,
                        self.sources_by_name,
                        target_unique_id=fixture_node.unique_id,
                    ),
                    dialect=self.dialect,
                )
                for leaf_ref in sorted(collect_leaf_refs(root)):
                    parent_name, source_column = lineage_column_ref(leaf_ref)
                    source_id = column_id(parent_name, source_column)
                    edges.append(
                        Edge(
                            kind="derives_from",
                            source_id=output_id,
                            target_id=source_id,
                            label="derives_from",
                            evidence=[
                                Evidence(
                                    file=fixture_node.compiled_path,
                                    expression=leaf_ref,
                                    confidence="medium",
                                )
                            ],
                        )
                    )

        artifact = CatalogArtifact(
            nodes=sorted(nodes_by_id.values(), key=lambda item: item.id),
            edges=edges,
            warnings=warnings,
        )
        return merge(artifact)

    def upstream(
        self, artifact: CatalogArtifact, dataset_name: str, column_name: str
    ) -> list[str]:
        start_id = column_id(dataset_name, column_name)
        adjacency = self._adjacency_by_source(artifact)
        visited: set[str] = set()
        stack = [start_id]
        ordered: list[str] = []
        while stack:
            current = stack.pop()
            for target_id in adjacency.get(current, []):
                if target_id in visited:
                    continue
                visited.add(target_id)
                ordered.append(target_id)
                stack.append(target_id)
        return ordered

    def downstream(
        self, artifact: CatalogArtifact, dataset_name: str, column_name: str
    ) -> list[str]:
        start_id = column_id(dataset_name, column_name)
        adjacency = self._adjacency_by_target(artifact)
        visited: set[str] = set()
        stack = [start_id]
        ordered: list[str] = []
        while stack:
            current = stack.pop()
            for source_id in adjacency.get(current, []):
                if source_id in visited:
                    continue
                visited.add(source_id)
                ordered.append(source_id)
                stack.append(source_id)
        return ordered

    def merge_with_query_artifacts(self, artifact: CatalogArtifact) -> CatalogArtifact:
        query_artifacts = [
            build_query_catalog_artifact(sql, dialect=self.dialect)
            for sql in self.sql_by_name.values()
        ]
        return merge(artifact, *query_artifacts)

    @staticmethod
    def _adjacency_by_source(artifact: CatalogArtifact) -> dict[str, list[str]]:
        adjacency: dict[str, list[str]] = {}
        for edge in artifact.edges:
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)
        return adjacency

    @staticmethod
    def _adjacency_by_target(artifact: CatalogArtifact) -> dict[str, list[str]]:
        adjacency: dict[str, list[str]] = {}
        for edge in artifact.edges:
            adjacency.setdefault(edge.target_id, []).append(edge.source_id)
        return adjacency


def run_comparison(fixture_dir: Path, dialect: str) -> dict[str, Any]:
    manifest, nodes, sql_by_name = load_fixture(fixture_dir)
    sources_by_name = build_sources_by_name(nodes, sql_by_name)
    root_schema = build_root_schema(nodes)

    baseline_upstream = build_raw_upstream(
        nodes=nodes,
        model_unique_id="model.jaffle_shop.customers",
        model_name="customers",
        column_name="customer_lifetime_value",
        sql_by_name=sql_by_name,
        root_schema=root_schema,
        sources_by_name=sources_by_name,
        dialect=dialect,
    )
    baseline_downstream = build_raw_downstream_index(
        nodes=nodes,
        sql_by_name=sql_by_name,
        root_schema=root_schema,
        sources_by_name=sources_by_name,
        dialect=dialect,
    )

    resolver = ProjectLineageResolver(
        manifest=manifest,
        nodes=nodes,
        sql_by_name=sql_by_name,
        dialect=dialect,
    )
    artifact = resolver.build_artifact()
    merged_artifact = resolver.merge_with_query_artifacts(artifact)

    return {
        "fixture": manifest["metadata"]["project_name"],
        "raw_sqlglot": {
            "manual_sources_count": len(sources_by_name),
            "manual_root_schema_count": len(root_schema),
            "upstream_customer_lifetime_value": baseline_upstream,
            "downstream_raw_payments_amount": baseline_downstream.get(
                "raw_payments.amount",
                [],
            ),
        },
        "prototype": {
            "artifact_summary": {
                "node_count": len(artifact.nodes),
                "edge_count": len(artifact.edges),
                "warning_count": len(artifact.warnings),
            },
            "upstream_customer_lifetime_value": resolver.upstream(
                artifact,
                "customers",
                "customer_lifetime_value",
            ),
            "downstream_raw_payments_amount": resolver.downstream(
                artifact,
                "raw_payments",
                "amount",
            ),
            "merged_with_query_summary": {
                "node_count": len(merged_artifact.nodes),
                "edge_count": len(merged_artifact.edges),
                "warning_count": len(merged_artifact.warnings),
            },
        },
        "artifact": render_json(artifact),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare raw sqlglot.lineage with a tiny project-level lineage resolver.",
    )
    parser.add_argument(
        "--fixture-dir",
        default=str(DEFAULT_FIXTURE_DIR),
        help="Path to the fixture directory containing manifest.json and compiled SQL files.",
    )
    parser.add_argument(
        "--dialect",
        default="postgres",
        help="sqlglot dialect name to use for parsing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_comparison(Path(args.fixture_dir), args.dialect)
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
