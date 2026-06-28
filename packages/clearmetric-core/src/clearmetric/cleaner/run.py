"""Cleaner execution."""

from __future__ import annotations

from clearmetric.core.errors import StructuralCheckError
from clearmetric.core.models import CatalogArtifact, Warning

from .checks import check_edges_resolve, check_unique_node_ids
from .models import CleanerReport, Finding


def run_structural_checks(artifact: CatalogArtifact) -> CleanerReport:
    findings = [
        *check_unique_node_ids(artifact),
        *check_edges_resolve(artifact),
    ]
    return CleanerReport(findings=findings)


def findings_from_warnings(warnings: list[Warning]) -> list[Finding]:
    findings: list[Finding] = []
    for warning in warnings:
        if warning.code not in {"schema_drift", "source_disagreement"}:
            continue
        findings.append(
            Finding(
                check_id=f"check.{warning.code}",
                node_id=warning.subject_id,
                severity="warn",
                message=warning.message,
            )
        )
    return findings


def run_compile_checks(artifact: CatalogArtifact) -> CleanerReport:
    report = run_structural_checks(artifact)
    report.findings.extend(findings_from_warnings(artifact.warnings))
    return report


def enforce_structural_checks(artifact: CatalogArtifact) -> None:
    report = run_structural_checks(artifact)
    errors = [finding for finding in report.findings if finding.severity == "error"]
    if not errors:
        return
    messages = "; ".join(f"{finding.check_id}: {finding.message}" for finding in errors)
    raise StructuralCheckError(messages)
