"""ExecutePipeline activity."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from fabric_data_pipelines.activities.base import Activity, SecureInputOutputPolicy
from fabric_data_pipelines.serialization import FabricModel


class PipelineReference(FabricModel):
    """Reference to another pipeline by id or name.

    Example::

        PipelineReference(reference_name="11111111-1111-1111-1111-111111111111")
    """

    reference_name: str
    type: str = "PipelineReference"


class ExecutePipeline(Activity):
    """Execute another pipeline as a nested activity.

    Example::

        from fabric_data_pipelines import ExecutePipeline, PipelineReference

        invoke = ExecutePipeline(
            name="Invoke_History_Full_Load",
            pipeline=PipelineReference(reference_name="11111111-1111-1111-1111-111111111111"),
            parameters={"full_load": 1},
            wait_on_completion=True,
        )
    """

    activity_type: ClassVar[str] = "ExecutePipeline"

    pipeline: PipelineReference | dict[str, Any]
    parameters: dict[str, Any] | None = None
    wait_on_completion: bool | None = None

    # Fabric UI exports ExecutePipeline with only secureInput: false.
    policy: SecureInputOutputPolicy | None = Field(
        default_factory=lambda: SecureInputOutputPolicy(secure_input=False)
    )
