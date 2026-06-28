"""Contract node validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from clearmetric.compiler.contracts import validate_contract_nodes
from clearmetric.core.errors import CompilerError
from clearmetric.core.models import CatalogArtifact, Node


def test_metric_node_requires_contract_aspect():
    artifact = CatalogArtifact(
        nodes=[Node(id="metric:revenue", kind="metric", name="revenue")]
    )
    with pytest.raises(CompilerError, match="aspects.metric"):
        validate_contract_nodes(artifact)


def test_unresolved_depends_on_raises():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="metric:revenue",
                kind="metric",
                name="revenue",
                aspects={
                    "metric": {
                        "formula": "sum(amount)",
                        "depends_on": ["column:missing.amount"],
                    }
                },
            )
        ]
    )
    with pytest.raises(CompilerError, match="missing node"):
        validate_contract_nodes(artifact)


def test_empty_metric_formula_raises():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="metric:revenue",
                kind="metric",
                name="revenue",
                aspects={"metric": {"formula": "   ", "depends_on": []}},
            )
        ]
    )
    with pytest.raises(CompilerError, match="non-empty formula"):
        validate_contract_nodes(artifact)


def test_empty_query_sql_raises():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="query:empty",
                kind="query",
                name="empty",
                aspects={"query": {"sql": "   ", "depends_on": []}},
            )
        ]
    )
    with pytest.raises(CompilerError, match="non-empty sql"):
        validate_contract_nodes(artifact)


def test_malformed_query_aspect_raises_compiler_error():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="query:bad",
                kind="query",
                name="bad",
                aspects={
                    "query": {
                        "sql": "SELECT 1",
                        "depends_on": [],
                        "parameters": 123,
                    }
                },
            )
        ]
    )
    with pytest.raises(CompilerError, match="query:bad invalid contract aspect"):
        validate_contract_nodes(artifact)


def test_malformed_metric_aspect_raises_compiler_error():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="metric:bad",
                kind="metric",
                name="bad",
                aspects={"metric": {"formula": 123, "depends_on": []}},
            )
        ]
    )
    with pytest.raises(CompilerError, match="metric:bad invalid contract aspect"):
        validate_contract_nodes(artifact)


def test_enforce_graph_rejects_broken_contract_via_compile(tmp_path: Path, monkeypatch):

    from clearmetric.compiler.compile import compile as compile_project

    from tests.backbone_lab.helpers import setup_backbone_lab_project

    monkeypatch.setenv("CM_EXPERIMENTAL", "1")
    project_dir = setup_backbone_lab_project(tmp_path / "broken")
    intent_path = project_dir / "intent" / "metrics.yaml"
    intent_path.write_text(
        "metrics:\n  - id: bad\n    name: Bad\n    formula: sum(x)\n    depends_on: [column:missing.col]\n",
        encoding="utf-8",
    )
    with pytest.raises(CompilerError):
        compile_project(project_dir)


def test_valid_metric_and_query_nodes_pass():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.amount",
                kind="column",
                name="amount",
                qualified_name="orders.amount",
            ),
            Node(
                id="metric:revenue",
                kind="metric",
                name="revenue",
                aspects={
                    "metric": {
                        "formula": "sum(orders.amount)",
                        "depends_on": ["column:orders.amount"],
                    }
                },
            ),
            Node(
                id="query:top_orders",
                kind="query",
                name="top_orders",
                aspects={
                    "query": {
                        "sql": "SELECT amount FROM orders",
                        "depends_on": ["column:orders.amount"],
                    }
                },
            ),
        ]
    )
    validate_contract_nodes(artifact)
