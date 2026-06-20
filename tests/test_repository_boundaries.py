from __future__ import annotations

import ast
from pathlib import Path

from catalogkit.core import merge
from catalogkit.lineage import build_catalog_artifact as build_lineage_catalog_artifact
from catalogkit.query import build_catalog_artifact as build_query_catalog_artifact

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_ROOT = REPO_ROOT / "packages"
PACKAGE_SOURCE_ROOTS = {
    "catalogkit-core": PACKAGES_ROOT
    / "catalogkit-core"
    / "src"
    / "catalogkit"
    / "core",
    "catalogkit-query": PACKAGES_ROOT
    / "catalogkit-query"
    / "src"
    / "catalogkit"
    / "query",
    "catalogkit-lineage": PACKAGES_ROOT
    / "catalogkit-lineage"
    / "src"
    / "catalogkit"
    / "lineage",
}
SHARED_CLASS_NAMES = {"Node", "Edge", "Evidence", "Warning"}
ALLOWED_MODULES_BY_PACKAGE = {
    "catalogkit-core": {"catalogkit.core"},
    "catalogkit-query": {"catalogkit.core", "catalogkit.query"},
    "catalogkit-lineage": {"catalogkit.core", "catalogkit.lineage"},
}
PROPRIETARY_IMPORT_PREFIXES = (
    "apps",
    "auth",
    "clearmetric",
    "config",
    "database",
    "models",
    "services",
    "shared_config",
)


def test_tool_packages_only_depend_on_catalogkit_core_and_themselves():
    violations: list[str] = []

    for package_name, package_root in PACKAGE_SOURCE_ROOTS.items():
        allowed_modules = ALLOWED_MODULES_BY_PACKAGE[package_name]

        for path in package_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(
                            "catalogkit."
                        ) and not _is_allowed_module(
                            alias.name,
                            allowed_modules,
                        ):
                            violations.append(f"{path}: import {alias.name}")
                elif (
                    isinstance(node, ast.ImportFrom) and node.module and node.level == 0
                ):
                    if node.module.startswith("catalogkit.") and not _is_allowed_module(
                        node.module,
                        allowed_modules,
                    ):
                        violations.append(f"{path}: from {node.module} import ...")

    assert violations == []


def test_tool_packages_do_not_import_enterprise_or_proprietary_prefixes():
    violations: list[str] = []

    for package_root in PACKAGE_SOURCE_ROOTS.values():
        for path in package_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if _has_banned_prefix(alias.name):
                            violations.append(f"{path}: import {alias.name}")
                elif (
                    isinstance(node, ast.ImportFrom) and node.module and node.level == 0
                ):
                    if _has_banned_prefix(node.module):
                        violations.append(f"{path}: from {node.module} import ...")

    assert violations == []


def test_shared_model_class_names_exist_only_in_catalogkit_core():
    violations: list[str] = []
    core_models_path = (
        PACKAGES_ROOT / "catalogkit-core" / "src" / "catalogkit" / "core" / "models.py"
    )

    for path in PACKAGES_ROOT.rglob("*.py"):
        if path == core_models_path:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in SHARED_CLASS_NAMES:
                violations.append(f"{path}: class {node.name}")

    assert violations == []


def test_no_namespace_root_init_file_exists():
    violations = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in PACKAGES_ROOT.rglob("catalogkit/__init__.py")
    )
    assert violations == []


def test_tool_artifacts_merge_on_shared_ids():
    example_root = (
        PACKAGES_ROOT / "catalogkit-lineage" / "examples" / "jaffle_shop"
    ).resolve()
    manifest_path = example_root / "manifest.json"
    customers_sql = (example_root / "compiled" / "customers.sql").read_text(
        encoding="utf-8"
    )

    lineage_artifact = build_lineage_catalog_artifact(manifest_path, dialect="postgres")
    query_artifact = build_query_catalog_artifact(customers_sql, dialect="postgres")
    merged = merge(lineage_artifact, query_artifact)

    stg_orders_nodes = [node for node in merged.nodes if node.id == "table:stg_orders"]
    raw_payments_nodes = [
        node for node in merged.nodes if node.id == "table:raw_payments"
    ]

    assert len(stg_orders_nodes) == 1
    assert len(raw_payments_nodes) == 1


def _is_allowed_module(module_name: str, allowed_modules: set[str]) -> bool:
    return any(
        module_name == allowed or module_name.startswith(f"{allowed}.")
        for allowed in allowed_modules
    )


def _has_banned_prefix(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in PROPRIETARY_IMPORT_PREFIXES
    )
