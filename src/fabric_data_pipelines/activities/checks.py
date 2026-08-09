"""Shared offline validation helpers for activity model validators."""

from __future__ import annotations

from typing import Any

from fabric_data_pipelines.errors import PipelineValidationError
from fabric_data_pipelines.serialization import Expression


def require_non_empty_str(value: str, *, field: str) -> None:
    """Reject blank strings."""
    if not value.strip():
        raise PipelineValidationError(f"{field} must be a non-empty string")


def require_expression_value(value: Any, *, field: str) -> None:
    """Reject empty expression-like values (str / Expression / dict with value)."""
    if isinstance(value, str):
        require_non_empty_str(value, field=field)
        return
    if isinstance(value, Expression):
        require_non_empty_str(value.value, field=field)
        return
    if isinstance(value, dict):
        inner = value.get("value")
        if not isinstance(inner, str) or not inner.strip():
            raise PipelineValidationError(f"{field} must have a non-empty 'value'")
        return


def get_type_name(obj: Any) -> str | None:
    """Return a ``type`` string from a model or dict, if present and non-empty."""
    if obj is None:
        return None
    raw = obj.get("type") if isinstance(obj, dict) else getattr(obj, "type", None)
    if isinstance(raw, str) and raw.strip():
        return raw
    return None


def get_dataset_settings(connector: Any) -> Any:
    """Return nested dataset settings from a connector model or dict."""
    if isinstance(connector, dict):
        return connector.get("datasetSettings", connector.get("dataset_settings"))
    return getattr(connector, "dataset_settings", None)
