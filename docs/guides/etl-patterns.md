# ETL Patterns

These examples model pipelines you would actually run in a Fabric workspace: landing ingestion, notebook transforms, scheduled gold refreshes, lakehouse-to-warehouse hand-offs, parameterized ELT controllers, and lock-guarded orchestration.

All scripts live under `examples/` and print Fabric JSON (or write an item folder) when run with `uv run python examples/<name>.py`.

## Example catalog

| Example | What it shows |
| --- | --- |
| `daily_notebook_transform.py` | Smallest useful flow: `Wait` → `Notebook` |
| `landing_truncate_copy.py` | Sql MI truncate + `Copy` with column mappings and library variables |
| `scheduled_gold_refresh.py` | Weekly schedule, pinned `logical_id`, `save_item()` Git folder export |
| `lakehouse_lookup_to_warehouse.py` | `Lookup` → `SetVariable` → Lakehouse-to-Warehouse `Copy` |
| `parameterized_elt_controller.py` | `Parameter`, `ForEach`, `Dataflow`, `Switch`, `StoredProcedure`, `Fail` |
| `etl_with_lock_pattern.py` | Lock acquire / retry / invoke child / release |

## Pattern: truncate, then copy

`examples/landing_truncate_copy.py` is the classic landing load:

1. `Script` truncates the landing table.
2. `Copy` reads a typed SQL subset from an ERP twin.
3. `TabularTranslator` maps columns explicitly.
4. Connections come from Fabric Variable Library entries via `LibraryVariable`.

Use this when promoting UI-built landing pipelines into code without losing connector detail.

## Pattern: scheduled notebook refresh

`examples/scheduled_gold_refresh.py` attaches a weekday evening schedule with `weekly_at`, pins `logical_id` so renames stay the same Fabric item, and writes:

```text
Gold_Finance_Metrics_Refresh.DataPipeline/
  pipeline-content.json
  .platform
  .schedules
```

See [Scheduling](scheduling.md) for the schedule model and [Exporting](../concepts/exporting.md) for `save_item()` / `save_workspace()`.

## Pattern: lookup watermark, then load warehouse

`examples/lakehouse_lookup_to_warehouse.py` covers the ELT hand-off:

1. `Lookup` reads the latest batch from a Lakehouse control table.
2. `SetVariable` stores `batch_id` for downstream use.
3. `Copy` appends silver facts into a Fabric Warehouse table.
4. Pipeline `parameters` and `variables` keep the graph reusable.

## Pattern: parameterized ELT controller

`examples/parameterized_elt_controller.py` is a parent controller:

1. `ForEach` walks `@pipeline().parameters.tables`.
2. Each iteration refreshes a Dataflow Gen2 item.
3. `Switch` on `mode` runs a warehouse merge for `full`, otherwise `Fail`.

This is the pattern to reach for when one pipeline should drive many similar loads.

## Pattern: lock, wait, run, release

`examples/etl_with_lock_pattern.py` models a concurrency-1 sales ETL orchestrator:

1. Try to acquire a lock with a `Script` activity.
2. Use `IfCondition` to detect whether the lock was acquired.
3. If not, `Wait` and retry inside an `Until` loop.
4. Once the lock is acquired, `ExecutePipeline` runs the child pipeline.
5. A final `Script` releases the lock on `Completed`.

### Techniques worth copying

- assign long expression paths to named Python constants
- separate query text into structured `ScriptBlock` objects
- model retry behavior with `Until` instead of hand-wiring repetitive dependencies
- keep release and cleanup steps explicit in the graph (`on="Completed"`)

## Where to start

1. `daily_notebook_transform.py` — first successful export
2. `landing_truncate_copy.py` — first real data movement
3. `scheduled_gold_refresh.py` — first Git item folder with a schedule
4. `etl_with_lock_pattern.py` — production-style orchestration
