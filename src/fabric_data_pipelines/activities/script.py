"""Script activity."""

from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import Field, field_validator, model_serializer, model_validator

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy
from fabric_data_pipelines.activities.checks import require_expression_value
from fabric_data_pipelines.errors import PipelineValidationError
from fabric_data_pipelines.serialization import Expression, FabricModel

ScriptBlockType = Literal["Query", "NonQuery"]


class ScriptBlock(FabricModel):
    """A single script block inside a Script activity.

    Fabric stores script text as an Expression object when dynamic content is
    used, or as a plain string. This class accepts either.

    Example::

        ScriptBlock(text="SELECT 1", type="Query")
        ScriptBlock(
            text={
                "value": "EXEC usp_Lock @RunId = N'@{pipeline().RunId}';",
                "type": "Expression",
            },
            type="Query",
        )
    """

    text: Expression | str | dict[str, Any]
    type: ScriptBlockType = "Query"

    @field_validator("text", mode="before")
    @classmethod
    def _coerce_text(cls, value: Any) -> Any:
        if isinstance(value, dict) and "value" in value:
            return value
        return value

    @model_serializer(mode="wrap")
    def _serialize(self, handler: Any) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        text = self.text
        if isinstance(text, Expression):
            data["text"] = text.model_dump(by_alias=True, exclude_none=True, mode="json")
        elif isinstance(text, dict):
            data["text"] = text
        else:
            data["text"] = text
        data["type"] = self.type
        return data


class Script(Activity):
    """Execute one or more SQL (or other) scripts against a database.

    Example::

        from fabric_data_pipelines import Script, ScriptBlock, ExternalReferences, expr

        script = Script(
            name="Guard_TryAcquireLock",
            database="JobControl",
            scripts=[
                ScriptBlock(
                    text={
                        "value": (
                            "EXEC [dbo].[usp_TryAcquireJobLock]\\n"
                            f"  @RunId = N'{expr.interp(expr.run_id())}';"
                        ),
                        "type": "Expression",
                    },
                    type="Query",
                )
            ],
            script_block_execution_timeout="02:00:00",
            external_references=ExternalReferences(
                connection=expr.library_variable("Demo_ETL_Library_SourceDb")
            ),
        )
    """

    activity_type: ClassVar[str] = "Script"

    database: str | dict[str, Any] | None = None
    scripts: list[ScriptBlock] | list[dict[str, Any]]
    log_settings: dict[str, Any] | None = None
    script_block_execution_timeout: str | None = None
    connection_version: str | None = None

    policy: ActivityPolicy | None = Field(default_factory=ActivityPolicy)

    @model_validator(mode="after")
    def _validate_script(self) -> Script:
        if not self.scripts:
            raise PipelineValidationError(
                f"Script activity '{self.name}' requires a non-empty scripts list"
            )
        for i, block in enumerate(self.scripts):
            if isinstance(block, ScriptBlock):
                require_expression_value(block.text, field=f"scripts[{i}].text")
            elif isinstance(block, dict):
                require_expression_value(block.get("text"), field=f"scripts[{i}].text")
            else:
                raise PipelineValidationError(
                    f"Script activity '{self.name}' scripts[{i}] must be a ScriptBlock or dict"
                )
        if self.external_references is None or not self.external_references.connection.strip():
            raise PipelineValidationError(
                f"Script activity '{self.name}' requires external_references.connection"
            )
        return self
