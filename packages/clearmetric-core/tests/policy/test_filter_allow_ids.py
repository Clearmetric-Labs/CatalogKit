"""filter_allow_only_ids tests."""

from __future__ import annotations

import pytest
from clearmetric.core.errors import GraphError
from clearmetric.core.models import CatalogArtifact, Node
from clearmetric.graph import view_of
from clearmetric.policy import filter_allow_only_ids
from clearmetric.policy.models import PolicyRule, PolicyRulesFile, PolicySelector


def test_filter_allow_only_ids_includes_allow_excludes_default_deny():
    artifact = CatalogArtifact(
        nodes=[
            Node(id="column:orders.amount", kind="column", name="amount"),
            Node(id="table:orders", kind="table", name="orders"),
        ]
    )
    view = view_of(artifact)
    rules = PolicyRulesFile(
        rules=[
            PolicyRule(
                id="allow-columns",
                kind="rbac",
                identity="analyst",
                effect="allow",
                selector=PolicySelector(kind="column"),
            ),
        ]
    )
    allowed = filter_allow_only_ids(
        node_ids=["column:orders.amount", "table:orders"],
        resolve_node=view.node,
        identity="analyst",
        rules=rules,
    )
    assert allowed == ["column:orders.amount"]


def test_filter_allow_only_ids_excludes_mask_decision():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.email",
                kind="column",
                name="email",
                aspects={"classification": "pii", "policy_refs": ["policy/email"]},
            ),
        ]
    )
    view = view_of(artifact)
    rules = PolicyRulesFile(
        rules=[
            PolicyRule(
                id="mask-pii",
                kind="masking",
                identity="analyst",
                effect="mask",
                selector=PolicySelector(kind="column"),
            ),
        ]
    )
    allowed = filter_allow_only_ids(
        node_ids=["column:orders.email"],
        resolve_node=view.node,
        identity="analyst",
        rules=rules,
    )
    assert allowed == []


def test_filter_allow_only_ids_propagates_missing_node():
    artifact = CatalogArtifact(nodes=[Node(id="column:a", kind="column", name="a")])
    view = view_of(artifact)
    with pytest.raises(GraphError):
        filter_allow_only_ids(
            node_ids=["column:missing"],
            resolve_node=view.node,
            identity="analyst",
            rules=PolicyRulesFile(),
        )
