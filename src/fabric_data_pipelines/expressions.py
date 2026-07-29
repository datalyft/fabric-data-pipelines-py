"""Helpers that render Fabric expression language strings.

Fabric pipelines use expressions such as ``@pipeline().parameters.x`` and
``@activity('name').output``. Prefer these helpers over hard-coded strings so
typos are caught early and the rendered form stays consistent.

Example::

    from fabric_data_pipelines import expr

    expr.parameter("run_date")
    # '@pipeline().parameters.run_date'

    expr.activity_output("get_tables")
    # "@activity('get_tables').output"
"""

from __future__ import annotations

from typing import Any


class Expr(str):
    """A Fabric expression string that is also a plain ``str``.

    Subclassing ``str`` means an ``Expr`` can be passed anywhere a string field
    is accepted (SQL text, connection ids, notebook parameters, etc.).
    """

    __slots__ = ()

    def __new__(cls, value: str) -> Expr:
        return str.__new__(cls, value)

    def __repr__(self) -> str:
        return f"Expr({str.__repr__(self)})"


def parameter(name: str) -> Expr:
    """Reference a pipeline parameter: ``@pipeline().parameters.<name>``.

    Example::

        expr.parameter("run_date")
        # '@pipeline().parameters.run_date'
    """
    return Expr(f"@pipeline().parameters.{name}")


def variable(name: str) -> Expr:
    """Reference a pipeline variable: ``@variables('<name>')``.

    Example::

        expr.variable("row_count")
        # "@variables('row_count')"
    """
    return Expr(f"@variables('{name}')")


def library_variable(name: str) -> Expr:
    """Reference a Variable Library value: ``@pipeline().libraryVariables.<name>``.

    Example::

        expr.library_variable("Demo_ETL_Library_SourceDb")
        # '@pipeline().libraryVariables.Demo_ETL_Library_SourceDb'
    """
    return Expr(f"@pipeline().libraryVariables.{name}")


def activity_output(name: str, path: str = "") -> Expr:
    """Reference an activity's output: ``@activity('<name>').output[.path]``.

    Example::

        expr.activity_output("get_tables")
        # "@activity('get_tables').output"

        expr.activity_output("lookup", "value")
        # "@activity('lookup').output.value"
    """
    base = f"@activity('{name}').output"
    if path:
        return Expr(f"{base}.{path}")
    return Expr(base)


def item(path: str = "") -> Expr:
    """Reference the current ForEach item: ``@item()[.path]``.

    Example::

        expr.item()
        # '@item()'

        expr.item("name")
        # '@item().name'
    """
    if path:
        return Expr(f"@item().{path}")
    return Expr("@item()")


def run_id() -> Expr:
    """Reference the current pipeline run id: ``@pipeline().RunId``."""
    return Expr("@pipeline().RunId")


def pipeline_name() -> Expr:
    """Reference the current pipeline name: ``@pipeline().Pipeline``."""
    return Expr("@pipeline().Pipeline")


def interp(expression: str) -> str:
    """Wrap an expression for string interpolation inside SQL or text.

    Fabric uses ``@{...}`` (without a leading ``@`` on the outer string) when
    embedding expressions inside larger string literals.

    Example::

        f"EXEC usp_Lock @RunId = N'{expr.interp(expr.run_id())}';"
        # "EXEC usp_Lock @RunId = N'@{pipeline().RunId}';"
    """
    # Strip a leading @ so callers can pass either Expr("@pipeline()...") or
    # a bare "pipeline()..." fragment.
    body = expression[1:] if expression.startswith("@") else expression
    return f"@{{{body}}}"


def equals(left: Any, right: Any) -> Expr:
    """Render ``@equals(left, right)``.

    Example::

        expr.equals(expr.parameter("full_load"), 1)
        # '@equals(pipeline().parameters.full_load, 1)'
    """
    return func("equals", left, right)


def not_(operand: Any) -> Expr:
    """Render ``@not(operand)``.

    Example::

        expr.not_(expr.equals(expr.parameter("flag"), 0))
    """
    return func("not", operand)


def and_(*operands: Any) -> Expr:
    """Render ``@and(a, b, ...)``."""
    return func("and", *operands)


def or_(*operands: Any) -> Expr:
    """Render ``@or(a, b, ...)``."""
    return func("or", *operands)


def concat(*parts: Any) -> Expr:
    """Render ``@concat(a, b, ...)``."""
    return func("concat", *parts)


def bool_(value: bool) -> Expr:
    """Render ``@bool(true)`` or ``@bool(false)``."""
    return Expr(f"@bool({'true' if value else 'false'})")


def func(name: str, *args: Any) -> Expr:
    """Render an arbitrary Fabric function: ``@name(arg1, arg2, ...)``.

    Example::

        expr.func("string", expr.parameter("n"))
        # '@string(pipeline().parameters.n)'
    """
    rendered = ", ".join(_render_arg(arg) for arg in args)
    return Expr(f"@{name}({rendered})")


def _render_arg(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if value is None:
        return "null"
    text = str(value)
    # Nested expressions passed as @equals(...) should drop the leading @ so
    # they become bare function calls inside an outer expression.
    if text.startswith("@"):
        return text[1:]
    if text.startswith("'") and text.endswith("'"):
        return text
    # Quote plain strings.
    escaped = text.replace("'", "''")
    return f"'{escaped}'"
