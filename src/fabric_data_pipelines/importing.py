"""Parse Fabric pipeline JSON and Git item folders into typed models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fabric_data_pipelines.activities.base import (
    Activity,
    ActivityDependency,
    ActivityPolicy,
    ExternalReferences,
    SecureInputOutputPolicy,
)
from fabric_data_pipelines.activities.control import (
    Fail,
    ForEach,
    IfCondition,
    Switch,
    SwitchCase,
    Until,
    Wait,
)
from fabric_data_pipelines.activities.copy import (
    Copy,
    CopySink,
    CopySource,
    DataWarehouseSink,
    DataWarehouseSource,
    LakehouseTableSink,
    LakehouseTableSource,
    SqlMISink,
    SqlMISource,
    StagingSettings,
    TabularTranslator,
)
from fabric_data_pipelines.activities.dataflow import Dataflow
from fabric_data_pipelines.activities.datasets import (
    AzureSqlMITable,
    AzureSqlTable,
    Dataset,
    DatasetSettings,
    DataWarehouseTable,
    LakehouseTable,
)
from fabric_data_pipelines.activities.execute_pipeline import ExecutePipeline
from fabric_data_pipelines.activities.lookup import Lookup
from fabric_data_pipelines.activities.notebook import Notebook
from fabric_data_pipelines.activities.raw import RawActivity
from fabric_data_pipelines.activities.script import Script
from fabric_data_pipelines.activities.stored_procedure import StoredProcedure
from fabric_data_pipelines.activities.variables import AppendVariable, SetVariable
from fabric_data_pipelines.activities.web import Web
from fabric_data_pipelines.errors import PipelineImportError
from fabric_data_pipelines.export import read_platform_logical_id
from fabric_data_pipelines.pipeline import LibraryVariable, Parameter, Pipeline, Variable
from fabric_data_pipelines.schedule import Schedule

# Modeled activity types keyed by Fabric ``type`` string.
ACTIVITY_REGISTRY: dict[str, type[Activity]] = {
    Copy.activity_type: Copy,
    Lookup.activity_type: Lookup,
    Notebook.activity_type: Notebook,
    Dataflow.activity_type: Dataflow,
    StoredProcedure.activity_type: StoredProcedure,
    Script.activity_type: Script,
    Web.activity_type: Web,
    ExecutePipeline.activity_type: ExecutePipeline,
    SetVariable.activity_type: SetVariable,
    AppendVariable.activity_type: AppendVariable,
    IfCondition.activity_type: IfCondition,
    ForEach.activity_type: ForEach,
    Switch.activity_type: Switch,
    Until.activity_type: Until,
    Wait.activity_type: Wait,
    Fail.activity_type: Fail,
}

_SOURCE_REGISTRY: dict[str, type[CopySource]] = {
    "SqlMISource": SqlMISource,
    "LakehouseTableSource": LakehouseTableSource,
    "DataWarehouseSource": DataWarehouseSource,
}

_SINK_REGISTRY: dict[str, type[CopySink]] = {
    "SqlMISink": SqlMISink,
    "LakehouseTableSink": LakehouseTableSink,
    "DataWarehouseSink": DataWarehouseSink,
}

_DATASET_REGISTRY: dict[str, type[DatasetSettings]] = {
    "LakehouseTable": LakehouseTable,
    "AzureSqlMITable": AzureSqlMITable,
    "AzureSqlTable": AzureSqlTable,
    "DataWarehouseTable": DataWarehouseTable,
}

_NESTED_ACTIVITY_KEYS = frozenset(
    {
        "ifTrueActivities",
        "ifFalseActivities",
        "activities",
        "defaultActivities",
    }
)


def parse_dataset(raw: dict[str, Any]) -> DatasetSettings:
    """Parse a Fabric ``datasetSettings`` object into a typed dataset model."""
    if not isinstance(raw, dict):
        raise PipelineImportError(f"Expected datasetSettings object, got {type(raw).__name__}")
    dtype = raw.get("type")
    if not isinstance(dtype, str) or not dtype:
        raise PipelineImportError("datasetSettings is missing required 'type'")

    # Typed subclasses use custom ``__init__`` sugar that conflicts with
    # ``model_validate`` when ``type`` is present in the payload. Validate as
    # the base shape, then re-box into the concrete class via ``model_construct``.
    base = DatasetSettings.model_validate(raw)
    cls = _DATASET_REGISTRY.get(dtype, Dataset)
    if cls is DatasetSettings:
        return base
    return cls.model_construct(
        type=base.type,
        type_properties=dict(base.type_properties),
        annotations=list(base.annotations),
        schema_=list(base.schema_),
        external_references=base.external_references,
        linked_service=base.linked_service,
        parameters=base.parameters,
        description=base.description,
    )


def parse_copy_source(raw: dict[str, Any]) -> CopySource:
    """Parse a Copy/Lookup source connector, dispatching known types."""
    if not isinstance(raw, dict):
        raise PipelineImportError(f"Expected source object, got {type(raw).__name__}")
    data = dict(raw)
    ds = data.get("datasetSettings")
    if isinstance(ds, dict):
        data["datasetSettings"] = parse_dataset(ds)
    stype = data.get("type")
    if not isinstance(stype, str) or not stype:
        raise PipelineImportError("Copy source is missing required 'type'")
    cls = _SOURCE_REGISTRY.get(stype, CopySource)
    return cls.model_validate(data)


def parse_copy_sink(raw: dict[str, Any]) -> CopySink:
    """Parse a Copy sink/destination connector, dispatching known types."""
    if not isinstance(raw, dict):
        raise PipelineImportError(f"Expected sink object, got {type(raw).__name__}")
    data = dict(raw)
    ds = data.get("datasetSettings")
    if isinstance(ds, dict):
        data["datasetSettings"] = parse_dataset(ds)
    stype = data.get("type")
    if not isinstance(stype, str) or not stype:
        raise PipelineImportError("Copy sink is missing required 'type'")
    cls = _SINK_REGISTRY.get(stype, CopySink)
    return cls.model_validate(data)


def _parse_envelope(raw: dict[str, Any], *, name: str) -> dict[str, Any]:
    """Build camelCase constructor kwargs for activity envelope fields."""
    envelope: dict[str, Any] = {"name": name}
    if "dependsOn" in raw:
        deps = raw["dependsOn"]
        if deps is None:
            envelope["dependsOn"] = []
        elif not isinstance(deps, list):
            raise PipelineImportError(
                f"Activity '{name}' has invalid dependsOn "
                f"(expected list, got {type(deps).__name__})"
            )
        else:
            envelope["dependsOn"] = [ActivityDependency.model_validate(d) for d in deps]
    if "policy" in raw and raw["policy"] is not None:
        envelope["policy"] = raw["policy"]
    if "externalReferences" in raw and raw["externalReferences"] is not None:
        envelope["externalReferences"] = ExternalReferences.model_validate(
            raw["externalReferences"]
        )
    if "state" in raw and raw["state"] is not None:
        envelope["state"] = raw["state"]
    if "onInactiveMarkAs" in raw and raw["onInactiveMarkAs"] is not None:
        envelope["onInactiveMarkAs"] = raw["onInactiveMarkAs"]
    if "description" in raw and raw["description"] is not None:
        envelope["description"] = raw["description"]
    if "userProperties" in raw and raw["userProperties"] is not None:
        envelope["userProperties"] = raw["userProperties"]
    return envelope


def _parse_nested_activities(items: Any, *, parent: str, field: str) -> list[Activity]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise PipelineImportError(
            f"Activity '{parent}' field '{field}' must be a list, got {type(items).__name__}"
        )
    return [parse_activity(item) for item in items]


def parse_activity(raw: dict[str, Any]) -> Activity:
    """Parse one Fabric activity envelope into a typed model or ``RawActivity``."""
    if not isinstance(raw, dict):
        raise PipelineImportError(f"Expected activity object, got {type(raw).__name__}")

    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise PipelineImportError("Activity is missing required 'name'")

    act_type = raw.get("type")
    if not isinstance(act_type, str) or not act_type:
        raise PipelineImportError(f"Activity '{name}' is missing required 'type'")

    type_properties = raw.get("typeProperties")
    if type_properties is None:
        type_properties = {}
    if not isinstance(type_properties, dict):
        raise PipelineImportError(
            f"Activity '{name}' has invalid typeProperties "
            f"(expected object, got {type(type_properties).__name__})"
        )

    envelope = _parse_envelope(raw, name=name)
    cls = ACTIVITY_REGISTRY.get(act_type)

    if cls is None:
        return RawActivity(
            type=act_type,
            type_properties=dict(type_properties),
            **_raw_activity_kwargs(envelope),
        )

    if cls is Copy:
        return _parse_copy(envelope, type_properties)
    if cls is Lookup:
        return _parse_lookup(envelope, type_properties)
    if cls is IfCondition:
        return _parse_if_condition(envelope, type_properties)
    if cls is ForEach:
        return _parse_for_each(envelope, type_properties)
    if cls is Switch:
        return _parse_switch(envelope, type_properties)
    if cls is Until:
        return _parse_until(envelope, type_properties)

    data = {**envelope, **type_properties}
    return cls.model_validate(data)


def _raw_activity_kwargs(envelope: dict[str, Any]) -> dict[str, Any]:
    """Map camelCase envelope keys to RawActivity constructor kwargs."""
    kwargs: dict[str, Any] = {"name": envelope["name"]}
    if "dependsOn" in envelope:
        kwargs["depends_on"] = envelope["dependsOn"]
    if "policy" in envelope:
        policy = envelope["policy"]
        if isinstance(policy, dict):
            # Prefer full ActivityPolicy when possible; keep dict otherwise.
            try:
                kwargs["policy"] = ActivityPolicy.model_validate(policy)
            except Exception:
                try:
                    kwargs["policy"] = SecureInputOutputPolicy.model_validate(policy)
                except Exception:
                    kwargs["policy"] = policy
        else:
            kwargs["policy"] = policy
    if "externalReferences" in envelope:
        kwargs["external_references"] = envelope["externalReferences"]
    if "state" in envelope:
        kwargs["state"] = envelope["state"]
    if "onInactiveMarkAs" in envelope:
        kwargs["on_inactive_mark_as"] = envelope["onInactiveMarkAs"]
    if "description" in envelope:
        kwargs["description"] = envelope["description"]
    if "userProperties" in envelope:
        kwargs["user_properties"] = envelope["userProperties"]
    return kwargs


def _parse_copy(envelope: dict[str, Any], tp: dict[str, Any]) -> Copy:
    skip = {"source", "sink", "destination"}
    data = {**envelope, **{k: v for k, v in tp.items() if k not in skip}}
    source = tp.get("source")
    if not isinstance(source, dict):
        raise PipelineImportError(f"Copy activity '{envelope['name']}' is missing source object")
    data["source"] = parse_copy_source(source)

    sink = tp.get("sink")
    destination = tp.get("destination")
    if isinstance(sink, dict):
        data["sink"] = parse_copy_sink(sink)
    elif isinstance(destination, dict):
        # Fabric sometimes uses ``destination`` instead of ``sink``.
        data["sink"] = parse_copy_sink(destination)
    if isinstance(destination, dict) and "sink" in data:
        # Prefer sink; drop destination to avoid duplicate fields on re-export.
        pass
    elif isinstance(destination, dict):
        data["destination"] = parse_copy_sink(destination)

    translator = tp.get("translator")
    if isinstance(translator, dict):
        data["translator"] = TabularTranslator.model_validate(translator)

    staging = tp.get("stagingSettings")
    if isinstance(staging, dict):
        data["stagingSettings"] = StagingSettings.model_validate(staging)

    return Copy.model_validate(data)


def _parse_lookup(envelope: dict[str, Any], tp: dict[str, Any]) -> Lookup:
    data = {
        **envelope,
        **{k: v for k, v in tp.items() if k not in {"source", "datasetSettings"}},
    }
    source = tp.get("source")
    if not isinstance(source, dict):
        raise PipelineImportError(f"Lookup activity '{envelope['name']}' is missing source object")
    data["source"] = parse_copy_source(source)

    dataset = tp.get("datasetSettings")
    if not isinstance(dataset, dict):
        raise PipelineImportError(
            f"Lookup activity '{envelope['name']}' is missing datasetSettings object"
        )
    data["datasetSettings"] = parse_dataset(dataset)
    return Lookup.model_validate(data)


def _parse_if_condition(envelope: dict[str, Any], tp: dict[str, Any]) -> IfCondition:
    name = envelope["name"]
    data = {
        **envelope,
        **{k: v for k, v in tp.items() if k not in _NESTED_ACTIVITY_KEYS},
        "ifTrueActivities": _parse_nested_activities(
            tp.get("ifTrueActivities"), parent=name, field="ifTrueActivities"
        ),
        "ifFalseActivities": _parse_nested_activities(
            tp.get("ifFalseActivities"), parent=name, field="ifFalseActivities"
        ),
    }
    return IfCondition.model_validate(data)


def _parse_for_each(envelope: dict[str, Any], tp: dict[str, Any]) -> ForEach:
    name = envelope["name"]
    nested = _parse_nested_activities(tp.get("activities"), parent=name, field="activities")
    data = {
        **envelope,
        **{k: v for k, v in tp.items() if k not in _NESTED_ACTIVITY_KEYS},
        "activities": nested,
    }
    return ForEach.model_validate(data)


def _parse_until(envelope: dict[str, Any], tp: dict[str, Any]) -> Until:
    name = envelope["name"]
    nested = _parse_nested_activities(tp.get("activities"), parent=name, field="activities")
    data = {
        **envelope,
        **{k: v for k, v in tp.items() if k not in _NESTED_ACTIVITY_KEYS},
        "activities": nested,
    }
    return Until.model_validate(data)


def _parse_switch(envelope: dict[str, Any], tp: dict[str, Any]) -> Switch:
    name = envelope["name"]
    cases_raw = tp.get("cases") or []
    if not isinstance(cases_raw, list):
        raise PipelineImportError(
            f"Switch activity '{name}' field 'cases' must be a list, got {type(cases_raw).__name__}"
        )
    cases: list[SwitchCase] = []
    for i, case in enumerate(cases_raw):
        if not isinstance(case, dict):
            raise PipelineImportError(f"Switch activity '{name}' cases[{i}] must be an object")
        value = case.get("value")
        if not isinstance(value, str):
            raise PipelineImportError(
                f"Switch activity '{name}' cases[{i}] is missing string 'value'"
            )
        cases.append(
            SwitchCase(
                value=value,
                activities=_parse_nested_activities(
                    case.get("activities"), parent=name, field=f"cases[{i}].activities"
                ),
            )
        )
    data = {
        **envelope,
        **{k: v for k, v in tp.items() if k not in _NESTED_ACTIVITY_KEYS | {"cases"}},
        "cases": cases,
        "defaultActivities": _parse_nested_activities(
            tp.get("defaultActivities"), parent=name, field="defaultActivities"
        ),
    }
    return Switch.model_validate(data)


def _parse_parameters(
    raw: dict[str, Any] | None,
) -> dict[str, Parameter | dict[str, Any]] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PipelineImportError(
            f"properties.parameters must be an object, got {type(raw).__name__}"
        )
    result: dict[str, Parameter | dict[str, Any]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise PipelineImportError(
                f"properties.parameters[{key!r}] must be an object, got {type(value).__name__}"
            )
        try:
            result[key] = Parameter.model_validate(value)
        except Exception:
            result[key] = value
    return result


def _parse_variables(
    raw: dict[str, Any] | None,
) -> dict[str, Variable | dict[str, Any]] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PipelineImportError(
            f"properties.variables must be an object, got {type(raw).__name__}"
        )
    result: dict[str, Variable | dict[str, Any]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise PipelineImportError(
                f"properties.variables[{key!r}] must be an object, got {type(value).__name__}"
            )
        try:
            result[key] = Variable.model_validate(value)
        except Exception:
            result[key] = value
    return result


def _parse_library_variables(
    raw: dict[str, Any] | None,
) -> dict[str, LibraryVariable | dict[str, Any]] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PipelineImportError(
            f"properties.libraryVariables must be an object, got {type(raw).__name__}"
        )
    result: dict[str, LibraryVariable | dict[str, Any]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise PipelineImportError(
                f"properties.libraryVariables[{key!r}] must be an object, "
                f"got {type(value).__name__}"
            )
        try:
            result[key] = LibraryVariable.model_validate(value)
        except Exception:
            result[key] = value
    return result


def pipeline_from_dict(data: dict[str, Any], *, name: str) -> Pipeline:
    """Build a :class:`~fabric_data_pipelines.Pipeline` from ``pipeline-content`` JSON.

    Args:
        data: Fabric pipeline content (``{"properties": {...}}``).
        name: Pipeline name (not stored in content JSON; usually from the item folder).
    """
    if not isinstance(name, str) or not name:
        raise PipelineImportError("Pipeline name is required")
    if not isinstance(data, dict):
        raise PipelineImportError(f"Expected pipeline JSON object, got {type(data).__name__}")
    props = data.get("properties")
    if not isinstance(props, dict):
        raise PipelineImportError("Pipeline JSON is missing required 'properties' object")

    activities_raw = props.get("activities")
    if activities_raw is None:
        activities_raw = []
    if not isinstance(activities_raw, list):
        raise PipelineImportError(
            f"properties.activities must be a list, got {type(activities_raw).__name__}"
        )

    return Pipeline(
        name=name,
        description=props.get("description"),
        activities=[parse_activity(item) for item in activities_raw],
        parameters=_parse_parameters(props.get("parameters")),
        variables=_parse_variables(props.get("variables")),
        library_variables=_parse_library_variables(props.get("libraryVariables")),
        concurrency=props.get("concurrency"),
    )


def pipeline_from_json(text: str, *, name: str) -> Pipeline:
    """Parse Fabric pipeline JSON text into a :class:`~fabric_data_pipelines.Pipeline`."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PipelineImportError(f"Invalid pipeline JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineImportError(f"Expected pipeline JSON object, got {type(data).__name__}")
    return pipeline_from_dict(data, name=name)


