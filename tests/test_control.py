"""Unit tests for control-flow activities."""

from fabric_data_pipelines import (
    Expression,
    Fail,
    ForEach,
    IfCondition,
    Pipeline,
    Switch,
    SwitchCase,
    Until,
    Wait,
    expr,
)


def test_wait_has_no_policy() -> None:
    wait = Wait(name="pause", wait_time_in_seconds=60)
    data = wait.to_dict()
    assert "policy" not in data
    assert data["typeProperties"]["waitTimeInSeconds"] == 60


def test_if_condition_nested() -> None:
    wait = Wait(name="inner", wait_time_in_seconds=1)
    branch = IfCondition(
        name="branch",
        expression=expr.bool_(True),
        if_true_activities=[wait],
        if_false_activities=[],
    )
    data = branch.to_dict()
    assert data["typeProperties"]["expression"] == {
        "value": "@bool(true)",
        "type": "Expression",
    }
    assert data["typeProperties"]["ifTrueActivities"][0]["name"] == "inner"
    assert data["typeProperties"]["ifFalseActivities"] == []


def test_foreach_and_switch() -> None:
    fail = Fail(name="bad", message="nope", error_code="1")
    loop = ForEach(
        name="loop",
        items=Expression(value=expr.parameter("items")),
        activities=[Wait(name="step", wait_time_in_seconds=1)],
        is_sequential=True,
    )
    switch = Switch(
        name="sw",
        on=expr.parameter("mode"),
        cases=[SwitchCase(value="x", activities=[Wait(name="case_x", wait_time_in_seconds=1)])],
        default_activities=[fail],
    )
    loop.then(switch)
    pipeline = Pipeline(name="ctrl", activities=[loop, switch])
    props = pipeline.to_dict()["properties"]
    assert props["activities"][0]["type"] == "ForEach"
    assert props["activities"][1]["type"] == "Switch"


def test_until() -> None:
    until = Until(
        name="until",
        expression="@bool(true)",
        timeout="01:00:00",
        activities=[Wait(name="tick", wait_time_in_seconds=5)],
    )
    data = until.to_dict()
    assert data["typeProperties"]["timeout"] == "01:00:00"
    assert data["typeProperties"]["activities"][0]["name"] == "tick"
