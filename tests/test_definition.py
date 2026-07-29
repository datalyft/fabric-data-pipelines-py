"""Unit tests for to_definition REST payload."""

import base64
import json

from fabric_data_pipelines import Notebook, Pipeline


def test_definition_parts_round_trip() -> None:
    pipeline = Pipeline(
        name="nb_pipe",
        activities=[
            Notebook(
                name="Notebook1",
                notebook_id="00000000-0000-0000-0000-000000000002",
                workspace_id="00000000-0000-0000-0000-000000000001",
            )
        ],
        logical_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    )
    definition = pipeline.to_definition()
    platform_part = next(p for p in definition["parts"] if p["path"] == ".platform")
    platform = json.loads(base64.b64decode(platform_part["payload"]))
    assert platform["metadata"]["type"] == "DataPipeline"
    assert platform["config"]["logicalId"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert platform_part["payloadType"] == "InlineBase64"
