"""Web (HTTP) activity."""

from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import Field, model_validator

from fabric_data_pipelines.activities.base import Activity, ActivityPolicy, ExternalReferences
from fabric_data_pipelines.activities.checks import require_non_empty_str
from fabric_data_pipelines.errors import PipelineValidationError

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
_METHODS_REQUIRING_BODY: frozenset[str] = frozenset({"POST", "PUT", "PATCH"})
_METHODS_FORBIDDING_BODY: frozenset[str] = frozenset({"GET", "DELETE"})


class Web(Activity):
    """Call a REST endpoint via a Fabric connection.

    Serializes as Fabric activity type ``WebActivity``. The connection supplies
    the base URL; ``relative_url`` is the path (and query) appended to it.

    Example::

        from fabric_data_pipelines import Web, ExternalReferences

        web = Web(
            name="Call_Orders_API",
            method="GET",
            relative_url="/orders?status=open",
            headers={"Accept": "application/json"},
            http_request_timeout="00:01:40",
            external_references=ExternalReferences(
                connection="00000000-0000-0000-0000-000000000005"
            ),
        )
    """

    activity_type: ClassVar[str] = "WebActivity"

    relative_url: str
    method: HttpMethod
    headers: dict[str, Any] | str | None = None
    body: str | dict[str, Any] | None = None
    disable_cert_validation: bool | None = None
    http_request_timeout: str | None = None
    turn_off_async: bool | None = None

    external_references: ExternalReferences
    policy: ActivityPolicy | None = Field(default_factory=ActivityPolicy)

    @model_validator(mode="after")
    def _validate_web(self) -> Web:
        require_non_empty_str(self.relative_url, field="relative_url")
        require_non_empty_str(
            self.external_references.connection,
            field="external_references.connection",
        )
        if self.method in _METHODS_REQUIRING_BODY and self.body is None:
            raise PipelineValidationError(
                f"Web activity '{self.name}' method '{self.method}' requires body"
            )
        if self.method in _METHODS_FORBIDDING_BODY and self.body is not None:
            raise PipelineValidationError(
                f"Web activity '{self.name}' method '{self.method}' must not set body"
            )
        return self
