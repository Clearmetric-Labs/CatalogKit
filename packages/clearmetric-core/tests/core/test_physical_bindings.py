from __future__ import annotations

import json
from pathlib import Path

import pytest
from clearmetric.adapters.warehouse import ingest_warehouse
from clearmetric.core import merge
from clearmetric.core.errors import MergeConflictError
from clearmetric.core.models import CatalogArtifact, Node, PhysicalBinding
from clearmetric.core.project import ClearMetricProject


def _warehouse_project(metadata_path: Path) -> ClearMetricProject:
    return ClearMetricProject.model_validate(
        {
            "version": 1,
            "dialect": "postgres",
            "sources": {
                "warehouse": {
                    "kind": "information_schema",
                    "path": str(metadata_path),
                }
            },
            "posture": "strict",
            "policy": {"rules": str(metadata_path.parent / "policy" / "rules.yaml")},
        }
    )


def test_warehouse_nodes_carry_physical_bindings(tmp_path: Path):
    metadata_path = tmp_path / "warehouse_schema.json"
    metadata_path.write_text(
        json.dumps(
            {
                "warehouse": "snowflake",
                "tables": [
                    {
                        "schema": "analytics",
                        "name": "orders",
                        "columns": [{"name": "amount", "data_type": "number"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "rules.yaml").write_text("rules: []\n", encoding="utf-8")

    artifact = ingest_warehouse(_warehouse_project(metadata_path))
    table = next(node for node in artifact.nodes if node.id == "table:analytics.orders")
    column = next(
        node for node in artifact.nodes if node.id == "column:analytics.orders.amount"
    )

    assert table.bindings == [
        PhysicalBinding(
            warehouse="snowflake",
            schema="analytics",
            table="orders",
        )
    ]
    assert column.bindings == [
        PhysicalBinding(
            warehouse="snowflake",
            schema="analytics",
            table="orders",
            column="amount",
        )
    ]


def test_conflicting_kind_merge_raises():
    left = Node(id="table:orders", kind="table", name="orders", qualified_name="orders")
    right = Node(
        id="table:orders", kind="column", name="orders", qualified_name="orders"
    )
    with pytest.raises(MergeConflictError):
        merge(CatalogArtifact(nodes=[left]), CatalogArtifact(nodes=[right]))
