"""Policy models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PolicyDecision = Literal["allow", "deny", "mask", "filter"]
PolicyKind = Literal["rbac", "rls", "masking", "ai_permission", "export"]
PolicyEffect = Literal["allow", "deny", "mask"]

SENSITIVE_ASPECT_KEYS = frozenset(
    {"classification", "policy_refs", "ai_behavior", "pii", "confidential"}
)


def strip_sensitive_aspects(aspects: dict) -> dict:
    """Drop governance metadata keys before consumer-facing export."""
    cleaned = dict(aspects)
    for key in SENSITIVE_ASPECT_KEYS:
        cleaned.pop(key, None)
    return cleaned


class PolicySelector(BaseModel):
    kind: str | None = None


class PolicyRule(BaseModel):
    id: str
    kind: PolicyKind
    identity: str
    effect: PolicyEffect = "allow"
    selector: PolicySelector | None = None


class PolicyRulesFile(BaseModel):
    rules: list[PolicyRule] = Field(default_factory=list)
