"""Resolve repository paths for example notebooks."""

from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    for candidate in (start, *start.parents):
        if (candidate / "packages" / "clearmetric-core").is_dir():
            return candidate
    raise FileNotFoundError(
        "ClearMetric-Core repo root not found. "
        "Start Jupyter from the repository or examples/notebooks/."
    )


def wedge_project(start: Path | None = None) -> Path:
    """Public quickstart project (examples/lineage-demo)."""
    return repo_root(start) / "examples" / "lineage-demo"


def backbone_lab_project(start: Path | None = None) -> Path:
    return repo_root(start) / "examples" / "backbone-lab"


def consumer_bundle_dir(
    scenario_id: str = "minimal", start: Path | None = None
) -> Path:
    return repo_root(start) / "examples" / "consumers" / "bundles" / scenario_id


def consumer_scenario(scenario_id: str = "minimal", start: Path | None = None) -> Path:
    return repo_root(start) / "examples" / "consumers" / "scenarios" / scenario_id


def build_bundle_script(start: Path | None = None) -> Path:
    return repo_root(start) / "scripts" / "consumers" / "build_bundle.py"
