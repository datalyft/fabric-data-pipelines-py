"""Snapshot parity tests against known-good Fabric pipeline JSON."""

from __future__ import annotations

from fabric_data_pipelines import (
    ActivityPolicy,
    AzureSqlMITable,
    ColumnMapping,
    ColumnRef,
    Copy,
    Dataflow,
    ExecutePipeline,
    Expression,
    ExternalReferences,
    Fail,
    ForEach,
    IfCondition,
    LakehouseTable,
    LakehouseTableSource,
    LibraryVariable,
    LinkedService,
    LinkedServiceProperties,
    Lookup,
    Notebook,
    Parameter,
    Pipeline,
    PipelineReference,
    RawActivity,
    Script,
    ScriptBlock,
    SqlMISink,
    SqlMISource,
    StoredProcedure,
    Switch,
    SwitchCase,
    TabularTranslator,
    TypeConversionSettings,
    Until,
    Wait,
    Web,
    expr,
)
from tests.helpers import assert_matches_snapshot


def test_empty_pipeline_snapshot() -> None:
    pipeline = Pipeline(name="Log")
    assert_matches_snapshot(pipeline, "empty_pipeline.json")


def test_sales_etl_history_full_load_snapshot() -> None:
    conn = expr.library_variable("Demo_ETL_Library_SourceDb")
    acquired = "activity('Guard_TryAcquireLock').output.resultSets[0].rows[0].Acquired"

    try_lock = Script(
        name="Guard_TryAcquireLock",
        database="JobControl",
        scripts=[
            ScriptBlock(
                text={
                    "value": (
                        "EXEC [dbo].[usp_TryAcquireJobLock]\n"
                        "  @ResourceName = N'Sales_ETL_History',\n"
                        f"  @RunId = N'{expr.interp(expr.run_id())}',\n"
                        f"  @PipelineName = N'{expr.interp(expr.pipeline_name())}',\n"
                        "  @LoadType = N'full',\n"
                        "  @LeaseMinutes = 720;"
                    ),
                    "type": "Expression",
                },
                type="Query",
            )
        ],
        script_block_execution_timeout="02:00:00",
        external_references=ExternalReferences(connection=conn),
    )

    wait = Wait(name="Wait_For_Lock", wait_time_in_seconds=60)
    if_lock = IfCondition(
        name="If_LockNotAcquired",
        expression=Expression(value=(f"@not(or(equals({acquired}, true),equals({acquired}, 1)))")),
        if_true_activities=[wait],
        if_false_activities=[],
    )
    try_lock.then(if_lock)

    until = Until(
        name="Until_TryAcquireLock",
        expression=Expression(value=f"@or(equals({acquired}, true),equals({acquired}, 1))"),
        timeout="02:00:00",
        activities=[try_lock, if_lock],
    )

    invoke_history = ExecutePipeline(
        name="Invoke_History_Full_Load",
        pipeline=PipelineReference(reference_name="11111111-1111-1111-1111-111111111111"),
        parameters={},
        wait_on_completion=True,
    )
    invoke_landing = ExecutePipeline(
        name="Invoke_Landing_Load",
        pipeline=PipelineReference(reference_name="22222222-2222-2222-2222-222222222222"),
        parameters={"full_load": 1},
        wait_on_completion=True,
    )
    invoke_staging = ExecutePipeline(
        name="Invoke_Staging_Load",
        pipeline=PipelineReference(reference_name="33333333-3333-3333-3333-333333333333"),
        parameters={"full_load": 1},
        wait_on_completion=True,
    )
    invoke_history.then(invoke_landing).then(invoke_staging)

    if_run = IfCondition(
        name="If_RunLoads",
        expression=Expression(value="@bool(true)"),
        if_true_activities=[invoke_history, invoke_landing, invoke_staging],
        if_false_activities=[],
    )
    until.then(if_run)

    release = Script(
        name="Guard_ReleaseLock",
        database="JobControl",
        scripts=[
            ScriptBlock(
                text={
                    "value": (
                        "EXEC [dbo].[usp_ReleaseJobLock]\n"
                        "  @ResourceName = N'Sales_ETL_History',\n"
                        f"  @RunId = N'{expr.interp(expr.run_id())}';"
                    ),
                    "type": "Expression",
                },
                type="NonQuery",
            )
        ],
        script_block_execution_timeout="02:00:00",
        external_references=ExternalReferences(connection=conn),
    )
    if_run.then(release, on="Completed")

    pipeline = Pipeline(
        name="Sales_ETL_History_Full_Load",
        activities=[until, if_run, release],
        library_variables={
            "Demo_ETL_Library_SourceDb": LibraryVariable(
                type="String",
                variable_name="SourceDb",
                library_name="Demo_ETL_Library",
            )
        },
        concurrency=1,
    )
    assert_matches_snapshot(pipeline, "sales_etl_history_full_load.json")


