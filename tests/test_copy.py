"""Unit tests for Copy activity serialization."""

from fabric_data_pipelines import (
    AzureSqlMITable,
    ColumnMapping,
    ColumnRef,
    Copy,
    Pipeline,
    SqlMISink,
    SqlMISource,
    TabularTranslator,
    TypeConversionSettings,
    expr,
)


def test_copy_sql_mi_round_shape() -> None:
    copy = Copy(
        name="Copy_customers",
        source=SqlMISource(
            sql_reader_query="SELECT 1 AS id",
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
        translator=TabularTranslator(
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
        ),
    )
    data = copy.to_dict()
    assert data["type"] == "Copy"
    assert data["typeProperties"]["source"]["type"] == "SqlMISource"
    assert data["typeProperties"]["sink"]["type"] == "SqlMISink"
    assert data["typeProperties"]["source"]["datasetSettings"]["type"] == "AzureSqlMITable"
    assert data["typeProperties"]["source"]["datasetSettings"]["annotations"] == []
    assert data["typeProperties"]["source"]["datasetSettings"]["schema"] == []
    assert data["policy"]["timeout"] == "0.12:00:00"

    pipeline = Pipeline(name="copy_demo", activities=[copy])
    assert pipeline.to_dict()["properties"]["activities"][0]["name"] == "Copy_customers"
