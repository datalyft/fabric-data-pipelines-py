"""Lookup activity."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy
from fabric_data_pipelines.activities.copy import CopySource
from fabric_data_pipelines.activities.datasets import DatasetSettings


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
