"""Security floor validation."""

from __future__ import annotations

from clearmetric.core.errors import SecurityFloorError
from clearmetric.core.models import CatalogArtifact, Node


def validate_security_floor(artifact: CatalogArtifact) -> None:
    violations: list[str] = []
    for node in artifact.nodes:
        violations.extend(_node_violations(node))
    if violations:
        raise SecurityFloorError("; ".join(violations))


def _node_violations(node: Node) -> list[str]:
    if not node.aspects:
        return []
    violations: list[str] = []
    ai_behavior = node.aspects.get("ai_behavior")
    if isinstance(ai_behavior, dict) and ai_behavior.get("allowed") is True:
        classification = node.aspects.get("classification")
        if not classification:
            violations.append(
                f"{node.id} exposes AI behavior without classification aspect"
            )
    classification = node.aspects.get("classification")
    if classification in {"pii", "confidential"}:
        policy_refs = node.aspects.get("policy_refs")
        if not policy_refs:
            violations.append(
                f"{node.id} is classified {classification!r} without policy_refs"
            )
    return violations
