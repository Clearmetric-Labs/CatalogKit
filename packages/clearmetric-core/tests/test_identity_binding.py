"""Identity binding tests for warehouse and dbt table resolution."""

from __future__ import annotations

from clearmetric.adapters.warehouse import WarehouseMetadataTable, _table_qualified_name
from clearmetric.core import (
    resolve_table_match,
    warehouse_table_fqn_candidates,
    warehouse_table_fqn_candidates_from_name,
)


def test_warehouse_qualified_name_includes_database():
    table = WarehouseMetadataTable(
        database="db1",
        schema="public",
        name="orders",
        columns=[],
    )
    assert _table_qualified_name(table) == "db1.public.orders"


def test_warehouse_qualified_name_database_without_schema():
    table = WarehouseMetadataTable(
        database="db1",
        name="orders",
        columns=[],
    )
    assert _table_qualified_name(table) == "db1.orders"


def test_database_specific_candidate_wins_before_suffix_bridge():
    target_ids = {"table:db1.public.orders", "table:db2.public.orders"}
    candidates = warehouse_table_fqn_candidates(
        database="db1",
        schema="public",
        table="orders",
    )
    matched, status = resolve_table_match(candidates, target_ids)
    assert status == "resolved"
    assert matched == "table:db1.public.orders"


def test_schema_only_candidate_refuses_two_database_ambiguity():
    target_ids = {"table:db1.public.orders", "table:db2.public.orders"}
    candidates = warehouse_table_fqn_candidates(
        schema="public",
        table="orders",
    )
    matched, status = resolve_table_match(candidates, target_ids)
    assert matched is None
    assert status == "ambiguous"


def test_two_database_orders_resolve_via_generated_fqn_candidates():
    target_ids = {"table:db1.public.orders", "table:db2.public.orders"}
    db1_candidates = warehouse_table_fqn_candidates_from_name("db1.public.orders")
    matched, status = resolve_table_match(db1_candidates, target_ids)
    assert status == "resolved"
    assert matched == "table:db1.public.orders"
    db2_candidates = warehouse_table_fqn_candidates_from_name("db2.public.orders")
    matched_other, status_other = resolve_table_match(db2_candidates, target_ids)
    assert status_other == "resolved"
    assert matched_other == "table:db2.public.orders"


def test_two_database_suffix_bridge_refuses_ambiguous_orders():
    target_ids = {"table:db1.public.orders", "table:db2.public.orders"}
    candidates = warehouse_table_fqn_candidates(table="orders")
    matched, status = resolve_table_match(candidates, target_ids)
    assert matched is None
    assert status == "ambiguous"


def test_warehouse_candidates_preserve_database_prefix():
    candidates = warehouse_table_fqn_candidates(
        database="db1",
        schema="public",
        table="orders",
    )
    assert candidates[0] == "db1.public.orders"
    assert "orders" in candidates
