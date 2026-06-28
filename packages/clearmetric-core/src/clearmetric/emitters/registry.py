"""Emitter registry — wedge formats + experimental lab formats."""

from __future__ import annotations

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core.errors import EmitterError

from .catalog import emit_catalog
from .consumer_catalog import emit_consumer_catalog
from .context import emit_context
from .frontend_contract import emit_frontend_contract
from .json import emit_json
from .openlineage import emit_openlineage
from .text import emit_text

WEDGE_COMPILE_FORMATS = ("json", "text", "openlineage", "catalog")
LAB_COMPILE_FORMATS = ("consumer-catalog", "frontend-contract")
GATED_COMPILE_FORMATS = frozenset(LAB_COMPILE_FORMATS)


def emit_compile(
    format: str,
    compiled: CompiledGraph,
    *,
    identity: str | None = None,
) -> str:
    if format == "json":
        return emit_json(compiled)
    if format == "text":
        return emit_text(compiled)
    if format == "catalog":
        return emit_catalog(compiled)
    if format == "openlineage":
        return emit_openlineage(compiled)
    if format in GATED_COMPILE_FORMATS:
        ctx = emit_context(compiled, identity=identity)
        if format == "consumer-catalog":
            return emit_consumer_catalog(
                compiled, identity=ctx.identity, rules=ctx.rules
            )
        return emit_frontend_contract(compiled, identity=ctx.identity, rules=ctx.rules)

    raise EmitterError(f"unsupported compile format: {format}")
