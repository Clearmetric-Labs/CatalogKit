from __future__ import annotations

import pytest
from clearmetric.core.errors import SecurityFloorError
from clearmetric.core.models import CatalogArtifact, Node
from clearmetric.policy.floor import validate_security_floor


def test_ai_behavior_without_classification_raises():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.email",
                kind="column",
                name="email",
                qualified_name="orders.email",
                aspects={"ai_behavior": {"allowed": True}},
            )
        ]
    )
    with pytest.raises(SecurityFloorError, match="without classification"):
        validate_security_floor(artifact)


def test_classified_node_without_policy_refs_raises():
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:orders.email",
                kind="column",
                name="email",
                qualified_name="orders.email",
                aspects={"classification": "pii"},
            )
        ]
    )
    with pytest.raises(SecurityFloorError, match="policy_refs"):
        validate_security_floor(artifact)


def test_nodes_without_aspects_skip_checks():
    validate_security_floor(
        CatalogArtifact(
            nodes=[
                Node(
                    id="column:orders.amount",
                    kind="column",
                    name="amount",
                    qualified_name="orders.amount",
                )
            ]
        )
    )
