"""Trident (Fabric) Notebook activity."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, model_validator

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy
from fabric_data_pipelines.activities.checks import require_non_empty_str


class Notebook(Activity):
    """Execute a Fabric (Trident) notebook.

    Serializes as Fabric activity type ``TridentNotebook``.

    Example::

        from fabric_data_pipelines import Notebook

        notebook = Notebook(
            name="transform",
            notebook_id="00000000-0000-0000-0000-000000000002",
            workspace_id="00000000-0000-0000-0000-000000000001",
            parameters={"run_date": {"value": "2024-01-01", "type": "string"}},
        )
    """

    activity_type: ClassVar[str] = "TridentNotebook"

    notebook_id: str
    workspace_id: str
    parameters: dict[str, Any] | None = None
    session_tag: str | None = None

    policy: ActivityPolicy | None = Field(default_factory=ActivityPolicy)

    @model_validator(mode="after")
    def _validate_notebook(self) -> Notebook:
        require_non_empty_str(self.notebook_id, field="notebook_id")
        require_non_empty_str(self.workspace_id, field="workspace_id")
        return self
