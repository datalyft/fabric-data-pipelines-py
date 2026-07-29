"""Unit tests for pipeline validation."""

import pytest

from fabric_data_pipelines import (
    CrossScopeDependencyError,
    CyclicDependencyError,
    DuplicateActivityNameError,
    IfCondition,
    Pipeline,
    UnknownDependencyError,
    Wait,
)


def test_duplicate_names_across_scopes() -> None:
    inner = Wait(name="pause", wait_time_in_seconds=1)
    outer = Wait(name="pause", wait_time_in_seconds=2)
    branch = IfCondition(
        name="branch",
        expression="@bool(true)",
        if_true_activities=[inner],
    )
    pipeline = Pipeline(name="dup", activities=[outer, branch])
    with pytest.raises(DuplicateActivityNameError, match="pause"):
        pipeline.validate_graph()


def test_unknown_dependency() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    a.depends_on = []
    b = Wait(name="b", wait_time_in_seconds=2)
    b.after(Wait(name="missing", wait_time_in_seconds=0))
    # Manually set a bad dependency name
    from fabric_data_pipelines import ActivityDependency

    b.depends_on = [ActivityDependency(activity="ghost")]
    pipeline = Pipeline(name="bad", activities=[a, b])
    with pytest.raises(UnknownDependencyError, match="ghost"):
        pipeline.validate_graph()


def test_cross_scope_dependency() -> None:
    outer = Wait(name="outer", wait_time_in_seconds=1)
    inner = Wait(name="inner", wait_time_in_seconds=2)
    outer.then(inner)
    branch = IfCondition(
        name="branch",
        expression="@bool(true)",
        if_true_activities=[inner],
    )
    pipeline = Pipeline(name="cross", activities=[outer, branch])
    with pytest.raises(CrossScopeDependencyError, match="inner"):
        pipeline.validate_graph()


def test_cycle_detection() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    b = Wait(name="b", wait_time_in_seconds=2)
    a.then(b)
    b.then(a)
    pipeline = Pipeline(name="cycle", activities=[a, b])
    with pytest.raises(CyclicDependencyError, match="a"):
        pipeline.validate_graph()


def test_valid_pipeline_passes() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    b = Wait(name="b", wait_time_in_seconds=2)
    a.then(b)
    pipeline = Pipeline(name="ok", activities=[a, b])
    pipeline.validate_graph()
