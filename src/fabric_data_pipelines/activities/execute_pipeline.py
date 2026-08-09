"""ExecutePipeline activity."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, model_validator

from fabric_data_pipelines.activities.base import Activity, SecureInputOutputPolicy
from fabric_data_pipelines.activities.checks import require_non_empty_str
from fabric_data_pipelines.errors import PipelineValidationError
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

    @model_validator(mode="after")
    def _validate_execute_pipeline(self) -> ExecutePipeline:
        if isinstance(self.pipeline, PipelineReference):
            require_non_empty_str(self.pipeline.reference_name, field="pipeline.reference_name")
            return self
        if isinstance(self.pipeline, dict):
            ref = self.pipeline.get("referenceName", self.pipeline.get("reference_name"))
            if not isinstance(ref, str) or not ref.strip():
                raise PipelineValidationError(
                    f"ExecutePipeline activity '{self.name}' requires pipeline.reference_name"
                )
            return self
        raise PipelineValidationError(
            f"ExecutePipeline activity '{self.name}' pipeline must be a PipelineReference or dict"
        )
