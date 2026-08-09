"""Base activity types, policies, dependencies, and chaining helpers."""

from __future__ import annotations

from typing import Any, ClassVar, Literal, TypeVar

from pydantic import Field, model_serializer, model_validator

from fabric_data_pipelines.activities.checks import require_non_empty_str
from fabric_data_pipelines.errors import PipelineValidationError
from fabric_data_pipelines.serialization import FabricModel, to_camel

DependencyCondition = Literal["Succeeded", "Failed", "Completed", "Skipped"]
ActivityState = Literal["Active", "InActive"]
OnInactiveMarkAs = Literal["Succeeded", "Failed", "Skipped"]

A = TypeVar("A", bound="Activity")

# Envelope fields that live on the activity root, not inside typeProperties.
_ENVELOPE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "type",
        "depends_on",
        "policy",
        "external_references",
        "state",
        "on_inactive_mark_as",
        "description",
        "user_properties",
        "type_properties",
    }
)


class ActivityDependency(FabricModel):
    """A single entry in an activity's ``dependsOn`` array.

    Example::

        ActivityDependency(activity="lookup", dependency_conditions=["Succeeded"])
    """

    activity: str
    dependency_conditions: list[DependencyCondition] = Field(default=["Succeeded"])


class ActivityPolicy(FabricModel):
    """Execution policy matching Fabric UI defaults.

    Defaults mirror what the Fabric UI writes into exported JSON so generated
    pipelines round-trip without noisy diffs.

    Example::

        ActivityPolicy()  # timeout 0.12:00:00, retry 0, ...
        ActivityPolicy(timeout="1.00:00:00", retry=3)
    """

    timeout: str | None = "0.12:00:00"
    retry: int | None = 0
    retry_interval_in_seconds: int | None = 30
    secure_output: bool | None = False
    secure_input: bool | None = False


class SecureInputOutputPolicy(FabricModel):
    """Minimal policy used by ExecutePipeline and SetVariable activities."""

    secure_input: bool | None = False
    secure_output: bool | None = None


class ExternalReferences(FabricModel):
    """Reference to a Fabric connection.

    ``connection`` may be a GUID or an expression such as
    ``@pipeline().libraryVariables.MyConnection``.

    Example::

        ExternalReferences(connection="00000000-0000-0000-0000-000000000005")
        ExternalReferences(connection=expr.library_variable("MyConn"))
    """

    connection: str


