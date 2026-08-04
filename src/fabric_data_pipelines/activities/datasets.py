"""Dataset settings used by Copy, Lookup, and related activities."""

from __future__ import annotations

from typing import Any

from pydantic import Field, PrivateAttr, field_validator, model_serializer

from fabric_data_pipelines.activities.base import ExternalReferences
from fabric_data_pipelines.serialization import FabricModel


class LinkedServiceProperties(FabricModel):
    """Inner ``properties`` block of a Fabric linked service / connection reference."""

    type: str
    type_properties: dict[str, Any] = Field(default_factory=dict)
    annotations: list[Any] = Field(default_factory=list)
    external_references: ExternalReferences | None = None


class LinkedService(FabricModel):
    """A named linked service or connectionSettings embedded in dataset settings.

    Example::

        LinkedService(
            name="LakehouseGitArtifactW1",
            properties=LinkedServiceProperties(
                type="Lakehouse",
                type_properties={
                    "workspaceId": "...",
                    "artifactId": "...",
                    "rootFolder": "Tables",
                },
            ),
        )
    """

    name: str
    properties: LinkedServiceProperties


class DatasetSettings(FabricModel):
    """Base dataset settings with Fabric UI boilerplate.

    Always emits ``annotations: []`` and ``schema: []`` so generated JSON
    matches Fabric UI exports. Fabric sometimes exports an empty schema as
    ``{}``; that is normalized to ``[]`` on import.
    """

    type: str
    type_properties: dict[str, Any] = Field(default_factory=dict)
    annotations: list[Any] = Field(default_factory=list)
    schema_: list[Any] = Field(default_factory=list, alias="schema")
    external_references: ExternalReferences | None = None
    linked_service: LinkedService | None = None
    connection_settings: LinkedService | None = None
    parameters: dict[str, Any] | None = None
    description: str | None = None

    @field_validator("schema_", mode="before")
    @classmethod
    def _coerce_empty_schema_object(cls, value: Any) -> Any:
        # Fabric UI occasionally emits ``"schema": {}`` instead of ``[]``.
        if isinstance(value, dict) and not value:
            return []
        return value

    @model_serializer(mode="wrap")
    def _serialize(self, handler: Any) -> dict[str, Any]:
        _ = handler
        data: dict[str, Any] = {
            "type": self.type,
            "annotations": list(self.annotations),
            "schema": list(self.schema_),
            "typeProperties": dict(self.type_properties),
        }
        if self.external_references is not None:
            data["externalReferences"] = self.external_references.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            )
        if self.linked_service is not None:
            data["linkedService"] = self.linked_service.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            )
        if self.connection_settings is not None:
            data["connectionSettings"] = self.connection_settings.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            )
        if self.parameters is not None:
            data["parameters"] = self.parameters
        if self.description is not None:
            data["description"] = self.description
        return data


def _build_sql_table_tp(
    *,
    database: str | None,
    table: str | None,
    schema_name: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    tp = dict(extra)
    if database is not None:
        tp.setdefault("database", database)
    if table is not None:
        tp.setdefault("table", table)
    if schema_name is not None:
        tp.setdefault("schema", schema_name)
    return tp


class LakehouseTable(DatasetSettings):
    """Lakehouse table dataset.

    Example::

        LakehouseTable(
            table="sales",
            linked_service=LinkedService(
                name="MyLakehouse",
                properties=LinkedServiceProperties(
                    type="Lakehouse",
                    type_properties={
                        "workspaceId": "...",
                        "artifactId": "...",
                        "rootFolder": "Tables",
                    },
                ),
            ),
        )
    """

    type: str = "LakehouseTable"
    _table: str | None = PrivateAttr(default=None)
    _schema_name: str | None = PrivateAttr(default=None)

    def __init__(
        self,
        *,
        table: str | None = None,
        schema_name: str | None = None,
        type_properties: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        tp = dict(type_properties or {})
        if table is not None:
            tp.setdefault("table", table)
        if schema_name is not None:
            tp.setdefault("schema", schema_name)
        super().__init__(type="LakehouseTable", type_properties=tp, **kwargs)
        self._table = table
        self._schema_name = schema_name


class AzureSqlMITable(DatasetSettings):
    """Azure SQL Managed Instance table dataset.

    Example::

        AzureSqlMITable(
            database="Landing",
            schema_name="sales",
            table="customers",
            connection="@pipeline().libraryVariables.Landing",
        )
    """

    type: str = "AzureSqlMITable"

    def __init__(
        self,
        *,
        database: str | None = None,
        table: str | None = None,
        schema_name: str | None = None,
        connection: str | None = None,
        type_properties: dict[str, Any] | None = None,
        external_references: ExternalReferences | None = None,
        **kwargs: Any,
    ) -> None:
        tp = _build_sql_table_tp(
            database=database,
            table=table,
            schema_name=schema_name,
            extra=dict(type_properties or {}),
        )
        refs = external_references
        if connection is not None and refs is None:
            refs = ExternalReferences(connection=connection)
        super().__init__(
            type="AzureSqlMITable",
            type_properties=tp,
            external_references=refs,
            **kwargs,
        )


class AzureSqlTable(DatasetSettings):
    """Azure SQL Database table dataset."""

    type: str = "AzureSqlTable"

    def __init__(
        self,
        *,
        database: str | None = None,
        table: str | None = None,
        schema_name: str | None = None,
        connection: str | None = None,
        type_properties: dict[str, Any] | None = None,
        external_references: ExternalReferences | None = None,
        **kwargs: Any,
    ) -> None:
        tp = _build_sql_table_tp(
            database=database,
            table=table,
            schema_name=schema_name,
            extra=dict(type_properties or {}),
        )
        refs = external_references
        if connection is not None and refs is None:
            refs = ExternalReferences(connection=connection)
        super().__init__(
            type="AzureSqlTable",
            type_properties=tp,
            external_references=refs,
            **kwargs,
        )


class DataWarehouseTable(DatasetSettings):
    """Fabric Data Warehouse table dataset."""

    type: str = "DataWarehouseTable"

    def __init__(
        self,
        *,
        table: str | None = None,
        schema_name: str | None = None,
        connection: str | None = None,
        type_properties: dict[str, Any] | None = None,
        external_references: ExternalReferences | None = None,
        **kwargs: Any,
    ) -> None:
        tp = _build_sql_table_tp(
            database=None,
            table=table,
            schema_name=schema_name,
            extra=dict(type_properties or {}),
        )
        refs = external_references
        if connection is not None and refs is None:
            refs = ExternalReferences(connection=connection)
        super().__init__(
            type="DataWarehouseTable",
            type_properties=tp,
            external_references=refs,
            **kwargs,
        )


class Dataset(DatasetSettings):
    """Generic dataset escape hatch for any Fabric dataset type.

    Example::

        Dataset(type="DelimitedText", type_properties={"location": {...}})
    """
