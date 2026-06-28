"""Corpus checks against committed consumer bundles."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.consumers.checks_runner import run_checks

REPO_ROOT = Path(__file__).resolve().parents[4]
SCENARIOS_ROOT = REPO_ROOT / "examples" / "consumers" / "scenarios"
REGISTRY = SCENARIOS_ROOT / "registry.yaml"


def _ci_scenarios() -> list[tuple[str, Path]]:
    payload = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios") or []
    result: list[tuple[str, Path]] = []
    for entry in scenarios:
        if not entry.get("ci"):
            continue
        scenario_id = str(entry["id"])
        bundle_rel = str(entry["bundle_dir"])
        bundle_dir = (SCENARIOS_ROOT / bundle_rel).resolve()
        result.append((scenario_id, bundle_dir))
    return result


@pytest.mark.parametrize(
    ("scenario_id", "bundle_dir"),
    _ci_scenarios(),
    ids=[item[0] for item in _ci_scenarios()],
)
def test_corpus_checks(scenario_id: str, bundle_dir: Path):
    checks_path = SCENARIOS_ROOT / scenario_id / "checks.yaml"
    violations = run_checks(bundle_dir, checks_path)
    assert violations == [], "\n".join(violations)
