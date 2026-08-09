"""SetVariable and AppendVariable activities."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, model_validator

from fabric_data_pipelines.activities.base import Activity, SecureInputOutputPolicy
from fabric_data_pipelines.activities.checks import require_non_empty_str
from fabric_data_pipelines.errors import InvalidChoiceError

SYSTEM_VARIABLE_NAMES: tuple[str, ...] = ("PipelineReturnValue",)


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

    @model_validator(mode="after")
    def _validate_set_variable(self) -> SetVariable:
        require_non_empty_str(self.variable_name, field="variable_name")
        if self.set_system_variable is True and self.variable_name not in SYSTEM_VARIABLE_NAMES:
            raise InvalidChoiceError(
                field="variable",
                value=self.variable_name,
                valid=SYSTEM_VARIABLE_NAMES,
                context=" for set_system_variable=True",
            )
        return self


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

    @model_validator(mode="after")
    def _validate_append_variable(self) -> AppendVariable:
        require_non_empty_str(self.variable_name, field="variable_name")
        return self
