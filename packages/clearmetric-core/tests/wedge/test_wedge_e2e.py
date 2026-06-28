from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from clearmetric.compiler.compile import compile as compile_project
from clearmetric.compiler.impact import impact
from clearmetric.core.errors import SecurityFloorError
from clearmetric.core.models import CatalogArtifact, Edge, Node

from tests.wedge.helpers import (
    JAFFLE_FIXTURE,
    setup_wedge_project,
    write_warehouse_schema,
)


def _run_cm(project_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "clearmetric.cli",
            "--project-dir",
            str(project_dir),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_wedge_init_connect_scan_compile_impact_clean_contract(tmp_path: Path):
    empty_dir = tmp_path / "fresh"
    empty_dir.mkdir()
    target = empty_dir / "target"
    target.mkdir()
    shutil.copy2(JAFFLE_FIXTURE / "manifest.json", target / "manifest.json")
    write_warehouse_schema(empty_dir)

    init_result = _run_cm(empty_dir, "init")
    assert init_result.returncode == 0, init_result.stderr
    assert (empty_dir / "clearmetric.yaml").is_file()
    assert (empty_dir / "policy" / "rules.yaml").is_file()
    init_yaml = yaml.safe_load(
        (empty_dir / "clearmetric.yaml").read_text(encoding="utf-8")
    )
    assert init_yaml["posture"] == "strict"

    project_dir = setup_wedge_project(tmp_path / "wired")

    connect_result = _run_cm(
        project_dir,
        "connect",
        "warehouse",
        "--information-schema",
        "./warehouse_schema.json",
    )
    assert connect_result.returncode == 0, connect_result.stderr

    scan_result = _run_cm(project_dir, "scan", "--format", "json")
    assert scan_result.returncode == 0, scan_result.stderr
    scan_payload = json.loads(scan_result.stdout)
    kinds = {item["kind"] for item in scan_payload["sources"]}
    assert kinds == {"warehouse", "dbt"}

    compile_result = _run_cm(project_dir, "compile", "--format", "json")
    assert compile_result.returncode == 0, compile_result.stderr
    artifact = CatalogArtifact.model_validate(json.loads(compile_result.stdout))
    assert any(node.bindings for node in artifact.nodes)

    graph_path = project_dir / "graph.json"
    graph_path.write_text(compile_result.stdout, encoding="utf-8")

    _compiled, api_result = impact(
        project_dir,
        selection="orders.amount",
        direction="upstream",
    )
    cli_result = _run_cm(
        project_dir,
        "impact",
        "orders.amount",
        "--upstream",
        "--format",
        "json",
    )
    assert cli_result.returncode == 0, cli_result.stderr
    cli_payload = json.loads(cli_result.stdout)
    assert cli_payload["related_ids"] == api_result.related_ids
    assert cli_payload["selection_id"] == "column:orders.amount"

    alias_result = _run_cm(
        project_dir,
        "impact",
        "column.orders.amount",
        "--upstream",
        "--format",
        "json",
    )
    assert alias_result.returncode == 0, alias_result.stderr
    assert json.loads(alias_result.stdout)["related_ids"] == api_result.related_ids

    clean_result = _run_cm(project_dir, "clean", "--format", "json")
    assert clean_result.returncode == 0, clean_result.stderr
    clean_payload = json.loads(clean_result.stdout)
    assert not any(item["severity"] == "error" for item in clean_payload["findings"])

    contract_result = _run_cm(project_dir, "contract", str(graph_path))
    assert contract_result.returncode == 0, contract_result.stderr


def test_contract_rejects_dangling_edge(tmp_path: Path):
    artifact = CatalogArtifact(
        edges=[
            Edge(
                kind="derives_from",
                source_id="column:missing.x",
                target_id="column:present.y",
                label="derives_from",
            )
        ]
    )
    graph_path = tmp_path / "bad.json"
    graph_path.write_text(
        json.dumps(artifact.model_dump(mode="json")), encoding="utf-8"
    )
    result = _run_cm(tmp_path, "contract", str(graph_path))
    assert result.returncode == 1
    assert "cm error:" in result.stderr


def test_compile_raises_security_floor_for_ai_without_classification(tmp_path: Path):
    project_dir = setup_wedge_project(tmp_path)
    bad = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.email",
                kind="column",
                name="email",
                qualified_name="orders.email",
                aspects={"ai_behavior": {"allowed": True}},
            )
        ]
    )
    with patch("clearmetric.compiler.compile.ingest_all", return_value=[("dbt", bad)]):
        with pytest.raises(SecurityFloorError):
            compile_project(project_dir)
