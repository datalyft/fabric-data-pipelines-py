"""Parameterized ELT controller — ForEach, Switch, Dataflow, and Fail.

Scenario: a parent controller receives a list of tables and a load mode.
For each table it refreshes a Dataflow Gen2 item, then branches:
- ``full`` runs a warehouse merge stored procedure
- anything else fails fast with a clear error code
"""

from fabric_data_pipelines import (
    Dataflow,
    Expression,
    ExternalReferences,
    Fail,
    ForEach,
    Parameter,
    Pipeline,
    StoredProcedure,
    Switch,
    SwitchCase,
    expr,
)

WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"
DATAFLOW_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
WAREHOUSE_CONN = "11111111-2222-3333-4444-555555555555"

refresh_table = Dataflow(
    name="Refresh_Table_Dataflow",
    dataflow_id=DATAFLOW_ID,
    workspace_id=WORKSPACE_ID,
)

for_each_table = ForEach(
    name="ForEach_Table",
    items=Expression(value=expr.parameter("tables")),
    is_sequential=True,
    activities=[refresh_table],
)

run_merge = StoredProcedure(
    name="Run_Warehouse_Merge",
    stored_procedure_name="dbo.usp_MergeSales",
    database="Warehouse",
    external_references=ExternalReferences(connection=WAREHOUSE_CONN),
)

fail_unknown_mode = Fail(
    name="Fail_Unknown_Mode",
    message="Unknown load mode; expected 'full'.",
    error_code="BadMode",
)

by_mode = Switch(
    name="Switch_By_Mode",
    on=Expression(value=expr.parameter("mode")),
    cases=[SwitchCase(value="full", activities=[run_merge])],
    default_activities=[fail_unknown_mode],
)
for_each_table.then(by_mode)

pipeline = Pipeline(
    name="ELT_Controller_Sales",
    description=(
        "Parameterized ELT controller: refresh each table via Dataflow, "
        "then merge on full loads or fail on unknown modes."
    ),
    activities=[for_each_table, by_mode],
    parameters={
        "tables": Parameter(
            type="Array",
            default_value=["sales_header", "sales_line", "customer"],
        ),
        "mode": Parameter(type="String", default_value="full"),
    },
)

if __name__ == "__main__":
    print(pipeline.to_json())
