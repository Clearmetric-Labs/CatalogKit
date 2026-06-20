from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from catalogkit.lineage import __version__
from catalogkit.lineage.cli import main


def _example_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "jaffle_shop"


def _folder_example_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "sql_folder"


def test_cli_text_output_for_manifest(capsys):
    manifest_path = _example_root() / "manifest.json"

    exit_code = main(["--dialect", "postgres", str(manifest_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "catalogkit-lineage" in captured.out
    assert "dataset_count:" in captured.out


def test_cli_json_output_for_folder(capsys):
    compiled_dir = _folder_example_root()

    exit_code = main(["--dialect", "postgres", "--format", "json", str(compiled_dir)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["summary"]["input_kind"] == "sql_folder"
    assert payload["nodes"]


def test_cli_downstream_output(capsys):
    compiled_dir = _folder_example_root()

    exit_code = main(
        [
            "--dialect",
            "postgres",
            "--downstream",
            "orders_base.amount",
            str(compiled_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "column:customer_totals.total_amount" in captured.out


def test_cli_openlineage_output(capsys):
    manifest_path = _example_root() / "manifest.json"

    exit_code = main(
        ["--dialect", "postgres", "--format", "openlineage", str(manifest_path)]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["job"]["name"] == "jaffle_shop"


def test_module_entrypoint_runs_from_package_root():
    package_root = Path(__file__).resolve().parents[1]
    manifest_path = package_root / "examples" / "jaffle_shop" / "manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "catalogkit.lineage",
            "--dialect",
            "postgres",
            str(manifest_path),
        ],
        cwd=package_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "catalogkit-lineage" in result.stdout


def test_cli_version_output(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert captured.out.strip() == f"catalogkit-lineage {__version__}"
