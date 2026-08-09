"""Copy activity and source/sink helpers."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict, Field, field_validator, model_serializer, model_validator

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy, ExternalReferences
from fabric_data_pipelines.activities.checks import get_dataset_settings, get_type_name
from fabric_data_pipelines.activities.datasets import DatasetSettings
from fabric_data_pipelines.errors import InvalidChoiceError, PipelineValidationError
from fabric_data_pipelines.serialization import Expression, FabricModel, to_camel

# Fabric emits sqlReaderQuery as a plain string or an Expression object.
SqlReaderQuery = Expression | str | dict[str, Any]

# Known connector → allowed dataset types. Unknown types skip pairing (escape hatch).
CONNECTOR_DATASETS: dict[str, tuple[str, ...]] = {
    "SqlMISource": ("AzureSqlMITable", "AzureSqlTable"),
    "SqlMISink": ("AzureSqlMITable", "AzureSqlTable"),
    "LakehouseTableSource": ("LakehouseTable",),
    "LakehouseTableSink": ("LakehouseTable",),
    "DataWarehouseSource": ("DataWarehouseTable",),
    "DataWarehouseSink": ("DataWarehouseTable",),
}
_KNOWN_DATASETS: frozenset[str] = frozenset(
    dataset for datasets in CONNECTOR_DATASETS.values() for dataset in datasets
)


def check_connector_dataset(
    connector: Any,
    *,
    dataset: Any = None,
    role: str,
) -> None:
    """Reject known connector/dataset pairs that Fabric will not accept.

    Skips when the connector or dataset ``type`` is unknown so generic escape
    hatches keep working.
    """
    connector_type = get_type_name(connector)
    if connector_type is None or connector_type not in CONNECTOR_DATASETS:
        return
    ds = dataset if dataset is not None else get_dataset_settings(connector)
    if ds is None:
        return
    dataset_type = get_type_name(ds)
    if dataset_type is None or dataset_type not in _KNOWN_DATASETS:
        return
    allowed = CONNECTOR_DATASETS[connector_type]
    if dataset_type not in allowed:
        raise InvalidChoiceError(
            field="dataset",
            value=dataset_type,
            valid=allowed,
            context=f" for {role}",
        )


def _coerce_sql_reader_query(value: Any) -> Any:
    """Accept Expression dicts the same way ``ScriptBlock.text`` does."""
    if isinstance(value, dict) and "value" in value:
        return value
    return value


class _ConnectorModel(FabricModel):
    """Base for CopySource/CopySink that keeps unknown connector keys."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="allow",
        arbitrary_types_allowed=True,
    )

    @model_serializer(mode="wrap")
    def _serialize(self, handler: Any) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        # Merge extras that pydantic may have stored under __pydantic_extra__.
        extras = getattr(self, "__pydantic_extra__", None) or {}
        for key, value in extras.items():
            camel = to_camel(key) if "_" in key else key
            if camel not in data and value is not None:
                data[camel] = value
        return {k: v for k, v in data.items() if v is not None}


class CopySource(_ConnectorModel):
    """Generic copy source escape hatch.

    Example::

        CopySource(type="SqlMISource", sql_reader_query="SELECT 1", dataset_settings=...)
    """

    type: str
    dataset_settings: DatasetSettings | dict[str, Any] | None = None
    source_retry_count: int | None = None
    source_retry_wait: str | None = None
    max_concurrent_connections: int | None = None
    disable_metrics_collection: bool | None = None


class CopySink(_ConnectorModel):
    """Generic copy sink escape hatch.

    Example::

        CopySink(type="SqlMISink", write_behavior="insert", dataset_settings=...)
    """

    type: str
    dataset_settings: DatasetSettings | dict[str, Any] | None = None
    write_batch_size: int | None = None
    write_batch_timeout: str | None = None
    sink_retry_count: int | None = None
    sink_retry_wait: str | None = None
    max_concurrent_connections: int | None = None
    disable_metrics_collection: bool | None = None


class SqlMISource(CopySource):
    """Azure SQL Managed Instance copy source.

    ``sql_reader_query`` accepts a plain SQL string or a Fabric Expression
    object (``{"value": "...", "type": "Expression"}``), matching UI exports
    that bind the query from pipeline variables.

    Example::

        SqlMISource(
            sql_reader_query="SELECT * FROM dbo.customers",
            dataset_settings=AzureSqlMITable(
                database="SourceDb",
                connection=expr.library_variable("SourceDb"),
            ),
        )
    """

    type: str = "SqlMISource"
    sql_reader_query: SqlReaderQuery | None = None
    partition_option: str | None = None

    @field_validator("sql_reader_query", mode="before")
    @classmethod
    def _coerce_sql_reader_query(cls, value: Any) -> Any:
        return _coerce_sql_reader_query(value)


class SqlMISink(CopySink):
    """Azure SQL Managed Instance copy sink."""

    type: str = "SqlMISink"
    write_behavior: str | None = None
    sql_writer_use_table_lock: bool | None = None


class LakehouseTableSource(CopySource):
    """Lakehouse table copy source."""

    type: str = "LakehouseTableSource"


