"""Emitter registry — sole compile dispatch and gated_context caller."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core.errors import EmitterError
from clearmetric.core.models import CatalogArtifact
from clearmetric.graph import GraphView, select_kinds, view_of
from clearmetric.policy import gated_context
from clearmetric.projection import apply_policy

from .ai_context import serialize_ai_context
from .envelope import wrap_envelope
from .frontend_contract import serialize_frontend_contract
from .json import serialize_artifact
from .openlineage import serialize_openlineage
from .text import serialize_text

Lane = Literal["admin", "consumer"]
SerializeFn = Callable[[CatalogArtifact, CompiledGraph], dict[str, Any] | str]

CATALOG_ASSET_KINDS = frozenset({"table", "column", "model"})
CONSUMER_CATALOG_KINDS = frozenset({"table", "column", "model", "metric", "query"})
AI_CONTEXT_KINDS = frozenset({"table", "column", "model", "metric"})
QUERY_KINDS = frozenset({"query"})


@dataclass(frozen=True)
class FormatSpec:
    lane: Lane
    serialize: SerializeFn
    kinds: frozenset[str] | None = None
    clear_warnings: bool = False


def _slice_artifact(view: GraphView, spec: FormatSpec) -> CatalogArtifact:
    if spec.kinds is None:
        return view.artifact
    return select_kinds(view, spec.kinds, clear_warnings=spec.clear_warnings)


COMPILE_FORMATS: dict[str, FormatSpec] = {
    "json": FormatSpec(
        lane="admin",
        serialize=lambda artifact, _compiled: serialize_artifact(artifact),
    ),
    "text": FormatSpec(
        lane="admin",
        serialize=lambda artifact, compiled: serialize_text(artifact, compiled),
    ),
    "catalog": FormatSpec(
        lane="admin",
        kinds=CATALOG_ASSET_KINDS,
        clear_warnings=True,
        serialize=lambda artifact, _compiled: serialize_artifact(artifact),
    ),
    "openlineage": FormatSpec(
        lane="admin",
        serialize=lambda artifact, compiled: serialize_openlineage(artifact, compiled),
    ),
    "consumer-catalog": FormatSpec(
        lane="consumer",
        kinds=CONSUMER_CATALOG_KINDS,
        clear_warnings=True,
        serialize=lambda artifact, _compiled: serialize_artifact(artifact),
    ),
    "frontend-contract": FormatSpec(
        lane="consumer",
        kinds=QUERY_KINDS,
        serialize=lambda artifact, _compiled: serialize_frontend_contract(artifact),
    ),
    "ai-context": FormatSpec(
        lane="consumer",
        kinds=AI_CONTEXT_KINDS,
        serialize=lambda artifact, _compiled: serialize_ai_context(artifact),
    ),
}

_WEDGE_FORMAT_ORDER = ("json", "text", "openlineage", "catalog")
_LAB_FORMAT_ORDER = ("consumer-catalog", "frontend-contract", "ai-context")

WEDGE_COMPILE_FORMATS = tuple(
    name for name in _WEDGE_FORMAT_ORDER if name in COMPILE_FORMATS
)

LAB_COMPILE_FORMATS = tuple(
    name for name in _LAB_FORMAT_ORDER if name in COMPILE_FORMATS
)


def emit_compile(
    format: str,
    compiled: CompiledGraph,
    *,
    identity: str | None = None,
) -> str:
    spec = COMPILE_FORMATS.get(format)
    if spec is None:
        raise EmitterError(f"unsupported compile format: {format}")

    view = view_of(compiled.artifact)
    artifact = _slice_artifact(view, spec)

    if spec.lane == "admin":
        raw = spec.serialize(artifact, compiled)
        if isinstance(raw, str):
            return raw
        return json.dumps(raw, indent=2, sort_keys=False)

    ctx = gated_context(
        rules_path=compiled.project.policy.rules,
        identity=identity,
    )
    artifact = apply_policy(
        artifact,
        identity=ctx.identity,
        rules=ctx.rules,
    )
    raw = spec.serialize(artifact, compiled)
    if isinstance(raw, str):
        return raw
    return wrap_envelope(format, ctx.identity, artifact, raw)


__all__ = [
    "COMPILE_FORMATS",
    "FormatSpec",
    "LAB_COMPILE_FORMATS",
    "WEDGE_COMPILE_FORMATS",
    "emit_compile",
]
