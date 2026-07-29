"""Unit tests for activity chaining."""

from fabric_data_pipelines import Wait


def test_then_returns_downstream() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    b = Wait(name="b", wait_time_in_seconds=2)
    result = a.then(b)
    assert result is b
    assert len(b.depends_on) == 1
    assert b.depends_on[0].activity == "a"
    assert b.depends_on[0].dependency_conditions == ["Succeeded"]


def test_then_with_failed_condition() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    b = Wait(name="b", wait_time_in_seconds=2)
    a.then(b, on="Failed")
    assert b.depends_on[0].dependency_conditions == ["Failed"]


def test_then_chain() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    b = Wait(name="b", wait_time_in_seconds=2)
    c = Wait(name="c", wait_time_in_seconds=3)
    a.then(b).then(c)
    assert b.depends_on[0].activity == "a"
    assert c.depends_on[0].activity == "b"


def test_rshift_alias() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    b = Wait(name="b", wait_time_in_seconds=2)
    a >> b
    assert b.depends_on[0].activity == "a"


def test_after_fan_in() -> None:
    a = Wait(name="a", wait_time_in_seconds=1)
    b = Wait(name="b", wait_time_in_seconds=2)
    c = Wait(name="c", wait_time_in_seconds=3)
    c.after(a, b, on="Completed")
    assert {d.activity for d in c.depends_on} == {"a", "b"}
    assert all(d.dependency_conditions == ["Completed"] for d in c.depends_on)
