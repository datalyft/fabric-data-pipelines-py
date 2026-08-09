"""Unit tests for construction-time activity validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fabric_data_pipelines import (
    ActivityDependency,
    ActivityPolicy,
    AppendVariable,
    AzureSqlMITable,
    AzureSqlTable,
    Copy,
    CopySource,
    Dataflow,
    Dataset,
    ExecutePipeline,
    ExternalReferences,
    Fail,
    ForEach,
    IfCondition,
    InvalidChoiceError,
    LakehouseTable,
    LakehouseTableSink,
    LakehouseTableSource,
    Lookup,
    Notebook,
    PipelineReference,
    PipelineValidationError,
    RawActivity,
    Script,
    ScriptBlock,
    SetVariable,
    SqlMISink,
    SqlMISource,
    StagingSettings,
    StoredProcedure,
    Switch,
    SwitchCase,
    Until,
    Wait,
    Web,
)


def test_activity_empty_name_rejected() -> None:
    with pytest.raises(ValidationError):
        Wait(name="   ", wait_time_in_seconds=1)


def test_inactive_requires_on_inactive_mark_as() -> None:
    with pytest.raises(ValidationError, match="on_inactive_mark_as"):
        Wait(name="paused", wait_time_in_seconds=1, state="InActive")


def test_inactive_with_mark_as_ok() -> None:
    Wait(
        name="paused",
        wait_time_in_seconds=1,
        state="InActive",
        on_inactive_mark_as="Succeeded",
    )


def test_empty_dependency_conditions_rejected() -> None:
    with pytest.raises(ValidationError, match="dependencyConditions"):
        Wait(
            name="w",
            wait_time_in_seconds=1,
            depends_on=[ActivityDependency(activity="upstream", dependency_conditions=[])],
        )


def test_negative_policy_retry_rejected() -> None:
    with pytest.raises(ValidationError, match="retry"):
        Notebook(
            name="nb",
            notebook_id="n1",
            workspace_id="w1",
            policy=ActivityPolicy(retry=-1),
        )


def test_wait_negative_seconds_rejected() -> None:
    with pytest.raises(ValidationError, match="wait_time_in_seconds"):
        Wait(name="w", wait_time_in_seconds=-1)


def test_fail_empty_message_rejected() -> None:
    with pytest.raises(ValidationError, match="message"):
        Fail(name="f", message="  ", error_code="1")


def test_foreach_empty_activities_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty activities"):
        ForEach(name="loop", items="@pipeline().parameters.tables", activities=[])


def test_foreach_ok() -> None:
    ForEach(
        name="loop",
        items="@pipeline().parameters.tables",
        activities=[Wait(name="step", wait_time_in_seconds=1)],
    )


def test_switch_requires_case_or_default() -> None:
    with pytest.raises(ValidationError, match="at least one case"):
        Switch(name="sw", on="@pipeline().parameters.mode")


def test_switch_duplicate_case_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate case"):
        Switch(
            name="sw",
            on="@pipeline().parameters.mode",
            cases=[
                SwitchCase(value="a", activities=[]),
                SwitchCase(value="a", activities=[]),
            ],
        )


def test_until_empty_activities_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty activities"):
        Until(name="u", expression="@bool(true)", activities=[])


def test_if_empty_expression_rejected() -> None:
    with pytest.raises(ValidationError, match="expression"):
        IfCondition(name="branch", expression="   ")


def test_copy_requires_sink() -> None:
    with pytest.raises(ValidationError, match="sink or destination"):
        Copy(
            name="c",
            source=SqlMISource(
                dataset_settings=AzureSqlMITable(
                    database="db",
                    connection="conn",
                )
            ),
        )


def test_copy_staging_requires_settings() -> None:
    with pytest.raises(ValidationError, match="staging_settings"):
        Copy(
            name="c",
            source=SqlMISource(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
            sink=SqlMISink(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
            enable_staging=True,
        )


def test_copy_mismatched_dataset_lists_valid_choices() -> None:
    # Pydantic wraps ValueError subclasses as ValidationError; message still lists choices.
    with pytest.raises(ValidationError, match="AzureSqlMITable") as exc_info:
        Copy(
            name="c",
            source=SqlMISource(dataset_settings=LakehouseTable(table="t")),
            sink=SqlMISink(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
        )
    message = str(exc_info.value)
    assert "LakehouseTable" in message
    assert "`AzureSqlMITable`" in message
    assert "`AzureSqlTable`" in message
    assert "Valid datasets:" in message


def test_copy_unknown_connector_skips_pairing() -> None:
    Copy(
        name="c",
        source=CopySource(
            type="CustomBlobSource",
            dataset_settings=Dataset(type="CustomBlob", type_properties={}),
        ),
        sink=SqlMISink(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
    )


def test_copy_cross_connector_with_matching_datasets_ok() -> None:
    Copy(
        name="c",
        source=SqlMISource(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
        sink=LakehouseTableSink(dataset_settings=LakehouseTable(table="t")),
        enable_staging=False,
    )


def test_copy_sql_dataset_variants_ok() -> None:
    Copy(
        name="c",
        source=SqlMISource(dataset_settings=AzureSqlTable(database="db", connection="conn")),
        sink=SqlMISink(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
    )


def test_lookup_mismatched_dataset() -> None:
    with pytest.raises(ValidationError, match="LakehouseTable"):
        Lookup(
            name="l",
            source=SqlMISource(),
            dataset_settings=LakehouseTable(table="t"),
        )


def test_lookup_ok() -> None:
    Lookup(
        name="l",
        source=LakehouseTableSource(),
        dataset_settings=LakehouseTable(table="t"),
    )


def test_raw_activity_empty_type_rejected() -> None:
    with pytest.raises(ValidationError, match="type"):
        RawActivity(name="r", type="  ", type_properties={"a": 1})


def test_raw_activity_arbitrary_type_properties_ok() -> None:
    RawActivity(name="r", type="GetMetadata", type_properties={"fieldList": ["exists"]})


def test_notebook_empty_id_rejected() -> None:
    with pytest.raises(ValidationError, match="notebook_id"):
        Notebook(name="n", notebook_id="", workspace_id="w")


def test_dataflow_empty_id_rejected() -> None:
    with pytest.raises(ValidationError, match="dataflow_id"):
        Dataflow(name="d", dataflow_id="  ", workspace_id="w")


def test_script_requires_connection() -> None:
    with pytest.raises(ValidationError, match="external_references"):
        Script(name="s", scripts=[ScriptBlock(text="SELECT 1")])


def test_script_empty_scripts_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty scripts"):
        Script(
            name="s",
            scripts=[],
            external_references=ExternalReferences(connection="c"),
        )


def test_script_ok() -> None:
    Script(
        name="s",
        scripts=[ScriptBlock(text="SELECT 1")],
        external_references=ExternalReferences(connection="c"),
    )


def test_web_get_with_body_rejected() -> None:
    with pytest.raises(ValidationError, match="must not set body"):
        Web(
            name="w",
            method="GET",
            relative_url="/x",
            body="nope",
            external_references=ExternalReferences(connection="c"),
        )


def test_web_post_requires_body() -> None:
    with pytest.raises(ValidationError, match="requires body"):
        Web(
            name="w",
            method="POST",
            relative_url="/x",
            external_references=ExternalReferences(connection="c"),
        )


def test_set_variable_system_allowlist() -> None:
    with pytest.raises(ValidationError, match="PipelineReturnValue") as exc_info:
        SetVariable(
            name="s",
            variable_name="NotASystemVar",
            value=1,
            set_system_variable=True,
        )
    message = str(exc_info.value)
    assert "`PipelineReturnValue`" in message
    assert "Valid variables:" in message


def test_set_variable_system_ok() -> None:
    SetVariable(
        name="s",
        variable_name="PipelineReturnValue",
        value={"ok": True},
        set_system_variable=True,
    )


def test_append_variable_empty_name_rejected() -> None:
    with pytest.raises(ValidationError, match="variable_name"):
        AppendVariable(name="a", variable_name="", value=1)


def test_stored_procedure_requires_connection() -> None:
    with pytest.raises(ValidationError, match="external_references"):
        StoredProcedure(name="sp", stored_procedure_name="dbo.usp_X")


def test_stored_procedure_ok() -> None:
    StoredProcedure(
        name="sp",
        stored_procedure_name="dbo.usp_X",
        external_references=ExternalReferences(connection="c"),
    )


def test_execute_pipeline_empty_reference_rejected() -> None:
    with pytest.raises(ValidationError, match="reference_name"):
        ExecutePipeline(
            name="e",
            pipeline=PipelineReference(reference_name="  "),
        )


def test_execute_pipeline_ok() -> None:
    ExecutePipeline(
        name="e",
        pipeline=PipelineReference(reference_name="other_pipe"),
    )


def test_copy_staging_ok() -> None:
    Copy(
        name="c",
        source=SqlMISource(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
        sink=SqlMISink(dataset_settings=AzureSqlMITable(database="db", connection="conn")),
        enable_staging=True,
        staging_settings=StagingSettings(
            external_references=ExternalReferences(connection="stage")
        ),
    )


def test_invalid_choice_error_message_shape() -> None:
    err = InvalidChoiceError(
        field="dataset",
        value="LakehouseTable",
        valid=("AzureSqlMITable", "AzureSqlTable"),
        context=" for source 'SqlMISource'",
    )
    assert isinstance(err, PipelineValidationError)
    assert err.field == "dataset"
    assert err.valid == ("AzureSqlMITable", "AzureSqlTable")
    assert str(err) == (
        "Unknown dataset 'LakehouseTable' for source 'SqlMISource'. "
        "Valid datasets: `AzureSqlMITable`, `AzureSqlTable`."
    )
