"""Control-flow activities: IfCondition, ForEach, Switch, Until, Wait, Fail."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, field_validator

from fabric_data_pipelines.activities.base import Activity
from fabric_data_pipelines.serialization import Expression, FabricModel


def _coerce_expression(value: Any) -> Any:
    if isinstance(value, str):
        return Expression(value=value)
    return value


class IfCondition(Activity):
    """Execute activities based on a boolean expression.

    Nested activities are passed via ``if_true_activities`` /
    ``if_false_activities``. Dependencies among nested activities are scoped
    to that branch.

    Example::

        from fabric_data_pipelines import IfCondition, Wait, Expression, expr

        branch = IfCondition(
            name="If_LockNotAcquired",
            expression=Expression(value=expr.not_(expr.equals(...))),
            if_true_activities=[Wait(name="Wait_For_Lock", wait_time_in_seconds=60)],
            if_false_activities=[],
        )
    """

    activity_type: ClassVar[str] = "IfCondition"

    expression: Expression | dict[str, Any] | str
    if_true_activities: list[Activity] = Field(default_factory=list)
    if_false_activities: list[Activity] = Field(default_factory=list)

    @field_validator("expression", mode="before")
    @classmethod
    def _expression(cls, value: Any) -> Any:
        return _coerce_expression(value)


class ForEach(Activity):
    """Iterate over a collection and run nested activities for each item.

    Example::

        from fabric_data_pipelines import ForEach, Copy, Expression, expr

        loop = ForEach(
            name="for_each_table",
            items=Expression(value=expr.activity_output("get_tables", "value")),
            activities=[Copy(name="copy_one", source=..., sink=...)],
            is_sequential=True,
        )
    """

    activity_type: ClassVar[str] = "ForEach"

    items: Expression | dict[str, Any] | str
    activities: list[Activity]
    is_sequential: bool | None = None
    batch_count: int | None = None

    @field_validator("items", mode="before")
    @classmethod
    def _items(cls, value: Any) -> Any:
        return _coerce_expression(value)


class SwitchCase(FabricModel):
    """A single case branch inside a Switch activity.

    Example::

        SwitchCase(value="full", activities=[...])
    """

    value: str
    activities: list[Activity]


class Switch(Activity):
    """Execute different activity lists based on an expression value.

    Example::

        from fabric_data_pipelines import Switch, SwitchCase, Expression, Fail

        switch = Switch(
            name="by_mode",
            on=Expression(value=expr.parameter("mode")),
            cases=[
                SwitchCase(value="full", activities=[...]),
                SwitchCase(value="partial", activities=[...]),
            ],
            default_activities=[Fail(name="bad_mode", message="unknown", error_code="1")],
        )
    """

    activity_type: ClassVar[str] = "Switch"

    on: Expression | dict[str, Any] | str
    cases: list[SwitchCase] = Field(default_factory=list)
    default_activities: list[Activity] = Field(default_factory=list)

    @field_validator("on", mode="before")
    @classmethod
    def _on(cls, value: Any) -> Any:
        return _coerce_expression(value)


class Until(Activity):
    """Repeat nested activities until an expression evaluates to true.

    Example::

        from fabric_data_pipelines import Until, Script, Expression

        until = Until(
            name="Until_TryAcquireLock",
            expression=Expression(value="@equals(...)"),
            timeout="02:00:00",
            activities=[script, if_condition],
        )
    """

    activity_type: ClassVar[str] = "Until"

    expression: Expression | dict[str, Any] | str
    activities: list[Activity]
    timeout: str | None = None

    @field_validator("expression", mode="before")
    @classmethod
    def _expression(cls, value: Any) -> Any:
        return _coerce_expression(value)


class Wait(Activity):
    """Pause pipeline execution for a number of seconds.

    Wait activities do not carry a ``policy`` block in Fabric UI exports.

    Example::

        from fabric_data_pipelines import Wait

        Wait(name="Wait_For_Lock", wait_time_in_seconds=60)
    """

    activity_type: ClassVar[str] = "Wait"

    wait_time_in_seconds: int


class Fail(Activity):
    """Explicitly fail the pipeline with a message and error code.

    Example::

        from fabric_data_pipelines import Fail

        Fail(name="abort", message="Lock not acquired", error_code="LockTimeout")
    """

    activity_type: ClassVar[str] = "Fail"

    message: str
    error_code: str
