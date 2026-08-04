"""Tests for codegen CLI."""

from __future__ import annotations

import json
from pathlib import Path

from fabric_data_pipelines import Pipeline, Wait, load_item
from fabric_data_pipelines.cli import main
from fabric_data_pipelines.codegen import codegen_pipeline
from tests.helpers import assert_json_equal, load_snapshot


def test_codegen_pipeline_exec_round_trip(tmp_path: Path) -> None:
    snap = load_snapshot("control_flow_kitchen_sink.json")
    pipeline = Pipeline.from_dict(snap, name="kitchen_sink")
    source = codegen_pipeline(pipeline)

    module_path = tmp_path / "generated_pipeline.py"
    module_path.write_text(source, encoding="utf-8")

    namespace: dict[str, object] = {}
    exec(compile(source, str(module_path), "exec"), namespace)
    generated = namespace["pipeline"]
    assert isinstance(generated, Pipeline)
    assert_json_equal(generated.to_dict(), snap)


def test_codegen_cli_from_item(tmp_path: Path) -> None:
    original = Pipeline(name="cli_demo", activities=[Wait(name="pause", wait_time_in_seconds=3)])
    item_dir = original.save_item(tmp_path)
    out = tmp_path / "out.py"
    assert main(["codegen", str(item_dir), "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "Wait(" in text
    assert "pipeline = Pipeline(" in text

    namespace: dict[str, object] = {}
    exec(compile(text, str(out), "exec"), namespace)
    generated = namespace["pipeline"]
    assert isinstance(generated, Pipeline)
    assert_json_equal(generated.to_dict(), original.to_dict())


def test_codegen_cli_from_json(tmp_path: Path) -> None:
    snap = load_snapshot("web_get.json")
    json_path = tmp_path / "web.json"
    json_path.write_text(json.dumps(snap), encoding="utf-8")
    out = tmp_path / "web.py"
    assert main(["codegen", str(json_path), "--name", "Web_Get", "-o", str(out)]) == 0

    namespace: dict[str, object] = {}
    exec(compile(out.read_text(encoding="utf-8"), str(out), "exec"), namespace)
    generated = namespace["pipeline"]
    assert isinstance(generated, Pipeline)
    assert_json_equal(generated.to_dict(), snap)


def test_codegen_preserves_raw_activity(tmp_path: Path) -> None:
    snap = load_snapshot("docs_multi_activity.json")
    pipeline = Pipeline.from_dict(snap, name="docs_example")
    source = codegen_pipeline(pipeline)
    assert "RawActivity(" in source
    assert "GetMetadata" in source

    namespace: dict[str, object] = {}
    exec(compile(source, "<codegen>", "exec"), namespace)
    generated = namespace["pipeline"]
    assert isinstance(generated, Pipeline)
    assert_json_equal(generated.to_dict(), snap)


def test_codegen_preserves_copy_source_extras() -> None:
    from fabric_data_pipelines import CopySource, Dataset, Lookup, parse_activity

    activity = parse_activity(
        {
            "name": "Get notebook output",
            "type": "Lookup",
            "dependsOn": [],
            "typeProperties": {
                "source": {
                    "type": "JsonSource",
                    "storeSettings": {"type": "LakehouseReadSettings", "recursive": True},
                    "formatSettings": {"type": "JsonReadSettings"},
                },
                "datasetSettings": {
                    "type": "Json",
                    "annotations": [],
                    "schema": {},
                    "typeProperties": {"location": {"type": "LakehouseLocation"}},
                    "connectionSettings": {
                        "name": "lh",
                        "properties": {
                            "type": "Lakehouse",
                            "annotations": [],
                            "typeProperties": {"rootFolder": "Files"},
                        },
                    },
                },
            },
        }
    )
    assert isinstance(activity, Lookup)
    pipeline = Pipeline(name="extras", activities=[activity])
    source = codegen_pipeline(pipeline)
    assert "storeSettings=" in source
    assert "formatSettings=" in source
    assert "connection_settings=" in source

    namespace: dict[str, object] = {}
    exec(compile(source, "<codegen>", "exec"), namespace)
    generated = namespace["pipeline"]
    assert isinstance(generated, Pipeline)
    lookup = generated.activities[0]
    assert isinstance(lookup, Lookup)
    assert isinstance(lookup.source, CopySource)
    assert isinstance(lookup.dataset_settings, Dataset)
    assert_json_equal(generated.to_dict(), pipeline.to_dict())


def test_codegen_schedules_use_public_aliases() -> None:
    from fabric_data_pipelines import Schedule, Weekly

    pipeline = Pipeline(
        name="scheduled",
        activities=[Wait(name="w", wait_time_in_seconds=1)],
        schedules=[
            Schedule(
                configuration=Weekly(times=["21:30"], weekdays=["Monday"]),
            )
        ],
    )
    source = codegen_pipeline(pipeline)
    assert "Weekly(" in source
    assert "WeeklyScheduleConfiguration" not in source
    namespace: dict[str, object] = {}
    exec(compile(source, "<codegen>", "exec"), namespace)
    generated = namespace["pipeline"]
    assert isinstance(generated, Pipeline)
    assert generated.schedules is not None
    assert_json_equal(generated.schedules_dict(), pipeline.schedules_dict())


def test_codegen_cli_load_item_then_save(tmp_path: Path) -> None:
    """End-to-end: save_item → codegen CLI → exec → to_json matches."""
    original = Pipeline.from_dict(load_snapshot("landing_copy_subset.json"), name="landing")
    item_dir = original.save_item(tmp_path)
    out = tmp_path / "landing.py"
    assert main(["codegen", str(item_dir), "-o", str(out)]) == 0
    loaded = load_item(item_dir)
    namespace: dict[str, object] = {}
    exec(compile(out.read_text(encoding="utf-8"), str(out), "exec"), namespace)
    generated = namespace["pipeline"]
    assert isinstance(generated, Pipeline)
    assert_json_equal(generated.to_dict(), loaded.to_dict())
