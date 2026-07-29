"""Shared helpers for structural snapshot comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fabric_data_pipelines import Pipeline

SNAPSHOTS = Path(__file__).parent / "snapshots"


def load_snapshot(name: str) -> dict[str, Any]:
    """Load a snapshot JSON file from ``tests/snapshots/``."""
    path = SNAPSHOTS / name
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def assert_json_equal(actual: Any, expected: Any, path: str = "$") -> None:
    """Recursively compare JSON-compatible values with a readable path.

    Key order is ignored; list order is significant.
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            pytest.fail(
                f"Type mismatch at {path}: "
                f"{type(actual).__name__} != dict\n"
                f"  actual={actual!r}\n  expected={expected!r}"
            )
        actual_keys = set(actual)
        expected_keys = set(expected)
        if actual_keys != expected_keys:
            missing = expected_keys - actual_keys
            extra = actual_keys - expected_keys
            parts = []
            if missing:
                parts.append(f"missing keys: {sorted(missing)}")
            if extra:
                parts.append(f"extra keys: {sorted(extra)}")
            pytest.fail(f"Key mismatch at {path}: {'; '.join(parts)}")
        for key in expected:
            assert_json_equal(actual[key], expected[key], f"{path}.{key}")
        return

    if isinstance(expected, list):
        if not isinstance(actual, list):
            pytest.fail(
                f"Type mismatch at {path}: "
                f"{type(actual).__name__} != list\n"
                f"  actual={actual!r}\n  expected={expected!r}"
            )
        if len(actual) != len(expected):
            pytest.fail(f"List length mismatch at {path}: {len(actual)} != {len(expected)}")
        for i, (a_item, e_item) in enumerate(zip(actual, expected, strict=True)):
            assert_json_equal(a_item, e_item, f"{path}[{i}]")
        return

    if actual != expected:
        pytest.fail(f"Value mismatch at {path}:\n  actual={actual!r}\n  expected={expected!r}")


def assert_matches_snapshot(pipeline: Pipeline, filename: str) -> None:
    """Assert ``pipeline.to_dict()`` structurally equals a snapshot file."""
    actual = pipeline.to_dict()
    expected = load_snapshot(filename)
    assert_json_equal(actual, expected)


def assert_dict_matches_snapshot(actual: Any, filename: str) -> None:
    """Assert a JSON-compatible dict/list structurally equals a snapshot file."""

    expected = load_snapshot(filename)
    assert_json_equal(actual, expected)
