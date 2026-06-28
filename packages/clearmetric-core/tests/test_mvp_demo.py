"""Backbone lab MVP subprocess demo."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from tests.backbone_lab.helpers import setup_backbone_lab_project
from tests.wedge.helpers import run_cm_subprocess


def test_mvp_demo_same_canonical_id_flow(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")

    compile_json = run_cm_subprocess(
        project_dir, "compile", "--format", "json", experimental=True
    )
    assert compile_json.returncode == 0, compile_json.stderr
    graph = json.loads(compile_json.stdout)
    graph_ids = {node["id"] for node in graph["nodes"]}
    assert "column:orders.amount" in graph_ids
    assert "metric:executive_revenue" in graph_ids
    assert "query:executive_revenue" in graph_ids

    compile_catalog = run_cm_subprocess(
        project_dir, "compile", "--format", "catalog", experimental=True
    )
    assert compile_catalog.returncode == 0, compile_catalog.stderr
    catalog = json.loads(compile_catalog.stdout)
    catalog_ids = {node["id"] for node in catalog["nodes"]}
    assert "column:orders.amount" in catalog_ids
    assert "metric:executive_revenue" not in catalog_ids
    assert "query:executive_revenue" not in catalog_ids
    assert "payload" not in catalog

    compile_openlineage = run_cm_subprocess(
        project_dir, "compile", "--format", "openlineage", experimental=True
    )
    assert compile_openlineage.returncode == 0, compile_openlineage.stderr

    compile_consumer = run_cm_subprocess(
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
    consumer_ids = {node["id"] for node in consumer["payload"]["nodes"]}
    assert consumer["format"] == "consumer-catalog"
    assert "column:orders.amount" in consumer_ids
    assert "metric:executive_revenue" in consumer_ids
    assert "query:executive_revenue" in consumer_ids

    compile_contracts = run_cm_subprocess(
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
    assert contracts["payload"]["queries"][0]["id"] == "query:executive_revenue"
    assert "SELECT" in contracts["payload"]["queries"][0]["sql"]

    compile_ai = run_cm_subprocess(
        project_dir,
        "compile",
        "--format",
        "ai-context",
        "--identity",
        "analyst",
        experimental=True,
    )
    assert compile_ai.returncode == 0, compile_ai.stderr
    ai_context = json.loads(compile_ai.stdout)
    ai_ids = {node["id"] for node in ai_context["payload"]["nodes"]}
    assert "metric:executive_revenue" in ai_ids
    assert "query:executive_revenue" not in ai_ids

    impact = run_cm_subprocess(
        project_dir,
        "impact",
        "orders.amount",
        "--upstream",
        experimental=True,
    )
    assert impact.returncode == 0, impact.stderr
    assert "orders.amount" in impact.stdout or "column:orders.amount" in impact.stdout

    query = run_cm_subprocess(
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

    graph_path = project_dir / "graph.json"
    graph_path.write_text(compile_json.stdout, encoding="utf-8")
    port = 18765
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "clearmetric.cli",
            "--project-dir",
            str(project_dir),
            "serve",
            str(graph_path),
            "--identity",
            "analyst",
            "--port",
            str(port),
        ],
        env={**dict(**__import__("os").environ), "CM_EXPERIMENTAL": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health") as resp:
                    health = json.loads(resp.read().decode("utf-8"))
                    break
            except urllib.error.URLError:
                time.sleep(0.1)
        else:
            raise AssertionError(
                server.stderr.read() if server.stderr else "serve failed to start"
            )
        assert health["status"] == "ok"
        assert "debug harness" in health["note"]

        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/query",
            data=json.dumps({"query_id": "query:executive_revenue"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        assert payload["rows"][0]["net_revenue"] == 100
    finally:
        server.terminate()
        server.wait(timeout=5)
