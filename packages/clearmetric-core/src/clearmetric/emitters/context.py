"""Emitter context for policy-gated lab formats."""

from __future__ import annotations

from dataclasses import dataclass

from clearmetric.compiler.models import CompiledGraph
from clearmetric.policy import load_gated_context
from clearmetric.policy.models import PolicyRulesFile


@dataclass(frozen=True)
class EmitContext:
    identity: str
    rules: PolicyRulesFile


def emit_context(compiled: CompiledGraph, *, identity: str | None) -> EmitContext:
    resolved_identity, rules = load_gated_context(
        rules_path=compiled.project.policy.rules,
        identity=identity,
    )
    return EmitContext(identity=resolved_identity, rules=rules)


__all__ = ["EmitContext", "emit_context"]
