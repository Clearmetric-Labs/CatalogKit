"""Policy gate — sole consumer authorization entry."""

from __future__ import annotations

from clearmetric.core.errors import PolicyDeniedError, SecurityFloorError
from clearmetric.core.models import CatalogArtifact, Node
from clearmetric.policy.floor import validate_security_floor

from .evaluate import evaluate_node
from .models import PolicyDecision, PolicyRulesFile


def gate(*, node: Node, identity: str, rules: PolicyRulesFile) -> PolicyDecision:
    """Evaluate policy for one node; fail closed on errors or floor violations."""
    try:
        decision = evaluate_node(node=node, identity=identity, rules=rules)
        if decision in {"deny", "filter"}:
            return decision
        try:
            validate_security_floor(CatalogArtifact(nodes=[node]))
        except SecurityFloorError:
            return "deny"
        return decision
    except Exception:
        return "deny"


def require_allow(*, node: Node, identity: str, rules: PolicyRulesFile) -> None:
    """Raise when gate does not return allow (execute paths; mask/filter/deny fail closed)."""
    if gate(node=node, identity=identity, rules=rules) != "allow":
        raise PolicyDeniedError(f"{node.id} denied by policy for identity {identity!r}")


__all__ = ["gate", "require_allow"]
