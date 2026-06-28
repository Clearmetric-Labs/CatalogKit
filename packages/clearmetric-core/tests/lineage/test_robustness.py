from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .project_helpers import build_lineage_map


def _manifest_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "lineage"
        / "projects"
        / "jaffle_shop"
    )


def _sql_folder_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "lineage"
        / "projects"
        / "sql_folder"
    )


def test_bad_sql_file_warns_without_killing_valid_sibling(tmp_path: Path):
    (tmp_path / "valid.sql").write_text(
        "select amount from raw_orders", encoding="utf-8"
    )
    (tmp_path / "broken.sql").write_text("select from", encoding="utf-8")

    lineage_map = build_lineage_map(tmp_path, dialect="postgres")

    warning_codes = [warning.code for warning in lineage_map.warnings]
    derives_from = {
        (edge.source_id, edge.target_id)
        for edge in lineage_map.edges
        if edge.kind == "derives_from"
    }

    assert "lineage_resolution_failed" in warning_codes
    assert ("column:valid.amount", "column:raw_orders.amount") in derives_from


def test_cli_and_api_match_for_downstream_json_output(tmp_path: Path):
    fixture_root = _sql_folder_root()
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    for sql_file in fixture_root.glob("*.sql"):
        sql_dir.joinpath(sql_file.name).write_text(
            sql_file.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    config_path = tmp_path / "clearmetric.yaml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "dialect: postgres",
                "sources:",
                "  sql:",
                "    paths:",
                "      - ./sql",
                "posture: strict",
                "policy:",
                "  rules: ./policy/rules.yaml",
            ]
        ),
        encoding="utf-8",
    )
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "rules.yaml").write_text("rules: []\n", encoding="utf-8")

    from clearmetric.compiler.impact import impact

    _compiled, api_result = impact(
        tmp_path,
        selection="orders_base.amount",
        direction="downstream",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "clearmetric.cli",
            "--project-dir",
            str(tmp_path),
            "impact",
            "orders_base.amount",
            "--downstream",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["related_ids"] == api_result.related_ids
