"""Committed backbone-lab example subprocess demo."""

from __future__ import annotations

import json
from pathlib import Path

from tests.backbone_lab.helpers import copy_backbone_lab_example
from tests.wedge.helpers import run_cm_subprocess


def test_example_backbone_lab_demo(tmp_path: Path):
    project_dir = copy_backbone_lab_example(tmp_path / "example")

    steps = [
        ("compile", "--format", "json"),
        ("compile", "--format", "catalog"),
        (
            "compile",
            "--format",
            "consumer-catalog",
            "--identity",
            "analyst",
        ),
        (
            "compile",
            "--format",
            "frontend-contract",
            "--identity",
            "analyst",
        ),
        (
            "compile",
            "--format",
            "ai-context",
            "--identity",
            "analyst",
        ),
        ("impact", "orders.amount", "--upstream"),
        (
            "query",
            "--identity",
            "analyst",
            "query:executive_revenue",
        ),
    ]

    last_stdout = ""
    for args in steps:
        result = run_cm_subprocess(project_dir, *args, experimental=True)
        assert result.returncode == 0, result.stderr
        last_stdout = result.stdout

    rows = json.loads(last_stdout)
    assert rows[0]["net_revenue"] == 100

    consumer = json.loads(
        run_cm_subprocess(
            project_dir,
            "compile",
            "--format",
            "consumer-catalog",
            "--identity",
            "analyst",
            experimental=True,
        ).stdout
    )
    assert "query:executive_revenue" in {
        node["id"] for node in consumer["payload"]["nodes"]
    }