class Activity(FabricModel):
    """Base class for all Fabric pipeline activities.

    Subclasses declare a class-level ``activity_type`` and any fields that
    belong in ``typeProperties``. Serialization automatically splits envelope
    fields (``name``, ``dependsOn``, ``policy``, …) from type-specific fields.

    Example::

        from fabric_data_pipelines import Wait

        wait = Wait(name="pause", wait_time_in_seconds=30)
        wait.to_dict()
    """

    activity_type: ClassVar[str] = ""

    # Fields declared on subclasses that should NOT go into typeProperties
    # (e.g. RawActivity.type is the activity type discriminator).
    _exclude_from_type_properties: ClassVar[frozenset[str]] = frozenset()

    name: str
    depends_on: list[ActivityDependency] = Field(default_factory=list)
    policy: ActivityPolicy | SecureInputOutputPolicy | dict[str, Any] | None = None
    external_references: ExternalReferences | None = None
    state: ActivityState | None = None
    on_inactive_mark_as: OnInactiveMarkAs | None = None
    description: str | None = None
    user_properties: list[Any] | None = None

    @model_validator(mode="after")
    def _validate_activity(self) -> Activity:
        require_non_empty_str(self.name, field="name")
        for dep in self.depends_on:
            require_non_empty_str(dep.activity, field="depends_on.activity")
            if not dep.dependency_conditions:
                raise PipelineValidationError(
                    f"Activity '{self.name}' has a dependsOn entry with empty dependencyConditions"
                )
        if self.state == "InActive" and self.on_inactive_mark_as is None:
            raise PipelineValidationError(
                f"Activity '{self.name}' has state 'InActive' but on_inactive_mark_as is not set"
            )
        if isinstance(self.policy, ActivityPolicy):
            if self.policy.retry is not None and self.policy.retry < 0:
                raise PipelineValidationError(f"Activity '{self.name}' policy.retry must be >= 0")
            if (
                self.policy.retry_interval_in_seconds is not None
                and self.policy.retry_interval_in_seconds < 0
            ):
                raise PipelineValidationError(
                    f"Activity '{self.name}' policy.retry_interval_in_seconds must be >= 0"
                )
        if self.external_references is not None:
            require_non_empty_str(
                self.external_references.connection,
                field="external_references.connection",
            )
        return self

    def then(self, activity: A, on: DependencyCondition = "Succeeded") -> A:
        """Chain ``activity`` to run after this one.

        Returns ``activity`` so further chaining is possible::

            lookup.then(copy).then(notebook)

        Args:
            activity: The downstream activity.
            on: Dependency condition. One of ``Succeeded`` (default),
                ``Failed``, ``Completed``, ``Skipped``.
        """
        activity.depends_on.append(
            ActivityDependency(activity=self.name, dependency_conditions=[on])
        )
        return activity

    def after(self: A, *activities: Activity, on: DependencyCondition = "Succeeded") -> A:
        """Make this activity depend on one or more upstream activities (fan-in).

        Example::

            join.after(copy_a, copy_b)
        """
        for upstream in activities:
            self.depends_on.append(
                ActivityDependency(activity=upstream.name, dependency_conditions=[on])
            )
        return self

    def __rshift__(self, other: A) -> A:
        """Sugar for :meth:`then`: ``lookup >> copy``."""
        return self.then(other)

    def to_dict(self) -> dict[str, Any]:
        """Serialize this activity to a Fabric-compatible dict."""
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")

    def _resolve_activity_type(self) -> str:
        # RawActivity (and similar) store the Fabric type on an instance field.
        if "type" in type(self).model_fields:
            dynamic = getattr(self, "type", None)
            if isinstance(dynamic, str) and dynamic:
                return dynamic
        return self.activity_type

    @model_serializer(mode="wrap")
    def _serialize_activity(self, handler: Any) -> dict[str, Any]:
        # Touch handler so Pydantic still runs field serializers for nested models
        # when needed; we rebuild the envelope ourselves for a stable shape.
        _ = handler

        envelope: dict[str, Any] = {
            "name": self.name,
            "type": self._resolve_activity_type(),
            "dependsOn": [
                dep.model_dump(by_alias=True, exclude_none=True, mode="json")
                for dep in self.depends_on
            ],
        }

        if self.policy is not None:
            if isinstance(self.policy, FabricModel):
                envelope["policy"] = self.policy.model_dump(
                    by_alias=True, exclude_none=True, mode="json"
                )
            else:
                envelope["policy"] = self.policy

        if self.external_references is not None:
            envelope["externalReferences"] = self.external_references.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            )

        if self.state is not None:
            envelope["state"] = self.state
        if self.on_inactive_mark_as is not None:
            envelope["onInactiveMarkAs"] = self.on_inactive_mark_as
        if self.description is not None:
            envelope["description"] = self.description
        if self.user_properties is not None:
            envelope["userProperties"] = self.user_properties

        # RawActivity: free-form type_properties dict.
        raw_tp = getattr(self, "type_properties", None)
        if isinstance(raw_tp, dict) and "type_properties" in type(self).model_fields:
            if raw_tp:
                envelope["typeProperties"] = _serialize_value(raw_tp)
            return envelope

        type_properties: dict[str, Any] = {}
        exclude = _ENVELOPE_FIELDS | self._exclude_from_type_properties
        for field_name in type(self).model_fields:
            if field_name in exclude:
                continue
            value = getattr(self, field_name)
            if value is None:
                continue
            key = to_camel(field_name)
            type_properties[key] = _serialize_value(value)

        if type_properties:
            envelope["typeProperties"] = type_properties

        return envelope


def _serialize_value(value: Any) -> Any:
    if isinstance(value, FabricModel):
        return value.model_dump(by_alias=True, exclude_none=True, mode="json")
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def default_policy() -> ActivityPolicy:
    """Return a fresh :class:`ActivityPolicy` with Fabric UI defaults."""
    return ActivityPolicy()
