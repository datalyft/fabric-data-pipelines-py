"""Landing truncate-and-copy — classic SQL MI ingestion pattern.

Scenario: truncate a landing table, then copy a typed column subset from a
source database into Landing with explicit column mappings.
"""

from fabric_data_pipelines import (
    AzureSqlMITable,
    ColumnMapping,
    ColumnRef,
    Copy,
    ExternalReferences,
    LibraryVariable,
    Pipeline,
    Script,
    ScriptBlock,
    SqlMISink,
    SqlMISource,
    TabularTranslator,
    TypeConversionSettings,
    expr,
)

LANDING = expr.library_variable("Demo_ETL_Library_Landing")
SOURCE = expr.library_variable("Demo_ETL_Library_SourceDb")

COLUMNS = [
    "customer_id",
    "region",
    "segment",
    "updated_at",
]

SELECT_SQL = """\
SELECT
   CAST([customer_id] AS NVARCHAR (12)) AS [customer_id]
   , [region]
   , [segment]
   , [updated_at]
FROM [dbo].[customers];
"""

truncate = Script(
    name="Truncate_Landing_customers",
    database="Landing",
    scripts=[
        ScriptBlock(
            text={"value": "TRUNCATE TABLE sales.customers", "type": "Expression"},
            type="Query",
        )
    ],
    script_block_execution_timeout="02:00:00",
    external_references=ExternalReferences(connection=LANDING),
)

copy = Copy(
    name="Copy_customers_to_Landing",
    source=SqlMISource(
        sql_reader_query=SELECT_SQL,
        partition_option="None",
        dataset_settings=AzureSqlMITable(
            database="SourceDb",
            connection=SOURCE,
        ),
    ),
    sink=SqlMISink(
        write_behavior="insert",
        sql_writer_use_table_lock=True,
        dataset_settings=AzureSqlMITable(
            database="Landing",
            schema_name="sales",
            table="customers",
            connection=LANDING,
        ),
    ),
    enable_staging=False,
    translator=TabularTranslator(
        mappings=[
            ColumnMapping(
                source=ColumnRef(name=col, type="String", physical_type="nvarchar"),
                sink=ColumnRef(name=col, type="String", physical_type="nvarchar"),
            )
            for col in COLUMNS
        ],
        type_conversion=True,
        type_conversion_settings=TypeConversionSettings(
            allow_data_truncation=True,
            treat_boolean_as_number=False,
        ),
    ),
)
truncate.then(copy)

pipeline = Pipeline(
    name="Landing_customers",
    description="Truncate Landing.sales.customers, then load a typed subset from SourceDb.",
    activities=[truncate, copy],
    library_variables={
        "Demo_ETL_Library_Landing": LibraryVariable(
            type="String",
            variable_name="Landing",
            library_name="Demo_ETL_Library",
        ),
        "Demo_ETL_Library_SourceDb": LibraryVariable(
            type="String",
            variable_name="SourceDb",
            library_name="Demo_ETL_Library",
        ),
    },
)

if __name__ == "__main__":
    print(pipeline.to_json())
