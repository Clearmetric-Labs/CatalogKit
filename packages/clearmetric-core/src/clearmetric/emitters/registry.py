"""Emitter registry — wedge formats only."""

from __future__ import annotations

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core.errors import EmitterError

from .catalog import emit_catalog
from .json import emit_json
from .openlineage import emit_openlineage
from .text import emit_text


def emit_compile(format: str, compiled: CompiledGraph) -> str:
    if format == "json":
        return emit_json(compiled)
    if format == "text":
        return emit_text(compiled)
    if format == "catalog":
        return emit_catalog(compiled)
    if format == "openlineage":
        return emit_openlineage(compiled)

    raise EmitterError(f"unsupported compile format: {format}")
