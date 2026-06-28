"""Projection tests."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact, Node, Warning
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


def test_apply_policy_strips_governance_aspects_on_allow():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.amount",
                kind="column",
                name="amount",
                aspects={
                    "classification": "internal",
                    "policy_refs": ["policy/orders"],
                },
            )
        ]
    )
    rules = PolicyRulesFile(
        rules=[
            PolicyRule(
                id="allow-columns",
                kind="rbac",
                identity="analyst",
                effect="allow",
                selector=PolicySelector(kind="column"),
            )
        ]
    )
    projected = apply_policy(artifact, identity="analyst", rules=rules)
    aspects = projected.nodes[0].aspects or {}
    assert "classification" not in aspects
    assert "policy_refs" not in aspects


def test_apply_policy_filters_warnings_for_denied_subjects():
    artifact = CatalogArtifact(
        nodes=[
            Node(id="column:orders.amount", kind="column", name="amount"),
            Node(id="table:orders", kind="table", name="orders"),
        ],
        warnings=[
            Warning(code="visible", message="ok", subject_id="column:orders.amount"),
            Warning(code="hidden", message="drop", subject_id="table:orders"),
            Warning(code="global", message="keep", subject_id=None),
        ],
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
    codes = {warning.code for warning in projected.warnings}
    assert codes == {"visible", "global"}
    assert "hidden" not in codes
