"""Report-only clean orchestration."""

from __future__ import annotations

from pathlib import Path

from clearmetric.cleaner import run_compile_checks
from clearmetric.cleaner.models import CleanerReport

from .compile import compile
from .models import CompiledGraph


def clean(project_dir: Path) -> tuple[CleanerReport, CompiledGraph]:
    compiled = compile(project_dir)
    report = run_compile_checks(compiled.artifact)
    return report, compiled
