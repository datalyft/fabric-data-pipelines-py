"""Dataflow Gen2 (RefreshDataFlow) activity."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, model_validator

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy
from fabric_data_pipelines.activities.checks import require_non_empty_str


class Dataflow(Activity):
    """Refresh a Fabric Dataflow Gen2.

    Serializes as Fabric activity type ``RefreshDataFlow``.

    Example::

        from fabric_data_pipelines import Dataflow

        dataflow = Dataflow(
            name="refresh_sales",
            dataflow_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            workspace_id="00000000-0000-0000-0000-000000000001",
        )
    """

    activity_type: ClassVar[str] = "RefreshDataFlow"

    dataflow_id: str
    workspace_id: str
    notify_option: str | None = None
    dataflow_type: str | None = None
    parameters: dict[str, Any] | None = None

    policy: ActivityPolicy | None = Field(default_factory=ActivityPolicy)

    @model_validator(mode="after")
    def _validate_dataflow(self) -> Dataflow:
        require_non_empty_str(self.dataflow_id, field="dataflow_id")
        require_non_empty_str(self.workspace_id, field="workspace_id")
        return self
