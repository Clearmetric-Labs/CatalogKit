"""JSON emitter."""

from __future__ import annotations

import json

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core import render_json


def emit_json(compiled: CompiledGraph) -> str:
    return json.dumps(render_json(compiled.artifact), indent=2, sort_keys=False)
