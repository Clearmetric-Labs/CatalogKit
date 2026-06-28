"""Compile stderr diagnostics tests."""

from __future__ import annotations

import json
from pathlib import Path

from clearmetric.core.models import CatalogArtifact
from clearmetric.emitters.diagnostics import format_compile_diagnostics

from tests.wedge.helpers import run_cm_subprocess


def test_zero_lineage_fixture_emits_stderr_warning(tmp_path: Path):
    project_dir = tmp_path / "empty-sql"
    project_dir.mkdir()
    (project_dir / "clearmetric.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "dialect: postgres",
                "posture: strict",
                "policy:",
                "  rules: ./policy/rules.yaml",
                "sources:",
                "  sql:",
                "    paths:",
                "      - ./sql",
            ]
        ),
        encoding="utf-8",
    )
    (project_dir / "policy").mkdir()
    (project_dir / "policy" / "rules.yaml").write_text(
        "version: 1\nrules: []\n",
        encoding="utf-8",
    )
    sql_dir = project_dir / "sql"
    sql_dir.mkdir()
    (sql_dir / "orphan.sql").write_text("select 1 as only_col", encoding="utf-8")

    result = run_cm_subprocess(project_dir, "compile", "--format", "json")
    assert result.returncode == 0
    assert "LINEAGE WARNING:" in result.stderr
    assert "0 derives_from edges were produced." in result.stderr
    payload = json.loads(result.stdout)
    assert payload["edges"] == [] or not any(
        edge["kind"] == "derives_from" for edge in payload["edges"]
    )


def test_healthy_fixture_has_no_lineage_warning():
    repo_root = Path(__file__).resolve().parents[4]
    project_dir = repo_root / "examples" / "lineage-demo"
    result = run_cm_subprocess(project_dir, "compile", "--format", "json")
    assert result.returncode == 0
    assert "LINEAGE WARNING:" not in result.stderr
    artifact = CatalogArtifact.model_validate(json.loads(result.stdout))
    assert format_compile_diagnostics(artifact) is None
