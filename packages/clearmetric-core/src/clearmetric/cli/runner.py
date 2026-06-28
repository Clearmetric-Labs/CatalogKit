"""Shared subprocess helper for invoking the ClearMetric CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_cm(
    project_dir: Path,
    *args: str,
    experimental: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run ``python -m clearmetric.cli --project-dir …`` and capture output."""
    env = os.environ.copy()
    if experimental:
        env["CM_EXPERIMENTAL"] = "1"
    else:
        env.pop("CM_EXPERIMENTAL", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "clearmetric.cli",
            "--project-dir",
            str(project_dir),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


__all__ = ["run_cm"]
