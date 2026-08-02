"""Validation and import errors raised when building a Fabric pipeline."""

from __future__ import annotations


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


class PipelineImportError(ValueError):
    """Raised when parsing Fabric pipeline JSON or item folders fails."""