class LakehouseTableSink(CopySink):
    """Lakehouse table copy sink."""

    type: str = "LakehouseTableSink"


class DataWarehouseSource(CopySource):
    """Fabric Data Warehouse copy source.

    ``sql_reader_query`` accepts a plain SQL string or a Fabric Expression
    object, same as :class:`SqlMISource`.
    """

    type: str = "DataWarehouseSource"
    sql_reader_query: SqlReaderQuery | None = None

    @field_validator("sql_reader_query", mode="before")
    @classmethod
    def _coerce_sql_reader_query(cls, value: Any) -> Any:
        return _coerce_sql_reader_query(value)


class DataWarehouseSink(CopySink):
    """Fabric Data Warehouse copy sink."""

    type: str = "DataWarehouseSink"
    write_behavior: str | None = None


class ColumnRef(FabricModel):
    """A column reference inside a TabularTranslator mapping."""

    name: str
    type: str | None = None
    physical_type: str | None = None


class ColumnMapping(FabricModel):
    """A single source→sink column mapping."""

    source: ColumnRef
    sink: ColumnRef


class TypeConversionSettings(FabricModel):
    """Advanced type-conversion settings for a TabularTranslator."""

    allow_data_truncation: bool | None = None
    treat_boolean_as_number: bool | None = None
    date_time_format: str | None = None
    date_time_offset_format: str | None = None
    time_span_format: str | None = None
    culture: str | None = None


class TabularTranslator(FabricModel):
    """Tabular translator with optional column mappings.

    Example::

        TabularTranslator(
            mappings=[
                ColumnMapping(
                    source=ColumnRef(name="id", type="String", physical_type="nvarchar"),
                    sink=ColumnRef(name="id", type="String", physical_type="nvarchar"),
                )
            ],
            type_conversion=True,
            type_conversion_settings=TypeConversionSettings(
                allow_data_truncation=True,
                treat_boolean_as_number=False,
            ),
        )
    """

    type: str = "TabularTranslator"
    mappings: list[ColumnMapping] | None = None
    type_conversion: bool | None = None
    type_conversion_settings: TypeConversionSettings | None = None
    column_mappings: str | None = None
    schema_mapping: str | None = None


class StagingSettings(FabricModel):
    """Interim staging settings when ``enable_staging`` is true."""

    external_references: ExternalReferences
    enable_compression: bool | None = None
    path: str | None = None


class Copy(Activity):
    """Copy data from a source to a sink.

    Example::

        from fabric_data_pipelines import Copy, SqlMISource, SqlMISink, AzureSqlMITable, expr

        copy = Copy(
            name="Copy_customers",
            source=SqlMISource(
                sql_reader_query="SELECT * FROM dbo.customers",
                partition_option="None",
                dataset_settings=AzureSqlMITable(
                    database="SourceDb",
                    connection=expr.library_variable("SourceDb"),
                ),
            ),
            sink=SqlMISink(
                write_behavior="insert",
                sql_writer_use_table_lock=True,
                dataset_settings=AzureSqlMITable(
                    database="Landing",
                    schema_name="sales",
                    table="customers",
                    connection=expr.library_variable("Landing"),
                ),
            ),
            enable_staging=False,
        )
    """

    activity_type: ClassVar[str] = "Copy"

    source: CopySource | dict[str, Any]
    sink: CopySink | dict[str, Any] | None = None
    destination: CopySink | dict[str, Any] | None = None
    translator: TabularTranslator | dict[str, Any] | None = None
    enable_staging: bool | None = None
    staging_settings: StagingSettings | dict[str, Any] | None = None
    parallel_copies: int | None = None
    data_integration_units: int | None = None
    enable_skip_incompatible_row: bool | None = None

    policy: ActivityPolicy | None = Field(default_factory=ActivityPolicy)

    @model_validator(mode="after")
    def _validate_copy(self) -> Copy:
        if self.sink is None and self.destination is None:
            raise PipelineValidationError(
                f"Copy activity '{self.name}' requires sink or destination"
            )
        if self.sink is not None and self.destination is not None:
            raise PipelineValidationError(
                f"Copy activity '{self.name}' must set only one of sink or destination"
            )
        if self.enable_staging is True and self.staging_settings is None:
            raise PipelineValidationError(
                f"Copy activity '{self.name}' has enable_staging=True "
                "but staging_settings is missing"
            )
        if self.enable_staging is not True and self.staging_settings is not None:
            raise PipelineValidationError(
                f"Copy activity '{self.name}' has staging_settings but enable_staging is not True"
            )
        if self.parallel_copies is not None and self.parallel_copies <= 0:
            raise PipelineValidationError(
                f"Copy activity '{self.name}' parallel_copies must be > 0"
            )
        if self.data_integration_units is not None and self.data_integration_units <= 0:
            raise PipelineValidationError(
                f"Copy activity '{self.name}' data_integration_units must be > 0"
            )

        source_type = get_type_name(self.source) or "source"
        check_connector_dataset(self.source, role=f"source '{source_type}'")
        target = self.sink if self.sink is not None else self.destination
        target_type = get_type_name(target) or "sink"
        check_connector_dataset(target, role=f"sink '{target_type}'")
        return self
