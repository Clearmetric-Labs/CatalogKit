from __future__ import annotations

from pathlib import Path

import pytest
from clearmetric.core import attach_warehouse_bindings
from clearmetric.core.models import (
    CatalogArtifact,
    DerivationState,
    Node,
    PhysicalBinding,
)
from clearmetric.lineage.errors import LineageInputError
from clearmetric.lineage.loaders import load_project

from .project_helpers import build_catalog_artifact

FIXTURES_ROOT = (
    Path(__file__).resolve().parent.parent / "fixtures" / "lineage" / "dbt_identity"
)


def test_name_differs_from_alias_uses_relation_identity():
    project = load_project(
        FIXTURES_ROOT / "name_differs_from_alias" / "manifest.json",
        dialect="postgres",
    )
    assert "warehouse.analytics.orders" in project.datasets
    assert "orders_mart" not in project.datasets
    artifact = build_catalog_artifact(
        FIXTURES_ROOT / "name_differs_from_alias" / "manifest.json",
        dialect="postgres",
    )
    table = next(
        node for node in artifact.nodes if node.id == "table:warehouse.analytics.orders"
    )
    assert table.qualified_name == "warehouse.analytics.orders"
    assert table.aspects is not None
    assert table.aspects["dbt"]["alias"] == "orders"
    assert table.aspects["dbt"]["name"] == "orders_mart"


def test_same_name_across_packages_stays_distinct():
    project = load_project(
        FIXTURES_ROOT / "same_name_across_packages" / "manifest.json",
        dialect="postgres",
    )
    identities = {
        dataset.name for dataset in project.datasets.values() if dataset.kind == "local"
    }
    assert identities == {"db_a.analytics.orders", "db_b.analytics.orders"}


def test_same_alias_across_schemas_stays_distinct():
    project = load_project(
        FIXTURES_ROOT / "same_alias_across_schemas" / "manifest.json",
        dialect="postgres",
    )
    identities = {
        dataset.name for dataset in project.datasets.values() if dataset.kind == "local"
    }
    assert identities == {
        "warehouse.schema_a.orders",
        "warehouse.schema_b.orders",
    }


def test_warehouse_bind_uses_relation_identity():
    manifest = FIXTURES_ROOT / "warehouse_bind" / "manifest.json"
    merged = build_catalog_artifact(manifest, dialect="postgres")
    warehouse = CatalogArtifact(
        nodes=[
            Node(
                id="table:db1.public.orders",
                kind="table",
                name="orders",
                qualified_name="db1.public.orders",
                derivation=DerivationState(
                    status="complete", confidence="high", source="information_schema"
                ),
                bindings=[
                    PhysicalBinding(
                        warehouse="snowflake",
                        database="db1",
                        schema="public",
                        table="orders",
                    )
                ],
            ),
            Node(
                id="table:db2.public.orders",
                kind="table",
                name="orders",
                qualified_name="db2.public.orders",
                derivation=DerivationState(
                    status="complete", confidence="high", source="information_schema"
                ),
                bindings=[
                    PhysicalBinding(
                        warehouse="snowflake",
                        database="db2",
                        schema="public",
                        table="orders",
                    )
                ],
            ),
        ]
    )
    result = attach_warehouse_bindings(
        merged=merged,
        warehouse_artifact=warehouse,
        alias_map=None,
    )
    bound = next(node for node in result.nodes if node.id == "table:db1.public.orders")
    assert bound.bindings
    assert bound.bindings[0].database == "db1"
    assert not any(w.code == "warehouse_bind_ambiguous" for w in result.warnings)


def test_unresolved_internal_dependency_raises():
    with pytest.raises(LineageInputError, match="Unresolved dbt dependency"):
        load_project(
            FIXTURES_ROOT / "unresolved_internal_dependency" / "manifest.json",
            dialect="postgres",
        )


def test_duplicate_resolved_identity_raises():
    with pytest.raises(LineageInputError, match="Duplicate dbt dataset identity"):
        load_project(
            FIXTURES_ROOT / "duplicate_resolved_identity" / "manifest.json",
            dialect="postgres",
        )


def test_source_under_sources_key_compiles_as_root():
    project = load_project(
        FIXTURES_ROOT / "source_under_sources_key" / "manifest.json",
        dialect="postgres",
    )
    assert "warehouse.shopify.orders" in project.datasets
    assert project.datasets["warehouse.shopify.orders"].kind == "root"
    assert "warehouse.analytics.stg_orders" in project.datasets
    stg = project.datasets["warehouse.analytics.stg_orders"]
    assert "warehouse.shopify.orders" in stg.dependency_names
    artifact = build_catalog_artifact(
        FIXTURES_ROOT / "source_under_sources_key" / "manifest.json",
        dialect="postgres",
    )
    root = next(
        node for node in artifact.nodes if node.id == "table:warehouse.shopify.orders"
    )
    assert root.aspects is not None
    assert root.aspects["dbt"]["resource_type"] == "source"
