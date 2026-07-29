"""SetVariable and AppendVariable activities."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from fabric_data_pipelines.activities.base import Activity, SecureInputOutputPolicy


class SetVariable(Activity):
    """Set the value of a pipeline variable.

    Example::

        from fabric_data_pipelines import SetVariable, expr

        set_var = SetVariable(
            name="Set row_count",
            variable_name="row_count",
            value=expr.activity_output("lookup", "count"),
        )
    """

    activity_type: ClassVar[str] = "SetVariable"

    variable_name: str
    value: Any
    set_system_variable: bool | None = None

    policy: SecureInputOutputPolicy | None = Field(
        default_factory=lambda: SecureInputOutputPolicy(secure_input=False)
    )


class AppendVariable(Activity):
    """Append a value to an array pipeline variable.

    Example::

        from fabric_data_pipelines import AppendVariable

        append = AppendVariable(
            name="collect_id",
            variable_name="ids",
            value="@item().id",
        )
    """

    activity_type: ClassVar[str] = "AppendVariable"

    variable_name: str
    value: Any
