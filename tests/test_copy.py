"""Unit tests for Copy activity serialization."""

from fabric_data_pipelines import (
    AzureSqlMITable,
    ColumnMapping,
    ColumnRef,
    Copy,
    DataWarehouseSource,
    DataWarehouseTable,
    Expression,
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


def test_sql_mi_source_expression_sql_reader_query_round_trip() -> None:
    """Fabric may emit sqlReaderQuery as an Expression object (#16)."""
    payload = {
        "properties": {
            "activities": [
                {
                    "name": "Copy_Dynamic_Query",
                    "type": "Copy",
                    "dependsOn": [],
                    "typeProperties": {
                        "source": {
                            "type": "SqlMISource",
                            "sqlReaderQuery": {
                                "value": "@variables('query_sql')",
                                "type": "Expression",
                            },
                            "datasetSettings": {
                                "type": "AzureSqlMITable",
                                "typeProperties": {
                                    "schema": "dbo",
                                    "table": "customers",
                                    "database": "SourceDb",
                                },
                                "externalReferences": {
                                    "connection": ("@pipeline().libraryVariables.Demo_Source")
                                },
                            },
                        },
                        "sink": {
                            "type": "SqlMISink",
                            "writeBehavior": "insert",
                            "datasetSettings": {
                                "type": "AzureSqlMITable",
                                "typeProperties": {
                                    "schema": "dbo",
                                    "table": "customers",
                                    "database": "Landing",
                                },
                                "externalReferences": {
                                    "connection": ("@pipeline().libraryVariables.Demo_Landing")
                                },
                            },
                        },
                    },
                }
            ]
        }
    }
    pipeline = Pipeline.from_dict(payload, name="demo_dynamic_copy")
    copy = pipeline.activities[0]
    assert isinstance(copy, Copy)
    assert isinstance(copy.source, SqlMISource)
    assert isinstance(copy.source.sql_reader_query, Expression)
    assert copy.source.sql_reader_query.value == "@variables('query_sql')"

    exported = pipeline.to_dict()
    query = exported["properties"]["activities"][0]["typeProperties"]["source"]["sqlReaderQuery"]
    assert query == {"value": "@variables('query_sql')", "type": "Expression"}


def test_sql_mi_source_string_sql_reader_query_unchanged() -> None:
    source = SqlMISource(sql_reader_query="SELECT 1 AS id")
    dumped = source.model_dump(by_alias=True, exclude_none=True, mode="json")
    assert dumped["sqlReaderQuery"] == "SELECT 1 AS id"


def test_data_warehouse_source_expression_sql_reader_query() -> None:
    source = DataWarehouseSource(
        sql_reader_query={
            "value": "@variables('query_sql')",
            "type": "Expression",
        },
        dataset_settings=DataWarehouseTable(
            table="customers",
            connection=expr.library_variable("Demo_Wh"),
        ),
    )
    assert isinstance(source.sql_reader_query, Expression)
    dumped = source.model_dump(by_alias=True, exclude_none=True, mode="json")
    assert dumped["sqlReaderQuery"] == {
        "value": "@variables('query_sql')",
        "type": "Expression",
    }
