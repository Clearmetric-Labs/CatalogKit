"""Projection tests."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact, Node
from clearmetric.policy.models import PolicyRule, PolicyRulesFile, PolicySelector
from clearmetric.projection import apply_policy


def test_apply_policy_filters_denied_nodes():
    artifact = CatalogArtifact(
        nodes=[
            Node(id="column:orders.amount", kind="column", name="amount"),
            Node(id="table:orders", kind="table", name="orders"),
        ]
    )
    rules = PolicyRulesFile(
        rules=[
            PolicyRule(
                id="allow-columns",
                kind="rbac",
                identity="viewer",
                effect="allow",
                selector=PolicySelector(kind="column"),
            ),
            PolicyRule(
                id="deny-tables",
                kind="rbac",
                identity="viewer",
                effect="deny",
                selector=PolicySelector(kind="table"),
            ),
        ]
    )
    projected = apply_policy(artifact, identity="viewer", rules=rules)
    assert {node.id for node in projected.nodes} == {"column:orders.amount"}