def _resolve_item_dir(path: Path) -> Path:
    """Accept a ``*.DataPipeline`` folder or a lone item under a parent directory."""
    if path.is_dir() and path.name.endswith(".DataPipeline"):
        return path
    if path.is_file() and path.name == "pipeline-content.json":
        return path.parent
    if path.is_dir():
        children = sorted(
            child
            for child in path.iterdir()
            if child.is_dir() and child.name.endswith(".DataPipeline")
        )
        if len(children) == 1:
            return children[0]
        if not children:
            raise PipelineImportError(
                f"No *.DataPipeline folder found under '{path}'. "
                "Pass the item folder path (e.g. out/MyPipeline.DataPipeline)."
            )
        raise PipelineImportError(
            f"Multiple *.DataPipeline folders under '{path}'; "
            "pass a specific item folder or use load_workspace()."
        )
    raise PipelineImportError(f"Not a Fabric pipeline item path: '{path}'")


def _pipeline_name_from_item(item_dir: Path) -> str:
    platform_path = item_dir / ".platform"
    if platform_path.exists():
        try:
            platform = json.loads(platform_path.read_text(encoding="utf-8"))
        except Exception:
            platform = None
        if isinstance(platform, dict):
            metadata = platform.get("metadata")
            if isinstance(metadata, dict):
                display = metadata.get("displayName")
                if isinstance(display, str) and display:
                    return display
    # Folder name: ``Name.DataPipeline``
    if item_dir.name.endswith(".DataPipeline"):
        return item_dir.name[: -len(".DataPipeline")]
    raise PipelineImportError(f"Could not determine pipeline name for item folder '{item_dir}'")


