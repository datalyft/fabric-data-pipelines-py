"""Shared serialization helpers for Fabric pipeline JSON."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def to_camel(snake: str) -> str:
    """Convert ``snake_case`` to ``camelCase``.

    >>> to_camel("wait_time_in_seconds")
    'waitTimeInSeconds'
    """
    parts = snake.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class FabricModel(BaseModel):
    """Base model that serializes fields as camelCase Fabric JSON keys."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="forbid",
        arbitrary_types_allowed=True,
    )


class Expression(FabricModel):
    """A Fabric expression object ``{"value": "...", "type": "Expression"}``.

    Strings that look like Fabric expressions (start with ``@``) or any
    :class:`~fabric_data_pipelines.expressions.Expr` may be passed wherever an
    ``Expression`` is expected and will be coerced automatically.

    Example::

        from fabric_data_pipelines import Expression, expr

        Expression(value="@pipeline().parameters.run_date")
        Expression.model_validate(expr.parameter("run_date"))
    """

    value: str
    type: str = Field(default="Expression")

    @model_validator(mode="before")
    @classmethod
    def _coerce_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"value": data, "type": "Expression"}
        return data


def dump_json(obj: Any, *, indent: int | None = 2) -> str:
    """Serialize a Fabric model (or nested dict/list) to JSON text.

    Args:
        obj: A :class:`FabricModel`, dict, list, or JSON-serializable value.
        indent: Indentation passed to :func:`json.dumps`. Use ``None`` for
            compact output.

    Returns:
        A JSON string.
    """
    if isinstance(obj, BaseModel):
        data = obj.model_dump(by_alias=True, exclude_none=True, mode="json")
    else:
        data = obj
    return json.dumps(data, indent=indent, ensure_ascii=False)
