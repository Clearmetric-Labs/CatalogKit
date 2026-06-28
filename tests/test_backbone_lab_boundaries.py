"""Public surface boundary tests for backbone lab."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _readme_shipped_section() -> str:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(
        r"## Features(.*?)## ",
        readme,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(1).lower()


def _v1_in_scope_section() -> str:
    boundary = (REPO_ROOT / "docs" / "v1-boundary.md").read_text(encoding="utf-8")
    match = re.search(
        r"### In scope(.*?)### Out of scope",
        boundary,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(1).lower()


def test_readme_shipped_section_does_not_list_lab_capabilities():
    shipped = _readme_shipped_section()
    for banned in ("consumer-catalog", "frontend-contract"):
        assert banned not in shipped


def test_v1_in_scope_does_not_list_lab_capabilities():
    in_scope = _v1_in_scope_section()
    for banned in ("consumer-catalog", "frontend-contract", "cm query", "cm serve"):
        assert banned not in in_scope


def test_normal_help_hides_lab_formats():
    result = subprocess.run(
        [sys.executable, "-m", "clearmetric.cli", "compile", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={k: v for k, v in os.environ.items() if k != "CM_EXPERIMENTAL"},
    )
    assert result.returncode == 0
    help_text = result.stdout.lower()
    assert "consumer-catalog" not in help_text
    assert "frontend-contract" not in help_text


def test_experimental_help_shows_lab_formats():
    env = os.environ.copy()
    env["CM_EXPERIMENTAL"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "clearmetric.cli", "compile", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0
    help_text = result.stdout.lower()
    assert "consumer-catalog" in help_text
    assert "frontend-contract" in help_text
    assert "ai-context" in help_text


def test_experimental_query_command_requires_env():
    result = subprocess.run(
        [sys.executable, "-m", "clearmetric.cli", "query", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={k: v for k, v in os.environ.items() if k != "CM_EXPERIMENTAL"},
    )
    assert result.returncode != 0
