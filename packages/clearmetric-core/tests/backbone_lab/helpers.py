"""Shared helpers for backbone lab tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from tests.wedge.helpers import (
    JAFFLE_WAREHOUSE_SCHEMA,
    copy_jaffle_fixture,
    write_warehouse_schema,
)


def write_lab_policy(project_dir: Path) -> None:
    policy_dir = project_dir / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "rules.yaml").write_text(
        yaml.safe_dump(
            {
                "rules": [
                    {
                        "id": "analyst-columns",
                        "kind": "rbac",
                        "identity": "analyst",
                        "effect": "allow",
                        "selector": {"kind": "column"},
                    },
                    {
                        "id": "analyst-metrics",
                        "kind": "rbac",
                        "identity": "analyst",
                        "effect": "allow",
                        "selector": {"kind": "metric"},
                    },
                    {
                        "id": "analyst-queries",
                        "kind": "rbac",
                        "identity": "analyst",
                        "effect": "allow",
                        "selector": {"kind": "query"},
                    },
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def write_lab_intent(project_dir: Path) -> None:
    intent_dir = project_dir / "intent"
    intent_dir.mkdir(parents=True, exist_ok=True)
    (intent_dir / "metrics.yaml").write_text(
        yaml.safe_dump(
            {
                "metrics": [
                    {
                        "id": "executive_revenue",
                        "name": "Executive Revenue",
                        "formula": "sum(amount)",
                        "depends_on": ["column:orders.amount"],
                    }
                ],
                "queries": [
                    {
                        "id": "executive_revenue",
                        "name": "Executive Revenue Query",
                        "sql": "SELECT amount AS net_revenue FROM orders",
                        "depends_on": ["column:orders.amount"],
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def write_lab_seed(project_dir: Path) -> None:
    fixtures = project_dir / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    (fixtures / "seed.sql").write_text(
        "CREATE TABLE orders AS SELECT 100::DOUBLE AS amount;\n",
        encoding="utf-8",
    )


def write_lab_config(project_dir: Path) -> None:
    write_lab_policy(project_dir)
    write_lab_intent(project_dir)
    write_lab_seed(project_dir)
    (project_dir / "clearmetric.yaml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "dialect": "postgres",
                "sources": {
                    "warehouse": {
                        "kind": "information_schema",
                        "path": "./warehouse_schema.json",
                    },
                    "dbt": {"manifest": "./target/manifest.json"},
                    "intent": {"paths": ["./intent"]},
                },
                "posture": "strict",
                "policy": {"rules": "./policy/rules.yaml"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def setup_backbone_lab_project(project_dir: Path) -> Path:
    project_dir.mkdir(parents=True, exist_ok=True)
    copy_jaffle_fixture(project_dir)
    write_warehouse_schema(project_dir)
    write_lab_config(project_dir)
    return project_dir


def copy_backbone_lab_example(project_dir: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    example = repo_root / "examples" / "backbone-lab"
    if example.is_dir():
        shutil.copytree(example, project_dir, dirs_exist_ok=True)
        target = project_dir / "target"
        target.mkdir(parents=True, exist_ok=True)
        copy_jaffle_fixture(project_dir)
        if not (project_dir / "warehouse_schema.json").is_file():
            shutil.copy2(JAFFLE_WAREHOUSE_SCHEMA, project_dir / "warehouse_schema.json")
    else:
        setup_backbone_lab_project(project_dir)
    return project_dir
