"""Link metrics pipeline tests."""

from __future__ import annotations

import pytest
from clearmetric.compiler.link_metrics import link_contract_dependencies
from clearmetric.core.errors import CompilerError
from clearmetric.core.models import CatalogArtifact, Node


def test_link_metrics_adds_depends_on_edges():
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
                        "formula": "sum(amount)",
                        "depends_on": ["column:orders.amount"],
                    }
                },
            ),
        ]
    )
    linked = link_contract_dependencies(artifact)
    assert any(
        edge.kind == "depends_on"
        and edge.source_id == "column:orders.amount"
        and edge.target_id == "metric:revenue"
        for edge in linked.edges
    )


def test_link_metrics_raises_on_missing_depends_on():
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
        link_contract_dependencies(artifact)
