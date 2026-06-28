#!/usr/bin/env python3
"""Build or validate a consumer artifact bundle from a scenario recipe."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from clearmetric.cli.runner import run_cm
from clearmetric.core import __version__ as clearmetric_version
from clearmetric.core.errors import ValidationError
from clearmetric.core.validate import (
    load_artifact_file,
    load_bundle_manifest_file,
    load_impact_output_file,
    validate_bundle_artifact_file,
    validate_bundle_manifest_dict,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_BUNDLES = _REPO_ROOT / "examples" / "consumers" / "bundles"


def _load_scenario(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Scenario must be a YAML mapping: {path}")
    return payload


def _resolve_project_dir(scenario_path: Path, scenario: dict[str, Any]) -> Path:
    project_dir = scenario.get("project_dir")
    if not isinstance(project_dir, str) or not project_dir.strip():
        raise SystemExit("project_dir is required for mode=project")
    resolved = (scenario_path.parent / project_dir).resolve()
    if not resolved.is_dir():
        raise SystemExit(f"project_dir does not exist: {resolved}")
    return resolved


def _resolve_bundle_dir(
    scenario_path: Path,
    scenario: dict[str, Any],
    out: Path | None,
    *,
    mode: str,
) -> Path:
    if out is not None:
        return out.resolve()
    if mode == "prebuilt":
        bundle_dir = scenario.get("bundle_dir")
        if isinstance(bundle_dir, str) and bundle_dir.strip():
            resolved = (scenario_path.parent / bundle_dir.strip()).resolve()
            if not resolved.is_dir():
                raise SystemExit(f"bundle_dir does not exist: {resolved}")
            return resolved
    scenario_id = str(scenario.get("id") or scenario_path.parent.name)
    return (_DEFAULT_BUNDLES / scenario_id).resolve()


def _write_and_validate_output(
    out_dir: Path,
    relative_path: str,
    content: str,
    *,
    lane: str,
    kind: str,
) -> None:
    target = out_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    if kind == "catalog-artifact":
        validate_bundle_artifact_file(target, lane=lane)
        return
    if kind == "impact-output":
        load_impact_output_file(target)
        return
    raise SystemExit(f"Unsupported artifact kind: {kind}")


def _build_project_bundle(
    scenario_path: Path,
    scenario: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    project_dir = _resolve_project_dir(scenario_path, scenario)
    outputs = scenario.get("outputs")
    impacts = scenario.get("impacts")
    if not isinstance(outputs, list) or not outputs:
        raise SystemExit("outputs must be a non-empty list")
    if not isinstance(impacts, list) or not impacts:
        raise SystemExit("impacts must be a non-empty list")

    artifact_refs: dict[str, Any] = {}
    for item in outputs:
        if not isinstance(item, dict):
            raise SystemExit("each output must be a mapping")
        compile_format = str(item.get("compile_format") or "").strip()
        relative_out = str(item.get("out") or "").strip()
        lane = str(item.get("lane") or "admin").strip()
        if not compile_format or not relative_out:
            raise SystemExit("each output requires compile_format and out")
        result = run_cm(project_dir, "compile", "--format", compile_format)
        if result.returncode != 0:
            raise SystemExit(
                f"cm compile --format {compile_format} failed:\n{result.stderr}"
            )
        key = "graph" if compile_format == "json" else compile_format
        _write_and_validate_output(
            out_dir,
            relative_out,
            result.stdout,
            lane=lane,
            kind="catalog-artifact",
        )
        ref: dict[str, Any] = {
            "path": relative_out,
            "kind": "catalog-artifact",
            "lane": lane,
        }
        identity = item.get("identity")
        if identity is not None:
            ref["identity"] = str(identity)
        artifact_refs[key] = ref

    if "graph" not in artifact_refs or "catalog" not in artifact_refs:
        raise SystemExit("outputs must include json (graph) and catalog")

    impact_refs: dict[str, Any] = {}
    for item in impacts:
        if not isinstance(item, dict):
            raise SystemExit("each impact must be a mapping")
        selection = str(item.get("selection") or "").strip()
        direction = str(item.get("direction") or "").strip()
        manifest_key = str(item.get("manifest_key") or "").strip()
        relative_out = str(item.get("out") or "").strip()
        if not selection or not direction or not manifest_key or not relative_out:
            raise SystemExit(
                "each impact requires selection, direction, manifest_key, and out"
            )
        flag = "--upstream" if direction == "upstream" else "--downstream"
        result = run_cm(project_dir, "impact", selection, flag, "--format", "json")
        if result.returncode != 0:
            raise SystemExit(f"cm impact failed for {selection}:\n{result.stderr}")
        _write_and_validate_output(
            out_dir,
            relative_out,
            result.stdout,
            lane="admin",
            kind="impact-output",
        )
        impact_refs[manifest_key] = {
            "path": relative_out,
            "selection": selection,
            "direction": direction,
        }

    default_key = str(impacts[0].get("manifest_key") or "").strip()
    manifest = {
        "schema_version": "1",
        "scenario_id": str(scenario.get("id") or scenario_path.parent.name),
        "label": str(scenario.get("label") or scenario_path.parent.name),
        "artifacts": {
            "graph": artifact_refs["graph"],
            "catalog": artifact_refs["catalog"],
            "impacts": impact_refs,
        },
        "defaults": {"impact_key": default_key},
    }
    provenance = scenario.get("provenance")
    if isinstance(provenance, str) and provenance.strip():
        manifest["provenance"] = provenance.strip()
    return manifest


def _validate_prebuilt_bundle(out_dir: Path) -> dict[str, Any]:
    manifest_path = out_dir / "bundle.manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(
            f"prebuilt bundle missing bundle.manifest.json: {manifest_path}"
        )
    try:
        manifest = load_bundle_manifest_file(manifest_path)
    except ValidationError as exc:
        raise SystemExit(f"bundle.manifest.json validation failed:\n{exc}") from exc
    artifacts = manifest["artifacts"]
    for key in ("graph", "catalog"):
        ref = artifacts[key]
        validate_bundle_artifact_file(out_dir / ref["path"], lane=ref["lane"])
    for ref in artifacts["impacts"].values():
        load_impact_output_file(out_dir / ref["path"])
    return manifest


def _write_meta(out_dir: Path, manifest: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "clearmetric_version": clearmetric_version,
        "scenario_id": manifest["scenario_id"],
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )


def _write_manifest_and_meta(out_dir: Path, manifest: dict[str, Any]) -> None:
    try:
        validate_bundle_manifest_dict(manifest)
    except ValidationError as exc:
        raise SystemExit(f"bundle manifest validation failed:\n{exc}") from exc
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "bundle.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_meta(out_dir, manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        required=True,
        type=Path,
        help="Path to scenario.yaml or scenario directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output bundle directory (default: examples/consumers/bundles/<id>/)",
    )
    args = parser.parse_args(argv)

    scenario_path = args.scenario.resolve()
    if scenario_path.is_dir():
        scenario_path = scenario_path / "scenario.yaml"
    if not scenario_path.is_file():
        raise SystemExit(f"Scenario file not found: {scenario_path}")

    scenario = _load_scenario(scenario_path)
    mode = str(scenario.get("mode") or "project").strip()
    out_dir = _resolve_bundle_dir(scenario_path, scenario, args.out, mode=mode)

    if mode == "project":
        manifest = _build_project_bundle(scenario_path, scenario, out_dir)
        _write_manifest_and_meta(out_dir, manifest)
    elif mode == "prebuilt":
        manifest = _validate_prebuilt_bundle(out_dir)
        _write_meta(out_dir, manifest)
    else:
        raise SystemExit(f"Unsupported scenario mode: {mode!r}")

    graph_path = out_dir / manifest["artifacts"]["graph"]["path"]
    load_artifact_file(graph_path)
    print(f"bundle ready: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
