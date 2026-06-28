from __future__ import annotations

from pathlib import Path

from clearmetric.compiler.compile import compile as compile_project

from tests.wedge.helpers import setup_wedge_project


def test_compile_project(tmp_path: Path):
    compiled = compile_project(setup_wedge_project(tmp_path))
    assert compiled.project.dialect == "postgres"
    assert compiled.artifact.nodes
