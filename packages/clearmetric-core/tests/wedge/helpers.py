"""Shared helpers for wedge/compiler tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from clearmetric.cli.runner import run_cm as run_cm_subprocess

__all__ = [
    "JAFFLE_FIXTURE",
    "JAFFLE_WAREHOUSE_SCHEMA",
    "copy_jaffle_fixture",
    "run_cm_subprocess",
    "setup_wedge_project",
    "write_policy",
    "write_warehouse_schema",
    "write_wedge_config",
]
JAFFLE_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "lineage"
    / "projects"
    / "jaffle_shop"
)
JAFFLE_WAREHOUSE_SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "wedge"
    / "jaffle_warehouse_schema.json"
)


def copy_jaffle_fixture(project_dir: Path) -> None:
    target = project_dir / "target"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(JAFFLE_FIXTURE / "manifest.json", target / "manifest.json")
    compiled_src = JAFFLE_FIXTURE / "compiled"
    if compiled_src.is_dir():
        shutil.copytree(compiled_src, target / "compiled", dirs_exist_ok=True)


def write_policy(project_dir: Path) -> None:
    policy_dir = project_dir / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "rules.yaml").write_text("rules: []\n", encoding="utf-8")


def write_warehouse_schema(project_dir: Path) -> None:
    shutil.copy2(JAFFLE_WAREHOUSE_SCHEMA, project_dir / "warehouse_schema.json")


def write_wedge_config(project_dir: Path) -> None:
    write_policy(project_dir)
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
                },
                "posture": "strict",
                "policy": {"rules": "./policy/rules.yaml"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def setup_wedge_project(project_dir: Path) -> Path:
    project_dir.mkdir(parents=True, exist_ok=True)
    copy_jaffle_fixture(project_dir)
    write_warehouse_schema(project_dir)
    write_wedge_config(project_dir)
    return project_dir
