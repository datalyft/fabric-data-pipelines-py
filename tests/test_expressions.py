"""Unit tests for expression helpers."""

from fabric_data_pipelines import expr


def test_parameter() -> None:
    assert expr.parameter("run_date") == "@pipeline().parameters.run_date"


def test_variable() -> None:
    assert expr.variable("row_count") == "@variables('row_count')"


def test_library_variable() -> None:
    assert (
        expr.library_variable("Demo_ETL_Library_SourceDb")
        == "@pipeline().libraryVariables.Demo_ETL_Library_SourceDb"
    )


def test_activity_output() -> None:
    assert expr.activity_output("get_tables") == "@activity('get_tables').output"
    assert expr.activity_output("lookup", "value") == "@activity('lookup').output.value"


def test_item() -> None:
    assert expr.item() == "@item()"
    assert expr.item("name") == "@item().name"


def test_run_id_and_pipeline_name() -> None:
    assert expr.run_id() == "@pipeline().RunId"
    assert expr.pipeline_name() == "@pipeline().Pipeline"


def test_interp() -> None:
    assert expr.interp(expr.run_id()) == "@{pipeline().RunId}"
    assert expr.interp("pipeline().RunId") == "@{pipeline().RunId}"


def test_equals_nested() -> None:
    result = expr.equals(expr.parameter("full_load"), 1)
    assert result == "@equals(pipeline().parameters.full_load, 1)"


def test_bool_or_not() -> None:
    assert expr.bool_(True) == "@bool(true)"
    assert expr.bool_(False) == "@bool(false)"
    nested = expr.not_(expr.equals(expr.parameter("flag"), 0))
    assert nested == "@not(equals(pipeline().parameters.flag, 0))"


def test_expr_is_str() -> None:
    value = expr.parameter("x")
    assert isinstance(value, str)
    assert f"prefix-{value}" == "prefix-@pipeline().parameters.x"
