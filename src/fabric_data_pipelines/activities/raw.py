"""Generic RawActivity escape hatch for unmodeled Fabric activity types."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from fabric_data_pipelines.activities.base import Activity


class RawActivity(Activity):
    """Pass-through activity for Fabric types not yet modeled.

    Use this for activity types outside the modeled set (GetMetadata,
    PBISemanticModelRefresh, Filter, …).

    Example::

        from fabric_data_pipelines import RawActivity, ActivityPolicy

        meta = RawActivity(
            name="Get Metadata1",
            type="GetMetadata",
            type_properties={
                "fieldList": ["columnCount"],
                "datasetSettings": {...},
            },
            policy=ActivityPolicy(),
        )
    """

    activity_type: ClassVar[str] = ""
    _exclude_from_type_properties: ClassVar[frozenset[str]] = frozenset({"type"})

    type: str
    type_properties: dict[str, Any] = Field(default_factory=dict)
