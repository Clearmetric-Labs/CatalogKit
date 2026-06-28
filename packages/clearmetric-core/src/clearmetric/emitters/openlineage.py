"""OpenLineage serializer — target serialization lives here, not in lineage build."""

from __future__ import annotations

import json
from typing import Any

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core.models import CatalogArtifact
from clearmetric.graph import column_selection_from_id, derives_from_edges, view_of


def build_openlineage_payload(
    artifact: CatalogArtifact,
    *,
    job_name: str = "clearmetric",
) -> dict[str, Any]:
    input_fields_by_output: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    for edge in derives_from_edges(view_of(artifact)):
        output_dataset, output_column = column_selection_from_id(edge.source_id)
        input_dataset, input_column = column_selection_from_id(edge.target_id)
        input_fields_by_output.setdefault((output_dataset, output_column), set()).add(
            ("clearmetric", input_dataset, input_column)
        )

    export_entries = [
        {
            "dataset": output_dataset,
            "column": output_column,
            "inputFields": [
                {
                    "namespace": namespace,
                    "name": input_dataset,
                    "field": input_column,
                }
                for namespace, input_dataset, input_column in sorted(input_fields)
            ],
        }
        for (output_dataset, output_column), input_fields in sorted(
            input_fields_by_output.items()
        )
    ]

    datasets = [
        {
            "namespace": "clearmetric",
            "name": node.qualified_name or node.name,
            "kind": node.kind,
        }
        for node in sorted(
            artifact.nodes, key=lambda item: item.qualified_name or item.name
        )
        if node.kind == "table"
    ]

    return {
        "job": {
            "namespace": "clearmetric",
            "name": job_name,
        },
        "datasets": datasets,
        "columnLineage": export_entries,
    }


def serialize_openlineage(artifact: CatalogArtifact, compiled: CompiledGraph) -> str:
    payload = build_openlineage_payload(
        artifact,
        job_name=compiled.project_dir.name,
    )
    return json.dumps(payload, indent=2, sort_keys=False)


__all__ = ["build_openlineage_payload", "serialize_openlineage"]
