from __future__ import annotations

from pathlib import Path

from catalogkit.lineage import (
    build_lineage_map,
    build_openlineage_export,
    trace_downstream,
    trace_upstream,
)


def _example_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "jaffle_shop"


def _folder_example_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "sql_folder"


def test_build_lineage_map_from_manifest():
    manifest_path = _example_root() / "manifest.json"

    lineage_map = build_lineage_map(manifest_path, dialect="postgres")

    assert lineage_map.summary.input_kind == "dbt_manifest"
    assert lineage_map.summary.dataset_count >= 8
    assert lineage_map.summary.column_count >= 20
    assert any(node.id == "table:customers" for node in lineage_map.nodes)
    assert any(
        edge.source_id == "column:customers.customer_lifetime_value"
        and edge.target_id == "column:stg_payments.amount"
        for edge in lineage_map.edges
    )
    assert any(warning.code == "select_star" for warning in lineage_map.warnings)


def test_folder_input_supports_traversal():
    compiled_dir = _folder_example_root()

    lineage_map = build_lineage_map(compiled_dir, dialect="postgres")
    downstream = trace_downstream(
        compiled_dir,
        dialect="postgres",
        selection="orders_base.amount",
    )
    upstream = trace_upstream(
        compiled_dir,
        dialect="postgres",
        selection="customers_report.customer_lifetime_value",
    )

    assert lineage_map.summary.input_kind == "sql_folder"
    assert lineage_map.warnings == []
    assert "column:customer_totals.total_amount" in downstream.related_ids
    assert "column:customers_report.customer_lifetime_value" in downstream.related_ids
    assert upstream.related_ids == [
        "column:customer_totals.total_amount",
        "column:orders_base.amount",
        "column:raw_orders.amount",
    ]


def test_openlineage_export_contains_column_lineage_entries():
    manifest_path = _example_root() / "manifest.json"

    payload = build_openlineage_export(manifest_path, dialect="postgres")

    assert payload["job"]["name"] == "jaffle_shop"
    assert any(entry["name"] == "customers" for entry in payload["datasets"])
    assert any(
        entry["dataset"] == "customers" and entry["column"] == "customer_lifetime_value"
        for entry in payload["columnLineage"]
    )


def test_openlineage_export_groups_multiple_inputs_per_output_column(tmp_path: Path):
    report_sql = tmp_path / "report.sql"
    report_sql.write_text(
        """
        select
            source_a.amount + source_b.amount as total_amount
        from source_a
        join source_b
            on source_a.id = source_b.id
        """.strip(),
        encoding="utf-8",
    )

    payload = build_openlineage_export(tmp_path, dialect="postgres")

    grouped_entries = [
        entry
        for entry in payload["columnLineage"]
        if entry["dataset"] == "report" and entry["column"] == "total_amount"
    ]

    assert len(grouped_entries) == 1
    assert grouped_entries[0]["inputFields"] == [
        {"namespace": "catalogkit", "name": "source_a", "field": "amount"},
        {"namespace": "catalogkit", "name": "source_b", "field": "amount"},
    ]