def test_landing_copy_subset_snapshot() -> None:
    cols = [
        "customer_id",
        "region",
        "segment",
        "updated_at",
    ]
    mappings = [
        ColumnMapping(
            source=ColumnRef(name=col, type="String", physical_type="nvarchar"),
            sink=ColumnRef(name=col, type="String", physical_type="nvarchar"),
        )
        for col in cols
    ]
    sql = (
        "SELECT\n"
        "   CAST([customer_id] AS NVARCHAR (12)) AS [customer_id]\n"
        "   , [region]\n"
        "   , [segment]\n"
        "   , [updated_at]\n"
        "FROM [dbo].[customers];"
    )

    truncate = Script(
        name="Truncate_customers",
        database="Landing",
        scripts=[
            ScriptBlock(
                text={"value": "TRUNCATE TABLE sales.customers", "type": "Expression"},
                type="Query",
            )
        ],
        script_block_execution_timeout="02:00:00",
        external_references=ExternalReferences(
            connection=expr.library_variable("Demo_ETL_Library_Landing")
        ),
    )
    copy = Copy(
        name="Copy_customers",
        source=SqlMISource(
            sql_reader_query=sql,
            partition_option="None",
            dataset_settings=AzureSqlMITable(
                database="SourceDb",
                connection=expr.library_variable("Demo_ETL_Library_SourceDb"),
            ),
        ),
        sink=SqlMISink(
            write_behavior="insert",
            sql_writer_use_table_lock=True,
            dataset_settings=AzureSqlMITable(
                database="Landing",
                schema_name="sales",
                table="customers",
                connection=expr.library_variable("Demo_ETL_Library_Landing"),
            ),
        ),
        enable_staging=False,
        translator=TabularTranslator(
            mappings=mappings,
            type_conversion=True,
            type_conversion_settings=TypeConversionSettings(
                allow_data_truncation=True,
                treat_boolean_as_number=False,
            ),
        ),
    )
    truncate.then(copy)

    pipeline = Pipeline(
        name="Landing_customers_subset",
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
    assert_matches_snapshot(pipeline, "landing_copy_subset.json")


def test_sql_script_refresh_snapshot() -> None:
    """Two Script activities that refresh aggregate tables."""
    conn = expr.library_variable("Demo_ETL_Library_SourceDb")
    fill_regions = Script(
        name="FillRegionsTable",
        database="SourceDb",
        scripts=[
            ScriptBlock(
                text={
                    "value": (
                        "BEGIN TRAN;\n"
                        "DELETE FROM [analytics].[region_totals];\n"
                        "INSERT INTO [analytics].[region_totals] ([region], [total])\n"
                        "SELECT [region], SUM([amount]) FROM [dbo].[orders] GROUP BY [region];\n"
                        "COMMIT;"
                    ),
                    "type": "Expression",
                },
                type="NonQuery",
            )
        ],
        script_block_execution_timeout="02:00:00",
        external_references=ExternalReferences(connection=conn),
    )
    fill_products = Script(
        name="FillProductsTable",
        database="SourceDb",
        scripts=[
            ScriptBlock(
                text={
                    "value": (
                        "BEGIN TRAN;\n"
                        "DELETE FROM [analytics].[product_totals];\n"
                        "INSERT INTO [analytics].[product_totals] "
                        "([product_id], [total])\n"
                        "SELECT [product_id], SUM([amount]) "
                        "FROM [dbo].[orders] GROUP BY [product_id];\n"
                        "COMMIT;"
                    ),
                    "type": "Expression",
                },
                type="NonQuery",
            )
        ],
        script_block_execution_timeout="02:00:00",
        external_references=ExternalReferences(connection=conn),
    )

    pipeline = Pipeline(
        name="Refresh_Aggregates",
        activities=[fill_regions, fill_products],
        library_variables={
            "Demo_ETL_Library_SourceDb": LibraryVariable(
                type="String",
                variable_name="SourceDb",
                library_name="Demo_ETL_Library",
            )
        },
        concurrency=1,
    )
    assert_matches_snapshot(pipeline, "sql_script_refresh.json")


def test_docs_multi_activity_snapshot() -> None:
    lh = LinkedService(
        name="LakehouseGitArtifactW1",
        properties=LinkedServiceProperties(
            type="Lakehouse",
            type_properties={
                "workspaceId": "00000000-0000-0000-0000-000000000001",
                "artifactId": "00000000-0000-0000-0000-000000000003",
                "rootFolder": "Tables",
            },
        ),
    )
    notebook = Notebook(
        name="Notebook1",
        notebook_id="00000000-0000-0000-0000-000000000002",
        workspace_id="00000000-0000-0000-0000-000000000001",
    )
    get_metadata = RawActivity(
        name="Get Metadata1",
        type="GetMetadata",
        type_properties={
            "fieldList": ["columnCount"],
            "datasetSettings": LakehouseTable(table="Lh1", linked_service=lh).model_dump(
                by_alias=True, exclude_none=True, mode="json"
            ),
        },
        policy=ActivityPolicy(),
    )
    lookup = Lookup(
        name="Lookup1",
        source=LakehouseTableSource(),
        dataset_settings=LakehouseTable(table="lh2", linked_service=lh),
    )
    pbi = RawActivity(
        name="PBISemanticModelRefresh1",
        type="PBISemanticModelRefresh",
        type_properties={
            "method": "POST",
            "groupId": "00000000-0000-0000-0000-000000000001",
            "datasetId": "00000000-0000-0000-0000-000000000004",
            "type": "Full",
            "commitMode": "transactional",
            "maxParallelism": 2,
            "retryCount": 1,
            "waitOnCompletion": True,
            "operationType": "RefreshDataset",
        },
        external_references=ExternalReferences(connection="00000000-0000-0000-0000-000000000005"),
        user_properties=[],
        policy=ActivityPolicy(timeout="7.00:00:00"),
    )
    pipeline = Pipeline(
        name="docs_example",
        description=(
            "Data pipeline with multiple activity types demonstrating different typeProperties"
        ),
        activities=[notebook, get_metadata, lookup, pbi],
    )
    assert_matches_snapshot(pipeline, "docs_multi_activity.json")


def test_control_flow_kitchen_sink_snapshot() -> None:
    refresh = Dataflow(
        name="refresh_one",
        dataflow_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        workspace_id="00000000-0000-0000-0000-000000000001",
    )
    loop = ForEach(
        name="for_each_table",
        items=Expression(value="@pipeline().parameters.tables"),
        is_sequential=True,
        activities=[refresh],
    )
    sp = StoredProcedure(
        name="run_merge",
        stored_procedure_name="dbo.usp_MergeSales",
        database="Warehouse",
        external_references=ExternalReferences(connection="11111111-2222-3333-4444-555555555555"),
    )
    fail = Fail(name="bad_mode", message="Unknown mode", error_code="BadMode")
    switch = Switch(
        name="by_mode",
        on=Expression(value="@pipeline().parameters.mode"),
        cases=[SwitchCase(value="full", activities=[sp])],
        default_activities=[fail],
    )
    loop.then(switch)

    pipeline = Pipeline(
        name="kitchen_sink",
        description=(
            "Kitchen-sink control flow covering ForEach, Switch, Fail, Dataflow, StoredProcedure"
        ),
        activities=[loop, switch],
        parameters={
            "tables": Parameter(type="Array", default_value=[]),
            "mode": Parameter(type="String", default_value="full"),
        },
    )
    assert_matches_snapshot(pipeline, "control_flow_kitchen_sink.json")


def test_web_get_snapshot() -> None:
    web = Web(
        name="Call_Orders_API",
        method="GET",
        relative_url="/orders?status=open",
        headers={"Accept": "application/json"},
        http_request_timeout="00:01:40",
        external_references=ExternalReferences(connection="00000000-0000-0000-0000-000000000005"),
    )
    pipeline = Pipeline(
        name="Web_Orders_Lookup",
        description="GET /orders from a Fabric Web connection.",
        activities=[web],
    )
    assert_matches_snapshot(pipeline, "web_get.json")
