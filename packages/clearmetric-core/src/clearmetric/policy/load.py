"""Policy rules loading."""

from __future__ import annotations

from pathlib import Path

import yaml
from clearmetric.core.errors import PolicyError
from pydantic import ValidationError

from .models import PolicyRulesFile


def load_rules(path: Path) -> PolicyRulesFile:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PolicyError(f"Policy rules file is not valid YAML: {path}") from exc
    if raw is None:
        raw = {"rules": []}
    if not isinstance(raw, dict):
        raise PolicyError(f"Policy rules file must be a mapping: {path}")
    try:
        return PolicyRulesFile.model_validate(raw)
    except ValidationError as exc:
        raise PolicyError(
            f"Policy rules file failed validation: {path}: {exc}"
        ) from exc
