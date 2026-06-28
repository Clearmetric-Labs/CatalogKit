"""JSON Schema validation for ClearMetric Core."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .errors import ValidationError
from .models import CatalogArtifact


@lru_cache(maxsize=8)
def _load_schema(name: str) -> dict[str, Any]:
    path = files("clearmetric.spec").joinpath(name)
    if not path.is_file():
        raise ValidationError(f"Schema not packaged: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(data: dict[str, Any], schema_name: str) -> dict[str, Any]:
    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise ValidationError(
            f"{schema_name} validation failed at {path}: {first.message}"
        )
    return data


def validate_project_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a project config dict against the project schema."""
    return _validate(data, "clearmetric-project.schema.json")


def validate_artifact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate an artifact dict against the artifact schema."""
    return _validate(data, "catalog-artifact.schema.json")


def collect_schema_errors(data: dict[str, Any], schema_name: str) -> list[str]:
    """Collect all schema validation errors (batch loud failure at adapter boundary)."""
    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema)
    messages: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda err: list(err.path)):
        path = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{path}: {error.message}")
    return messages


def load_artifact_file(path: Path) -> CatalogArtifact:
    """Load and validate a catalog artifact JSON file."""
    payload = _load_json_object(path)
    validate_artifact_dict(payload)
    return CatalogArtifact.model_validate(payload)


def validate_bundle_manifest_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a bundle manifest dict against the consumer bundle schema."""
    validated = _validate(data, "consumer-bundle.schema.json")
    impact_key = validated["defaults"]["impact_key"]
    impacts = validated["artifacts"]["impacts"]
    if impact_key not in impacts:
        raise ValidationError(
            f"defaults.impact_key {impact_key!r} not found in artifacts.impacts"
        )
    return validated


def validate_impact_output_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate impact CLI JSON output against the impact output schema."""
    return _validate(data, "impact-output.schema.json")


def validate_consumer_envelope_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a consumer-lane emit envelope dict."""
    return _validate(data, "consumer-envelope.schema.json")


def validate_bundle_artifact_file(path: Path, *, lane: str) -> dict[str, Any]:
    """Validate an artifact file according to manifest lane (admin or consumer)."""
    payload = _load_json_object(path)
    if lane == "admin":
        if "format" in payload and "payload" in payload:
            raise ValidationError(
                f"Admin lane artifact must not be wrapped in consumer envelope: {path}"
            )
        return validate_artifact_dict(payload)
    if lane == "consumer":
        envelope = validate_consumer_envelope_dict(payload)
        validate_artifact_dict(envelope["payload"])
        return envelope
    raise ValidationError(f"Unsupported lane {lane!r} for artifact: {path}")


def load_bundle_manifest_file(path: Path) -> dict[str, Any]:
    """Load and validate a bundle.manifest.json file."""
    payload = _load_json_object(path)
    return validate_bundle_manifest_dict(payload)


def load_impact_output_file(path: Path) -> dict[str, Any]:
    """Load and validate an impact output JSON file."""
    payload = _load_json_object(path)
    return validate_impact_output_dict(payload)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"File is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValidationError(f"File must contain a JSON object: {path}")
    return payload
