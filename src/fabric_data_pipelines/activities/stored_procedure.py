"""SqlServerStoredProcedure activity."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, model_validator

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy
from fabric_data_pipelines.activities.checks import require_non_empty_str
from fabric_data_pipelines.errors import PipelineValidationError


class StoredProcedure(Activity):
    """Execute a SQL Server stored procedure.

    Serializes as Fabric activity type ``SqlServerStoredProcedure``.

    Example::

        from fabric_data_pipelines import StoredProcedure, ExternalReferences

        sp = StoredProcedure(
            name="run_merge",
            stored_procedure_name="dbo.usp_MergeSales",
            database="Warehouse",
            stored_procedure_parameters={"RunDate": {"value": "2024-01-01", "type": "String"}},
            external_references=ExternalReferences(connection="..."),
        )
    """

    activity_type: ClassVar[str] = "SqlServerStoredProcedure"

    stored_procedure_name: str
    database: str | None = None
    stored_procedure_parameters: dict[str, Any] | None = None
    linked_service: dict[str, Any] | None = None
    connection_settings: dict[str, Any] | None = None

    policy: ActivityPolicy | None = Field(default_factory=ActivityPolicy)

    @model_validator(mode="after")
    def _validate_stored_procedure(self) -> StoredProcedure:
        require_non_empty_str(self.stored_procedure_name, field="stored_procedure_name")
        has_connection = (
            self.external_references is not None
            or self.linked_service is not None
            or self.connection_settings is not None
        )
        if not has_connection:
            raise PipelineValidationError(
                f"StoredProcedure activity '{self.name}' requires external_references, "
                "linked_service, or connection_settings"
            )
        return self
