"""Lakehouse lookup → warehouse copy — ELT hand-off pattern.

Scenario: look up the latest batch watermark from a Lakehouse control table,
store it in a pipeline variable, then copy that batch's facts into a Fabric
Warehouse table for reporting.
"""

from fabric_data_pipelines import (
    Copy,
    DataWarehouseSink,
    DataWarehouseTable,
    LakehouseTable,
    LakehouseTableSource,
    LibraryVariable,
    LinkedService,
    LinkedServiceProperties,
    Lookup,
    Parameter,
    Pipeline,
    SetVariable,
    Variable,
    expr,
)

WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"
LAKEHOUSE_ID = "00000000-0000-0000-0000-000000000003"

lakehouse = LinkedService(
    name="Silver_Sales_Lakehouse",
    properties=LinkedServiceProperties(
        type="Lakehouse",
        type_properties={
            "workspaceId": WORKSPACE_ID,
            "artifactId": LAKEHOUSE_ID,
            "rootFolder": "Tables",
        },
    ),
)

lookup_watermark = Lookup(
    name="Lookup_Latest_Batch",
    source=LakehouseTableSource(),
    dataset_settings=LakehouseTable(
        table="etl_watermarks",
        schema_name="ctrl",
        linked_service=lakehouse,
    ),
    first_row_only=True,
)

set_batch_id = SetVariable(
    name="Set_batch_id",
    variable_name="batch_id",
    value=expr.activity_output("Lookup_Latest_Batch", "firstRow.batch_id"),
)
lookup_watermark.then(set_batch_id)

copy_facts = Copy(
    name="Copy_Sales_Facts_to_Warehouse",
    source=LakehouseTableSource(
        dataset_settings=LakehouseTable(
            table="sales_facts",
            schema_name="silver",
            linked_service=lakehouse,
        ),
    ),
    sink=DataWarehouseSink(
        write_behavior="append",
        dataset_settings=DataWarehouseTable(
            schema_name="dbo",
            table="sales_facts",
            connection=expr.library_variable("Demo_ETL_Library_Warehouse"),
        ),
    ),
    enable_staging=False,
)
set_batch_id.then(copy_facts)

pipeline = Pipeline(
    name="Silver_to_Gold_Sales_Facts",
    description=(
        "Read the latest batch watermark from Lakehouse control tables, "
        "then append silver sales facts into the Warehouse."
    ),
    activities=[lookup_watermark, set_batch_id, copy_facts],
    parameters={
        "run_date": Parameter(type="String", default_value=""),
    },
    variables={
        "batch_id": Variable(type="String", default_value=""),
    },
    library_variables={
        "Demo_ETL_Library_Warehouse": LibraryVariable(
            type="String",
            variable_name="Warehouse",
            library_name="Demo_ETL_Library",
        ),
    },
)

if __name__ == "__main__":
    print(pipeline.to_json())
