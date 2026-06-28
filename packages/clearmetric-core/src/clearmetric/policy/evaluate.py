"""Policy evaluation."""

from __future__ import annotations

from clearmetric.core.models import Node

from .models import PolicyDecision, PolicyRulesFile


def evaluate(*, node: Node, identity: str, rules: PolicyRulesFile) -> PolicyDecision:
    try:
        for rule in rules.rules:
            if rule.effect != "allow":
                continue
            if rule.identity != identity:
                continue
            if rule.selector is not None and rule.selector.kind is not None:
                if rule.selector.kind != node.kind:
                    continue
            return "allow"
        return "deny"
    except Exception:
        # Policy evaluation must fail closed when rule matching breaks.
        return "deny"
