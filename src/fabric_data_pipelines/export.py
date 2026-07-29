"""Workspace-level export helpers for Fabric Git integration.

The library focuses on generating the correct on-disk item folder contents:

- `<name>.DataPipeline/pipeline-content.json`
- `<name>.DataPipeline/.platform`
- `<name>.DataPipeline/.schedules` (optional)
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fabric_data_pipelines.pipeline import Pipeline


def read_platform_logical_id(item_dir: str | Path) -> str | None:
    """Read `.platform.config.logicalId` from an item folder.

    Returns `None` if the file is missing or malformed.
    """

    platform_path = Path(item_dir) / ".platform"
    if not platform_path.exists():
        return None

    try:
        platform = json.loads(platform_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    config = platform.get("config")
    if not isinstance(config, dict):
        return None

    logical_id = config.get("logicalId")
    if not isinstance(logical_id, str):
        return None

    return logical_id


def save_workspace(
    pipelines: Iterable[Pipeline],
    directory: str | Path,
    *,
    prune: bool = False,
) -> list[Path]:
    """Export multiple pipelines into a Fabric workspace folder.

    Args:
        pipelines: Pipeline instances to export.
        directory: Target folder containing `*.DataPipeline/` item folders.
        prune: When True, remove any existing `*.DataPipeline/` folders not produced by
            this run.
    """

    from fabric_data_pipelines.pipeline import Pipeline

    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)

    pipelines_list = list(pipelines)
    for p in pipelines_list:
        if not isinstance(p, Pipeline):
            raise TypeError(f"Expected Pipeline objects, got {type(p).__name__}")

    names: set[str] = set()
    produced: list[Path] = []
    for p in pipelines_list:
        if p.name in names:
            raise ValueError(f"Duplicate pipeline name '{p.name}' in save_workspace() input")
        names.add(p.name)
        produced.append(p.save_item(directory_path))

    if prune:
        produced_names = {d.name for d in produced}
        for child in directory_path.iterdir():
            if not child.is_dir():
                continue
            if not child.name.endswith(".DataPipeline"):
                continue
            if child.name in produced_names:
                continue
            shutil.rmtree(child)

    return produced
