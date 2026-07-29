# API Reference

This section documents the public Python API of `fabric-data-pipelines`. Symbols are grouped by concept so you can jump to the area you need instead of scrolling a single dump of the package.

## Where to look

| Page | Contents |
| --- | --- |
| [Pipeline](pipeline.md) | `Pipeline`, parameters, variables, library variables |
| [Activities: Base](activities/base.md) | Shared activity model, dependencies, policies |
| [Activities: Control Flow](activities/control.md) | `IfCondition`, `ForEach`, `Switch`, `Until`, `Wait`, `Fail` |
| [Activities: Data Movement](activities/data-movement.md) | `Copy`, `Lookup`, sources, sinks, datasets |
| [Activities: Execution](activities/execution.md) | Notebooks, scripts, dataflows, stored procedures, child pipelines, Web |
| [Activities: Variables](activities/variables.md) | `SetVariable`, `AppendVariable` |
| [Activities: Raw](activities/raw.md) | Escape hatch for unmodeled Fabric activities |
| [Expressions](expressions.md) | `expr` helpers for Fabric expression strings |
| [Schedules](schedules.md) | Schedule models written to `.schedules` |
| [Export](export.md) | Workspace export and serialization helpers |
| [Errors](errors.md) | Validation and schedule error types |
| [Changelog](changelog.md) | Release history |

Import symbols from the top-level package:

```python
from fabric_data_pipelines import Pipeline, Wait, expr, save_workspace
```