def _parse_schedules_file(path: Path) -> list[Schedule] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineImportError(f"Invalid .schedules JSON in '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineImportError(f".schedules must be a JSON object in '{path}'")
    schedules_raw = data.get("schedules")
    if schedules_raw is None:
        return []
    if not isinstance(schedules_raw, list):
        raise PipelineImportError(f".schedules.schedules must be a list in '{path}'")
    return [Schedule.model_validate(item) for item in schedules_raw]


def load_item(directory: str | Path) -> Pipeline:
    """Load a Fabric ``*.DataPipeline`` item folder into a typed :class:`Pipeline`.

    Reads ``pipeline-content.json``, optional ``.schedules``, and ``logicalId`` from
    ``.platform`` when present.
    """
    item_dir = _resolve_item_dir(Path(directory))
    content_path = item_dir / "pipeline-content.json"
    if not content_path.exists():
        raise PipelineImportError(f"Missing pipeline-content.json in '{item_dir}'")

    name = _pipeline_name_from_item(item_dir)
    text = content_path.read_text(encoding="utf-8")
    pipeline = pipeline_from_json(text, name=name)

    logical_id = read_platform_logical_id(item_dir)
    if logical_id is not None:
        pipeline.logical_id = logical_id

    schedules = _parse_schedules_file(item_dir / ".schedules")
    if schedules is not None:
        pipeline.schedules = schedules

    return pipeline


def load_workspace(directory: str | Path) -> list[Pipeline]:
    """Load all ``*.DataPipeline`` item folders under a workspace directory."""
    directory_path = Path(directory)
    if not directory_path.is_dir():
        raise PipelineImportError(f"Workspace directory does not exist: '{directory_path}'")

    items = sorted(
        child
        for child in directory_path.iterdir()
        if child.is_dir() and child.name.endswith(".DataPipeline")
    )
    if not items:
        raise PipelineImportError(f"No *.DataPipeline folders found under '{directory_path}'")
    return [load_item(item) for item in items]
