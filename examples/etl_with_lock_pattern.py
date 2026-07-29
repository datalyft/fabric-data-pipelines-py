"""ETL lock orchestrator — acquire, retry, run child, release.

Scenario: a concurrency-1 parent pipeline guards a sales history full load.
It retries lock acquisition until success, invokes the child load pipeline,
and always releases the lock when the invoke branch completes.
"""

from fabric_data_pipelines import (
    ExecutePipeline,
    Expression,
    ExternalReferences,
    IfCondition,
    LibraryVariable,
    Pipeline,
    PipelineReference,
    Script,
    ScriptBlock,
    Until,
    Wait,
    expr,
)

CONN = expr.library_variable("Demo_ETL_Library_SourceDb")
ACQUIRED = "activity('Guard_TryAcquireLock').output.resultSets[0].rows[0].Acquired"
RESOURCE = "Sales_ETL_History"

try_lock = Script(
    name="Guard_TryAcquireLock",
    database="JobControl",
    scripts=[
        ScriptBlock(
            text={
                "value": (
                    "EXEC [dbo].[usp_TryAcquireJobLock]\n"
                    f"  @ResourceName = N'{RESOURCE}',\n"
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
    external_references=ExternalReferences(connection=CONN),
)

if_lock = IfCondition(
    name="If_LockNotAcquired",
    expression=Expression(value=f"@not(or(equals({ACQUIRED}, true),equals({ACQUIRED}, 1)))"),
    if_true_activities=[Wait(name="Wait_For_Lock", wait_time_in_seconds=60)],
    if_false_activities=[],
)
try_lock.then(if_lock)

until = Until(
    name="Until_TryAcquireLock",
    expression=Expression(value=f"@or(equals({ACQUIRED}, true),equals({ACQUIRED}, 1))"),
    timeout="02:00:00",
    activities=[try_lock, if_lock],
)

invoke = ExecutePipeline(
    name="Invoke_History_Full_Load",
    pipeline=PipelineReference(reference_name="11111111-1111-1111-1111-111111111111"),
    parameters={},
    wait_on_completion=True,
)

if_run = IfCondition(
    name="If_RunLoads",
    expression=Expression(value="@bool(true)"),
    if_true_activities=[invoke],
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
                    f"  @ResourceName = N'{RESOURCE}',\n"
                    f"  @RunId = N'{expr.interp(expr.run_id())}';"
                ),
                "type": "Expression",
            },
            type="NonQuery",
        )
    ],
    script_block_execution_timeout="02:00:00",
    external_references=ExternalReferences(connection=CONN),
)
if_run.then(release, on="Completed")

pipeline = Pipeline(
    name="Sales_ETL_History_Full_Load",
    description=(
        "Acquire an ETL execution lock with retry, run the history full-load child, "
        "then release the lock."
    ),
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

if __name__ == "__main__":
    print(pipeline.to_json())
