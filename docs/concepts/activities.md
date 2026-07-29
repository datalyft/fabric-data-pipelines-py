# Activities

Activities are the units of work in a Fabric pipeline. This library models them as typed Python objects so you can construct payloads without manually assembling nested dictionaries.

## Supported activity models

| Class | Fabric `type` | Notes |
| --- | --- | --- |
| `Copy` | `Copy` | Typed SQL MI / Lakehouse / Warehouse sources and sinks |
| `Lookup` | `Lookup` | Retrieve data for later expressions or branching |
| `Notebook` | `TridentNotebook` | Run a Fabric notebook |
| `Dataflow` | `RefreshDataFlow` | Trigger Dataflow Gen2 refreshes |
| `StoredProcedure` | `SqlServerStoredProcedure` | Execute stored procedures |
| `Script` | `Script` | Run query or non-query script blocks |
| `ExecutePipeline` | `ExecutePipeline` | Invoke another pipeline |
| `SetVariable` / `AppendVariable` | `SetVariable` / `AppendVariable` | Work with pipeline variables |
| `IfCondition` | `IfCondition` | Conditional nested execution |
| `ForEach` | `ForEach` | Iterate over collections |
| `Switch` | `Switch` | Multi-branch flow |
| `Until` | `Until` | Repeat-until-success flow |
| `Wait` | `Wait` | Delay execution |
| `Fail` | `Fail` | Explicitly fail a pipeline |
| `Web` | `WebActivity` | HTTP calls via a Fabric connection |
| `RawActivity` | *(any)* | Escape hatch for unsupported activity shapes |

## Not modeled yet

These Fabric activity types have no first-class class yet. Pass them through `RawActivity`, or track progress on the [Roadmap](../roadmap.md):

| Fabric activity | Notes |
| --- | --- |
| GetMetadata | Dataset metadata |
| Azure Function | Function apps |
| Teams / Outlook | Notification activities |
| Others | Filter, PBI semantic model refresh, … — see `RawActivity` docs |

## When to use typed activities

Prefer the typed classes when the library already models the Fabric activity you need. They make code easier to read, give you validation, and reduce the risk of malformed payloads.

Use `RawActivity` when:

- Fabric supports an activity not modeled yet
- you need to pass through a payload copied from an existing Fabric export
- you want to move quickly while waiting for first-class support

## Activity composition

Activities become useful when combined with dependencies and expressions:

- dependencies determine execution order
- expressions let later activities refer to parameters, metadata, and outputs
- nested activities enable branching and loops

Read [Dependencies](dependencies.md) and [Expressions](expressions.md) next. For end-to-end compositions, see [ETL Patterns](../guides/etl-patterns.md).
