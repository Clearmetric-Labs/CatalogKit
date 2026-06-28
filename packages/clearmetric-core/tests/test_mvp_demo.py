"""Backbone lab MVP subprocess demo."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.backbone_lab.helpers import setup_backbone_lab_project


def _run_cm(
    project_dir: Path,
    *args: str,
    experimental: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if experimental:
        env["CM_EXPERIMENTAL"] = "1"
    else:
        env.pop("CM_EXPERIMENTAL", None)
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
        env=env,
    )


def test_mvp_demo_same_canonical_id_flow(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")

    compile_json = _run_cm(project_dir, "compile", "--format", "json")
    assert compile_json.returncode == 0, compile_json.stderr
    graph = json.loads(compile_json.stdout)
    graph_ids = {node["id"] for node in graph["nodes"]}
    assert "column:orders.amount" in graph_ids
    assert "metric:executive_revenue" in graph_ids
    assert "query:executive_revenue" in graph_ids

    compile_catalog = _run_cm(project_dir, "compile", "--format", "catalog")
    assert compile_catalog.returncode == 0, compile_catalog.stderr
    catalog = json.loads(compile_catalog.stdout)
    assert "column:orders.amount" in {node["id"] for node in catalog["nodes"]}

    compile_consumer = _run_cm(
        project_dir,
        "compile",
        "--format",
        "consumer-catalog",
        "--identity",
        "analyst",
        experimental=True,
    )
    assert compile_consumer.returncode == 0, compile_consumer.stderr
    consumer = json.loads(compile_consumer.stdout)
    consumer_ids = {node["id"] for node in consumer["nodes"]}
    assert "column:orders.amount" in consumer_ids
    assert "query:executive_revenue" in consumer_ids

    compile_contracts = _run_cm(
        project_dir,
        "compile",
        "--format",
        "frontend-contract",
        "--identity",
        "analyst",
        experimental=True,
    )
    assert compile_contracts.returncode == 0, compile_contracts.stderr
    contracts = json.loads(compile_contracts.stdout)
    assert contracts["queries"][0]["id"] == "query:executive_revenue"
    assert "SELECT" in contracts["queries"][0]["sql"]

    impact = _run_cm(
        project_dir,
        "impact",
        "orders.amount",
        "--upstream",
    )
    assert impact.returncode == 0, impact.stderr
    assert "orders.amount" in impact.stdout or "column:orders.amount" in impact.stdout

    query = _run_cm(
        project_dir,
        "query",
        "--identity",
        "analyst",
        "query:executive_revenue",
        experimental=True,
    )
    assert query.returncode == 0, query.stderr
    rows = json.loads(query.stdout)
    assert rows[0]["net_revenue"] == 100
