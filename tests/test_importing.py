"""Tests for pipeline import (from_json / load_item / parse_activity)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fabric_data_pipelines import (
    Copy,
    Dataflow,
    Fail,
    ForEach,
    LakehouseTable,
    LakehouseTableSink,
    Lookup,
    Notebook,
    Pipeline,
    PipelineImportError,
    RawActivity,
    Schedule,
    Script,
    SqlMISink,
    SqlMISource,
    Switch,
    Wait,
    Weekly,
    load_item,
    load_workspace,
    parse_activity,
    save_workspace,
)
from tests.helpers import SNAPSHOTS, assert_json_equal, load_snapshot

PIPELINE_SNAPSHOTS = [
    ("empty_pipeline.json", "empty"),
    ("web_get.json", "Web_Get_Example"),
    ("sql_script_refresh.json", "sql_script_refresh"),
    ("docs_multi_activity.json", "docs_example"),
    ("control_flow_kitchen_sink.json", "kitchen_sink"),
    ("landing_copy_subset.json", "landing_truncate_copy"),
    ("sales_etl_history_full_load.json", "sales_etl_history_full_load"),
]


@pytest.mark.parametrize(("filename", "name"), PIPELINE_SNAPSHOTS)
def test_from_dict_round_trip(filename: str, name: str) -> None:
    snap = load_snapshot(filename)
    pipeline = Pipeline.from_dict(snap, name=name)
    assert_json_equal(pipeline.to_dict(), snap)


@pytest.mark.parametrize(("filename", "name"), PIPELINE_SNAPSHOTS)
def test_from_json_round_trip(filename: str, name: str) -> None:
    text = (SNAPSHOTS / filename).read_text(encoding="utf-8")
    pipeline = Pipeline.from_json(text, name=name)
    assert_json_equal(pipeline.to_dict(), json.loads(text))


def test_docs_multi_activity_types() -> None:
    pipeline = Pipeline.from_dict(load_snapshot("docs_multi_activity.json"), name="docs_example")
    assert isinstance(pipeline.activities[0], Notebook)
    assert isinstance(pipeline.activities[1], RawActivity)
    assert pipeline.activities[1].type == "GetMetadata"
    assert isinstance(pipeline.activities[2], Lookup)
    assert isinstance(pipeline.activities[2].dataset_settings, LakehouseTable)
    assert isinstance(pipeline.activities[3], RawActivity)
    assert pipeline.activities[3].type == "PBISemanticModelRefresh"


def test_control_flow_types() -> None:
    pipeline = Pipeline.from_dict(
        load_snapshot("control_flow_kitchen_sink.json"), name="kitchen_sink"
    )
    assert isinstance(pipeline.activities[0], ForEach)
    assert isinstance(pipeline.activities[0].activities[0], Dataflow)
    assert isinstance(pipeline.activities[1], Switch)
    assert isinstance(pipeline.activities[1].default_activities[0], Fail)


def test_landing_copy_types() -> None:
    pipeline = Pipeline.from_dict(
        load_snapshot("landing_copy_subset.json"), name="landing_truncate_copy"
    )
    assert isinstance(pipeline.activities[0], Script)
    copy = pipeline.activities[1]
    assert isinstance(copy, Copy)
    assert isinstance(copy.source, SqlMISource)
    assert isinstance(copy.sink, SqlMISink)


def test_unknown_activity_becomes_raw() -> None:
    raw = {
        "name": "Custom1",
        "type": "SomeFutureActivity",
        "dependsOn": [],
        "typeProperties": {"foo": 1, "bar": {"nested": True}},
    }
    activity = parse_activity(raw)
    assert isinstance(activity, RawActivity)
    assert activity.type == "SomeFutureActivity"
    assert activity.type_properties == {"foo": 1, "bar": {"nested": True}}
    assert_json_equal(activity.to_dict()["typeProperties"], raw["typeProperties"])


def test_copy_destination_normalized_to_sink() -> None:
    raw = {
        "name": "Copy1",
        "type": "Copy",
        "dependsOn": [],
        "typeProperties": {
            "source": {"type": "LakehouseTableSource"},
            "destination": {
                "type": "LakehouseTableSink",
                "datasetSettings": {
                    "type": "LakehouseTable",
                    "annotations": [],
                    "schema": [],
                    "typeProperties": {"table": "t1"},
                },
            },
        },
        "policy": {
            "timeout": "0.12:00:00",
            "retry": 0,
            "retryIntervalInSeconds": 30,
            "secureOutput": False,
            "secureInput": False,
        },
    }
    activity = parse_activity(raw)
    assert isinstance(activity, Copy)
    assert activity.sink is not None
    assert isinstance(activity.sink, LakehouseTableSink)
    exported = activity.to_dict()
    assert "sink" in exported["typeProperties"]
    assert exported["typeProperties"]["sink"]["type"] == "LakehouseTableSink"


def test_from_dict_requires_properties() -> None:
    with pytest.raises(PipelineImportError, match="properties"):
        Pipeline.from_dict({"activities": []}, name="x")


def test_from_dict_requires_name() -> None:
    with pytest.raises(PipelineImportError, match="name"):
        Pipeline.from_dict({"properties": {"activities": []}}, name="")


def test_parse_activity_requires_name_and_type() -> None:
    with pytest.raises(PipelineImportError, match="name"):
        parse_activity({"type": "Wait", "typeProperties": {"waitTimeInSeconds": 1}})
    with pytest.raises(PipelineImportError, match="type"):
        parse_activity({"name": "w", "typeProperties": {"waitTimeInSeconds": 1}})


def test_load_item_round_trip(tmp_path: Path) -> None:
    schedule = Schedule(
        enabled=True,
        configuration=Weekly(
            start_date_time="2026-07-10T00:00:00",
            end_date_time="2027-07-10T00:00:00",
            local_time_zone_id="Romance Standard Time",
            times=["21:30"],
            weekdays=["Monday"],
        ),
    )
    original = Pipeline(
        name="daily_load",
        activities=[Wait(name="pause", wait_time_in_seconds=5)],
        logical_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        schedules=[schedule],
    )
    item_dir = original.save_item(tmp_path)

    loaded = Pipeline.load_item(item_dir)
    assert loaded.name == "daily_load"
    assert loaded.logical_id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert loaded.schedules is not None
    assert len(loaded.schedules) == 1
    assert isinstance(loaded.activities[0], Wait)
    assert loaded.activities[0].wait_time_in_seconds == 5
    assert_json_equal(loaded.to_dict(), original.to_dict())
    assert_json_equal(loaded.schedules_dict(), original.schedules_dict())


def test_load_item_from_workspace_parent_with_single_item(tmp_path: Path) -> None:
    pipeline = Pipeline(name="only_one", activities=[Wait(name="w", wait_time_in_seconds=1)])
    pipeline.save_item(tmp_path)
    loaded = load_item(tmp_path)
    assert loaded.name == "only_one"


def test_load_item_missing_content(tmp_path: Path) -> None:
    item = tmp_path / "Broken.DataPipeline"
    item.mkdir()
    with pytest.raises(PipelineImportError, match=r"pipeline-content\.json"):
        load_item(item)


def test_load_workspace(tmp_path: Path) -> None:
    a = Pipeline(name="pipe_a", activities=[Wait(name="w", wait_time_in_seconds=1)])
    b = Pipeline(name="pipe_b", activities=[Wait(name="w2", wait_time_in_seconds=2)])
    save_workspace([a, b], tmp_path)
    loaded = load_workspace(tmp_path)
    assert [p.name for p in loaded] == ["pipe_a", "pipe_b"]


def test_load_workspace_empty(tmp_path: Path) -> None:
    with pytest.raises(PipelineImportError, match="No \\*\\.DataPipeline"):
        load_workspace(tmp_path)


def test_load_item_multiple_children_requires_explicit_path(tmp_path: Path) -> None:
    save_workspace(
        [
            Pipeline(name="a", activities=[Wait(name="w", wait_time_in_seconds=1)]),
            Pipeline(name="b", activities=[Wait(name="w2", wait_time_in_seconds=1)]),
        ],
        tmp_path,
    )
    with pytest.raises(PipelineImportError, match="Multiple"):
        load_item(tmp_path)
