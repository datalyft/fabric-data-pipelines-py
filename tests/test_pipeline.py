"""Unit tests for pipeline envelope and persistence."""

import base64
import json
from pathlib import Path

from fabric_data_pipelines import (
    LibraryVariable,
    Parameter,
    Pipeline,
    Schedule,
    Variable,
    Wait,
    Weekly,
)


def test_empty_pipeline() -> None:
    pipeline = Pipeline(name="empty")
    assert pipeline.to_dict() == {"properties": {"activities": []}}


def test_description_parameters_variables() -> None:
    pipeline = Pipeline(
        name="demo",
        description="A demo pipeline",
        activities=[Wait(name="pause", wait_time_in_seconds=5)],
        parameters={"run_date": Parameter(type="String", default_value="2024-01-01")},
        variables={"row_count": Variable(type="String")},
        library_variables={
            "Conn": LibraryVariable(
                type="String",
                variable_name="Conn",
                library_name="Lib",
            )
        },
        concurrency=1,
    )
    props = pipeline.to_dict()["properties"]
    assert props["description"] == "A demo pipeline"
    assert props["parameters"]["run_date"]["type"] == "String"
    assert props["parameters"]["run_date"]["defaultValue"] == "2024-01-01"
    assert props["variables"]["row_count"]["type"] == "String"
    assert props["libraryVariables"]["Conn"]["libraryName"] == "Lib"
    assert props["concurrency"] == 1


def test_save(tmp_path: Path) -> None:
    pipeline = Pipeline(name="saved", activities=[Wait(name="w", wait_time_in_seconds=1)])
    path = tmp_path / "saved.json"
    pipeline.save(path)
    data = json.loads(path.read_text())
    assert data["properties"]["activities"][0]["name"] == "w"


def test_save_item(tmp_path: Path) -> None:
    pipeline = Pipeline(
        name="item",
        activities=[Wait(name="w", wait_time_in_seconds=1)],
        logical_id="00000000-0000-0000-0000-000000000001",
    )
    item_dir = pipeline.save_item(tmp_path)
    assert (item_dir / "pipeline-content.json").exists()
    platform = json.loads((item_dir / ".platform").read_text())
    assert platform["metadata"]["displayName"] == "item"
    assert platform["config"]["logicalId"] == "00000000-0000-0000-0000-000000000001"
    assert not (item_dir / ".schedules").exists()


def test_save_item_logical_id_preserved_on_rewrite(tmp_path: Path) -> None:
    pipeline_1 = Pipeline(name="stable_item", activities=[Wait(name="w", wait_time_in_seconds=1)])
    item_dir = pipeline_1.save_item(tmp_path)
    platform_1 = json.loads((item_dir / ".platform").read_text())["config"]
    logical_id_1 = platform_1["logicalId"]

    pipeline_2 = Pipeline(name="stable_item", activities=[Wait(name="w2", wait_time_in_seconds=1)])
    pipeline_2.save_item(tmp_path)
    platform_2 = json.loads((item_dir / ".platform").read_text())["config"]
    assert platform_2["logicalId"] == logical_id_1


def test_save_item_logical_id_is_deterministic_from_name(tmp_path: Path) -> None:
    pipeline = Pipeline(name="deterministic", activities=[Wait(name="w", wait_time_in_seconds=1)])

    item_dir_1 = pipeline.save_item(tmp_path / "workspace_1")
    logical_id_1 = json.loads((item_dir_1 / ".platform").read_text())["config"]["logicalId"]

    item_dir_2 = pipeline.save_item(tmp_path / "workspace_2")
    logical_id_2 = json.loads((item_dir_2 / ".platform").read_text())["config"]["logicalId"]

    assert logical_id_1 == logical_id_2


def test_save_item_prunes_stale_schedules(tmp_path: Path) -> None:
    schedule = Schedule(
        enabled=True,
        job_type="Execute",
        configuration=Weekly(
            type="Weekly",
            start_date_time="2026-07-10T00:00:00",
            end_date_time="2027-07-10T00:00:00",
            local_time_zone_id="Romance Standard Time",
            times=["21:30"],
            weekdays=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        ),
    )
    pipeline_with_schedules = Pipeline(
        name="prune_schedules",
        activities=[Wait(name="w", wait_time_in_seconds=1)],
        schedules=[schedule],
    )
    item_dir = pipeline_with_schedules.save_item(tmp_path)
    assert (item_dir / ".schedules").exists()

    pipeline_without_schedules = Pipeline(
        name="prune_schedules",
        activities=[Wait(name="w2", wait_time_in_seconds=1)],
    )
    pipeline_without_schedules.save_item(tmp_path)
    assert not (item_dir / ".schedules").exists()


def test_save_item_writes_schedules(tmp_path: Path) -> None:
    schedule = Schedule(
        enabled=True,
        job_type="Execute",
        configuration=Weekly(
            type="Weekly",
            start_date_time="2026-07-10T00:00:00",
            end_date_time="2027-07-10T00:00:00",
            local_time_zone_id="Romance Standard Time",
            times=["21:30"],
            weekdays=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        ),
    )
    pipeline = Pipeline(
        name="writes_schedules",
        activities=[Wait(name="w", wait_time_in_seconds=1)],
        schedules=[schedule],
    )
    item_dir = pipeline.save_item(tmp_path)
    assert (item_dir / ".schedules").exists()


def test_to_definition() -> None:
    pipeline = Pipeline(
        name="def",
        activities=[Wait(name="w", wait_time_in_seconds=1)],
        logical_id="00000000-0000-0000-0000-000000000002",
    )
    definition = pipeline.to_definition()
    assert len(definition["parts"]) == 2
    paths = {part["path"] for part in definition["parts"]}
    assert paths == {"pipeline-content.json", ".platform"}
    content_part = next(p for p in definition["parts"] if p["path"] == "pipeline-content.json")
    decoded = base64.b64decode(content_part["payload"]).decode("utf-8")
    assert json.loads(decoded)["properties"]["activities"][0]["type"] == "Wait"
