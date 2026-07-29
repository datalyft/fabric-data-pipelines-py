# Expressions

Fabric pipelines rely heavily on expression strings. This library provides helpers under `expr` so you can generate common expressions without embedding every string by hand.

## Common helpers

```python
from fabric_data_pipelines import expr

expr.parameter("run_date")
# '@pipeline().parameters.run_date'

expr.activity_output("get_tables", "value")
# "@activity('get_tables').output.value"

expr.library_variable("MyConnection")
expr.interp(expr.run_id())
```

## What these are useful for

Use expressions when you need to reference:

- pipeline parameters
- activity outputs
- pipeline metadata such as run ID or pipeline name
- library variables and linked resources
- interpolated values inside SQL or script text

## String interpolation

`expr.interp(...)` is especially useful when a Fabric activity expects a larger string that embeds an expression, such as SQL text or a command template.

## Keep expressions readable

Recommended practice:

- build expressions from helpers where possible
- assign complex reusable expressions to well-named Python variables
- isolate very long activity output paths in constants when they appear more than once

See `examples/etl_with_lock_pattern.py` for reusable lock-output constants and SQL interpolation, and `examples/lakehouse_lookup_to_warehouse.py` for `expr.activity_output(...)` with `SetVariable`.

The ETL lock example in [ETL Patterns](../guides/etl-patterns.md) shows this style in practice.
