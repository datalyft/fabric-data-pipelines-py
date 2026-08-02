"""Pipeline container, parameters/variables, and definition helpers."""

from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator

from fabric_data_pipelines.activities.base import Activity
from fabric_data_pipelines.activities.control import ForEach, IfCondition, Switch, Until
from fabric_data_pipelines.errors import (
    CrossScopeDependencyError,
    CyclicDependencyError,
    DuplicateActivityNameError,
    ScheduleValidationError,
    UnknownDependencyError,
)
from fabric_data_pipelines.schedule import Schedule
from fabric_data_pipelines.serialization import FabricModel, dump_json

# Fabric allows at most 20 job schedules per pipeline item.
_MAX_SCHEDULES_PER_PIPELINE = 20


class Parameter(FabricModel):
    """A pipeline parameter definition.

    Example::

        Parameter(type="Int", default_value=0)
        Parameter(type="String", default_value="full")
    """

    type: str
    default_value: Any | None = None


class Variable(FabricModel):
    """A pipeline variable definition.

    Example::

        Variable(type="String")
        Variable(type="Array", default_value=[])
    """

    type: str
    default_value: Any | None = None


class LibraryVariable(FabricModel):
    """A reference to a Fabric Variable Library value.

    Example::

        LibraryVariable(
            type="String",
            variable_name="SourceDb",
            library_name="Demo_ETL_Library",
        )
    """

    type: str
    variable_name: str
    library_name: str


