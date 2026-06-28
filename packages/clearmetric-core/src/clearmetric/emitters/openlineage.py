"""OpenLineage emitter."""

from __future__ import annotations

import json

from clearmetric.compiler.models import CompiledGraph
from clearmetric.lineage import build_openlineage_export


def emit_openlineage(compiled: CompiledGraph) -> str:
    payload = build_openlineage_export(
        compiled.artifact,
        job_name=compiled.project_dir.name,
    )
    return json.dumps(payload, indent=2, sort_keys=False)
