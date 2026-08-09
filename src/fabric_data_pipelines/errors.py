"""Validation and import errors raised when building a Fabric pipeline."""

from __future__ import annotations

from collections.abc import Sequence


class PipelineValidationError(ValueError):
    """Base class for pipeline validation failures."""


class DuplicateActivityNameError(PipelineValidationError):
    """Raised when two activities share the same name.

    Example message::

        Duplicate activity name 'copy_table'. Activity names must be unique
        across the entire pipeline (including nested scopes).
    """


class CyclicDependencyError(PipelineValidationError):
    """Raised when activity dependencies form a cycle.

    Example message::

        Cyclic dependency detected: a -> b -> a.
    """


class UnknownDependencyError(PipelineValidationError):
    """Raised when an activity depends on a name that does not exist.

    Example message::

        Activity 'copy_table' depends on unknown activity 'missing'.
    """


class CrossScopeDependencyError(PipelineValidationError):
    """Raised when an activity depends on a name from a different scope.

    Fabric resolves ``dependsOn`` only within the same activity list (top-level
    or a single nested ``activities`` / ``ifTrueActivities`` block). Cross-scope
    references are accepted by the UI but fail at runtime.

    Example message::

        Activity 'inner_copy' depends on 'outer_lookup' which exists in a
        different scope. Dependencies must target activities in the same scope.
    """


class ScheduleValidationError(PipelineValidationError):
    """Raised when constructing a Fabric pipeline schedule fails validation."""


class InvalidChoiceError(PipelineValidationError):
    """Raised when a value is not in a known finite set of allowed choices.

    Example message::

        Unknown dataset 'LakehouseTable' for source 'SqlMISource'. Valid
        datasets: `AzureSqlMITable`, `AzureSqlTable`.
    """

    def __init__(
        self,
        *,
        field: str,
        value: str,
        valid: Sequence[str],
        context: str | None = None,
    ) -> None:
        self.field = field
        self.value = value
        self.valid = tuple(valid)
        self.context = context
        super().__init__(
            format_invalid_choice(field=field, value=value, valid=valid, context=context)
        )


def format_invalid_choice(
    *,
    field: str,
    value: str,
    valid: Sequence[str],
    context: str | None = None,
) -> str:
    """Build a rejection message that enumerates the allowed choices."""
    ctx = context or ""
    choices = ", ".join(f"`{item}`" for item in valid)
    return f"Unknown {field} '{value}'{ctx}. Valid {field}s: {choices}."


class PipelineImportError(ValueError):
    """Raised when parsing Fabric pipeline JSON or item folders fails."""