class Pipeline(FabricModel):
    """A Fabric data pipeline.

    Activities are declared declaratively; call :meth:`then` / :meth:`after` on
    them to express dependencies, then pass the list to ``Pipeline``.

    Schedules must be attached on the pipeline itself via ``schedules=[...]``
    (up to 20). Fabric stores them in a sibling ``.schedules`` file written by
    :meth:`save_item`.

    Example::

        from fabric_data_pipelines import Pipeline, Wait, Notebook, Schedule, Weekly

        wait = Wait(name="pause", wait_time_in_seconds=5)
        nb = Notebook(name="run", notebook_id="...", workspace_id="...")
        wait.then(nb)

        schedule = Schedule(
            configuration=Weekly(times=["21:30"], weekdays=["Monday"]),
        )
        pipeline = Pipeline(
            name="daily_load",
            activities=[wait, nb],
            schedules=[schedule],
        )
        pipeline.save_item("out")
    """

    name: str
    description: str | None = None
    activities: list[Activity] = Field(default_factory=list)
    parameters: dict[str, Parameter | dict[str, Any]] | None = None
    variables: dict[str, Variable | dict[str, Any]] | None = None
    library_variables: dict[str, LibraryVariable | dict[str, Any]] | None = None
    concurrency: int | None = None
    logical_id: str | None = None
    schedules: list[Schedule] | None = Field(
        default=None,
        description=(
            "Job schedules physically attached to this pipeline "
            f"(Fabric limit: {_MAX_SCHEDULES_PER_PIPELINE})."
        ),
    )

    # Fixed UUIDv5 namespace so `logicalId` can be derived deterministically from `name`.
    _LOGICAL_ID_NAMESPACE = uuid.UUID("0b7d8e2b-0c1c-4ad1-91c9-4c6d4d7f2f7d")

    @field_validator("schedules")
    @classmethod
    def _validate_schedule_count(cls, value: list[Schedule] | None) -> list[Schedule] | None:
        if value is not None and len(value) > _MAX_SCHEDULES_PER_PIPELINE:
            raise ScheduleValidationError(
                f"A pipeline can have at most {_MAX_SCHEDULES_PER_PIPELINE} schedules "
                f"(Fabric limit); got {len(value)}."
            )
        return value

    def resolve_logical_id(self, item_dir: str | Path | None = None) -> str:
        """Resolve a stable Fabric `logicalId`.

        Priority:
        1. explicit `Pipeline.logical_id`
        2. existing `.platform` on disk (if `item_dir` points at the item folder)
        3. deterministic UUIDv5 derived from pipeline name
        """

        if self.logical_id is not None:
            return self.logical_id

        if item_dir is not None:
            from fabric_data_pipelines.export import read_platform_logical_id

            existing = read_platform_logical_id(item_dir)
            if existing is not None:
                return existing

        return str(uuid.uuid5(self._LOGICAL_ID_NAMESPACE, self.name))

    def platform_dict(self, logical_id: str) -> dict[str, Any]:
        """Serialize `.platform` file payload."""

        platform: dict[str, Any] = {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/"
                "gitIntegration/platformProperties/2.0.0/schema.json"
            ),
            "metadata": {
                "type": "DataPipeline",
                "displayName": self.name,
            },
            "config": {
                "version": "2.0",
                "logicalId": logical_id,
            },
        }
        if self.description is not None:
            platform["metadata"]["description"] = self.description
        return platform

    def schedules_dict(self) -> dict[str, Any] | None:
        """Serialize `.schedules` payload (or `None` if no schedules are set)."""

        if self.schedules is None:
            return None
        return {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/"
                "gitIntegration/schedules/1.0.0/schema.json"
            ),
            "schedules": [_dump_model(s) for s in self.schedules],
        }

    def validate_graph(self) -> None:
        """Validate activity names and the dependency graph.

        Raises:
            DuplicateActivityNameError: Two activities share a name.
            UnknownDependencyError: A ``dependsOn`` target does not exist.
            CrossScopeDependencyError: A ``dependsOn`` target is in another scope.
            CyclicDependencyError: Dependencies form a cycle within a scope.
        """
        scopes = _collect_scopes(self.activities)
        all_names: dict[str, str] = {}  # name -> scope path where first seen

        for scope_path, acts in scopes:
            for act in acts:
                if act.name in all_names:
                    raise DuplicateActivityNameError(
                        f"Duplicate activity name '{act.name}'. Activity names must be "
                        f"unique across the entire pipeline (including nested scopes). "
                        f"First seen in scope '{all_names[act.name]}', again in '{scope_path}'."
                    )
                all_names[act.name] = scope_path

        name_to_scope = {
            name: path for path, acts in scopes for name, path in ((a.name, path) for a in acts)
        }

        for scope_path, acts in scopes:
            scope_names = {a.name for a in acts}
            for act in acts:
                for dep in act.depends_on:
                    target = dep.activity
                    if target not in name_to_scope:
                        raise UnknownDependencyError(
                            f"Activity '{act.name}' depends on unknown activity '{target}'."
                        )
                    if target not in scope_names:
                        raise CrossScopeDependencyError(
                            f"Activity '{act.name}' depends on '{target}' which exists in a "
                            f"different scope ('{name_to_scope[target]}' vs '{scope_path}'). "
                            f"Dependencies must target activities in the same scope."
                        )
            _detect_cycles(acts, scope_path)

    def to_dict(self) -> dict[str, Any]:
        """Build the Fabric ``pipeline-content.json`` structure.

        Returns:
            ``{"properties": {"activities": [...], ...}}``
        """
        self.validate_graph()
        properties: dict[str, Any] = {
            "activities": [act.to_dict() for act in self.activities],
        }
        if self.description is not None:
            properties["description"] = self.description
        if self.parameters is not None:
            properties["parameters"] = {
                key: _dump_model(value) for key, value in self.parameters.items()
            }
        if self.variables is not None:
            properties["variables"] = {
                key: _dump_model(value) for key, value in self.variables.items()
            }
        if self.library_variables is not None:
            properties["libraryVariables"] = {
                key: _dump_model(value) for key, value in self.library_variables.items()
            }
        if self.concurrency is not None:
            properties["concurrency"] = self.concurrency
        return {"properties": properties}

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize to Fabric pipeline JSON text."""
        return dump_json(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, name: str) -> Pipeline:
        """Parse Fabric ``pipeline-content`` JSON into a typed pipeline.

        The pipeline ``name`` is required because Fabric content JSON does not
        include it (it lives on the item folder / ``.platform`` display name).

        Unknown activity types become :class:`~fabric_data_pipelines.RawActivity`.
        """
        from fabric_data_pipelines.importing import pipeline_from_dict

        return pipeline_from_dict(data, name=name)

    @classmethod
    def from_json(cls, text: str, *, name: str) -> Pipeline:
        """Parse Fabric pipeline JSON text into a typed pipeline.

        See :meth:`from_dict` for naming and typing rules.
        """
        from fabric_data_pipelines.importing import pipeline_from_json

        return pipeline_from_json(text, name=name)

    @classmethod
    def load_item(cls, directory: str | Path) -> Pipeline:
        """Load a Fabric ``*.DataPipeline`` Git item folder.

        Reads ``pipeline-content.json``, optional ``.schedules``, and
        ``logicalId`` from ``.platform`` when present.
        """
        from fabric_data_pipelines.importing import load_item

        return load_item(directory)

    def save(self, path: str | Path) -> None:
        """Write ``pipeline-content.json`` (or any path) to disk.

        Example::

            pipeline.save("daily_load.json")
        """
        Path(path).write_text(self.to_json() + "\n", encoding="utf-8")

    def save_item(self, directory: str | Path, *, prune: bool = True) -> Path:
        """Write a Fabric item folder with pipeline-content, platform, and schedules.

        Creates ``<directory>/<name>.DataPipeline/`` containing all item files.

        Example::

            pipeline.save_item("out")
            # -> out/daily_load.DataPipeline/pipeline-content.json
            # -> out/daily_load.DataPipeline/.platform
        """
        item_dir = Path(directory) / f"{self.name}.DataPipeline"
        item_dir.mkdir(parents=True, exist_ok=True)

        # Read existing `.platform` before overwriting so logicalId stays stable.
        logical_id = self.resolve_logical_id(item_dir)

        (item_dir / "pipeline-content.json").write_text(self.to_json() + "\n", encoding="utf-8")
        (item_dir / ".platform").write_text(
            json.dumps(self.platform_dict(logical_id), indent=2) + "\n", encoding="utf-8"
        )

        schedules_dict = self.schedules_dict()
        if schedules_dict is not None:
            (item_dir / ".schedules").write_text(
                dump_json(schedules_dict, indent=2) + "\n", encoding="utf-8"
            )
        elif prune:
            (item_dir / ".schedules").unlink(missing_ok=True)

        return item_dir

    def to_definition(self, *, item_dir: str | Path | None = None) -> dict[str, Any]:
        """Build the REST API item definition payload with base64 parts.

        Returns a dict suitable for the Fabric Items API ``definition`` field::

            {
              "parts": [
                {"path": "pipeline-content.json", "payload": "...", "payloadType": "InlineBase64"},
                {"path": ".platform", "payload": "...", "payloadType": "InlineBase64"},
                # NOTE: `.schedules` is not part of the Items API definition payload.
              ]
            }
        """
        content = self.to_json(indent=2) + "\n"
        logical_id = self.resolve_logical_id(item_dir)
        platform_text = json.dumps(self.platform_dict(logical_id), indent=2) + "\n"
        return {
            "parts": [
                {
                    "path": "pipeline-content.json",
                    "payload": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                    "payloadType": "InlineBase64",
                },
                {
                    "path": ".platform",
                    "payload": base64.b64encode(platform_text.encode("utf-8")).decode("ascii"),
                    "payloadType": "InlineBase64",
                },
            ]
        }


def _dump_model(value: FabricModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, FabricModel):
        return value.model_dump(by_alias=True, exclude_none=True, mode="json")
    return value


def _collect_scopes(
    activities: list[Activity], path: str = "root"
) -> list[tuple[str, list[Activity]]]:
    """Return (scope_path, activities) for every activity list in the tree."""
    result: list[tuple[str, list[Activity]]] = [(path, activities)]
    for act in activities:
        if isinstance(act, IfCondition):
            result.extend(_collect_scopes(act.if_true_activities, f"{path}/{act.name}/ifTrue"))
            result.extend(_collect_scopes(act.if_false_activities, f"{path}/{act.name}/ifFalse"))
        elif isinstance(act, (ForEach, Until)):
            result.extend(_collect_scopes(act.activities, f"{path}/{act.name}/activities"))
        elif isinstance(act, Switch):
            for i, case in enumerate(act.cases):
                result.extend(
                    _collect_scopes(case.activities, f"{path}/{act.name}/case[{i}:{case.value}]")
                )
            result.extend(_collect_scopes(act.default_activities, f"{path}/{act.name}/default"))
    return result


def _detect_cycles(activities: list[Activity], scope_path: str) -> None:
    graph: dict[str, list[str]] = {a.name: [d.activity for d in a.depends_on] for a in activities}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in graph}
    stack: list[str] = []

    def visit(node: str) -> None:
        color[node] = GRAY
        stack.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                cycle_start = stack.index(neighbor)
                cycle = [*stack[cycle_start:], neighbor]
                raise CyclicDependencyError(
                    f"Cyclic dependency detected in scope '{scope_path}': "
                    + " -> ".join(cycle)
                    + "."
                )
            if color[neighbor] == WHITE:
                visit(neighbor)
        stack.pop()
        color[node] = BLACK

    for name in graph:
        if color[name] == WHITE:
            visit(name)
