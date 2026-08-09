"""Lookup activity."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, model_validator

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy
from fabric_data_pipelines.activities.checks import get_type_name, require_non_empty_str
from fabric_data_pipelines.activities.copy import CopySource, check_connector_dataset
from fabric_data_pipelines.activities.datasets import DatasetSettings
from fabric_data_pipelines.errors import PipelineValidationError


class Lookup(Activity):
    """Retrieve a row (or rows) for use by subsequent activities.

    Example::

        from fabric_data_pipelines import Lookup, LakehouseTableSource, LakehouseTable

        lookup = Lookup(
            name="get_tables",
            source=LakehouseTableSource(),
            dataset_settings=LakehouseTable(table="lh2", linked_service=...),
            first_row_only=True,
        )
    """

    activity_type: ClassVar[str] = "Lookup"

    source: CopySource | dict[str, Any]
    dataset_settings: DatasetSettings | dict[str, Any]
    first_row_only: bool | None = None

    policy: ActivityPolicy | None = Field(default_factory=ActivityPolicy)

    @model_validator(mode="after")
    def _validate_lookup(self) -> Lookup:
        source_type = get_type_name(self.source)
        if source_type is None:
            raise PipelineValidationError(
                f"Lookup activity '{self.name}' source.type must be a non-empty string"
            )
        dataset_type = get_type_name(self.dataset_settings)
        if dataset_type is None:
            raise PipelineValidationError(
                f"Lookup activity '{self.name}' dataset_settings.type must be a non-empty string"
            )
        require_non_empty_str(source_type, field="source.type")
        require_non_empty_str(dataset_type, field="dataset_settings.type")
        check_connector_dataset(
            self.source,
            dataset=self.dataset_settings,
            role=f"source '{source_type}'",
        )
        return self
