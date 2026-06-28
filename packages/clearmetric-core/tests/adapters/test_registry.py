from __future__ import annotations

from pathlib import Path

import pytest
from clearmetric.adapters.registry import SOURCE_ORDER, enabled_sources, ingest_all
from clearmetric.core.errors import AdapterError
from clearmetric.core.project import load_project_config

from tests.wedge.helpers import setup_wedge_project


def test_source_order_and_enabled_sources(tmp_path: Path):
    project_dir = setup_wedge_project(tmp_path)
    project = load_project_config(project_dir)
    assert enabled_sources(project) == ["warehouse", "dbt"]
    assert SOURCE_ORDER == ("warehouse", "dbt", "sql", "intent")


def test_ingest_all_merges_warehouse_and_dbt(tmp_path: Path):
    project_dir = setup_wedge_project(tmp_path)
    project = load_project_config(project_dir)
    ingested = ingest_all(project)
    kinds = [kind for kind, _artifact in ingested]
    assert kinds == ["warehouse", "dbt"]
    warehouse_artifact = ingested[0][1]
    assert any(node.bindings for node in warehouse_artifact.nodes)


def test_intent_source_requires_experimental_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CM_EXPERIMENTAL", raising=False)
    project_dir = tmp_path / "intent-project"
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
                "  intent:",
                "    paths:",
                "      - ./intent",
            ]
        ),
        encoding="utf-8",
    )
    policy_dir = project_dir / "policy"
    policy_dir.mkdir()
    (policy_dir / "rules.yaml").write_text("version: 1\nrules: []\n", encoding="utf-8")
    intent_dir = project_dir / "intent"
    intent_dir.mkdir()
    (intent_dir / "metrics.yaml").write_text("metrics: []\n", encoding="utf-8")
    project = load_project_config(project_dir)

    with pytest.raises(AdapterError, match="CM_EXPERIMENTAL=1"):
        enabled_sources(project)
