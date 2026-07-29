# Scheduling

Microsoft Fabric stores pipeline schedules separately from the main pipeline definition. In Git-backed item folders, that means schedule settings live in `.schedules` alongside `pipeline-content.json` and `.platform`.

Schedules are not free-floating: attach one or more `Schedule` instances on the pipeline with `Pipeline(schedules=[...])`. Fabric allows at most 20 schedules per pipeline; the library enforces that limit.

## Define a schedule and attach it

```python
from datetime import date, time
from zoneinfo import ZoneInfo

from fabric_data_pipelines import Notebook, Pipeline, Weekday, weekly_at

refresh = Notebook(
    name="Refresh_Gold_Finance_Metrics",
    notebook_id="00000000-0000-0000-0000-000000000002",
    workspace_id="00000000-0000-0000-0000-000000000001",
)

pipeline = Pipeline(
    name="Gold_Finance_Metrics_Refresh",
    activities=[refresh],
    logical_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    schedules=[
        weekly_at(
            time(21, 30),
            weekdays=[
                Weekday.MONDAY,
                Weekday.TUESDAY,
                Weekday.WEDNESDAY,
                Weekday.THURSDAY,
                Weekday.FRIDAY,
            ],
            start_date_time=date(2026, 7, 10),
            end_date_time=date(2027, 7, 10),
            local_time_zone_id=ZoneInfo("Europe/Amsterdam"),
        )
    ],
)
```

`weekly_at` is the convenience helper for the common weekday shape. You can also build `Schedule(configuration=Weekly(...))`, `Daily`, `Monthly`, or `Cron` directly.

## Write the Fabric item

```python
pipeline.save_item("out")
```

If schedules are attached, the output folder includes `.schedules`. Passing more than 20 schedules raises a validation error.

## Full runnable example

See `examples/scheduled_gold_refresh.py` for a complete weekday gold-refresh pipeline that pins `logical_id` and exports the item folder.

## Why this matters

This separation mirrors Fabric's Git representation, so the generated folder structure is ready for repositories where Fabric items are managed as source-controlled assets instead of being created only through the UI.
