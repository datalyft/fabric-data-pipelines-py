"""Scheduled gold refresh — notebook plus Fabric Git item export.

Scenario: every weekday evening, refresh gold-layer metrics with a notebook
and publish a Fabric-ready item folder (including `.schedules` and a pinned
`logicalId` so renames do not create a new Fabric item).
"""

from datetime import date, time
from pathlib import Path
from zoneinfo import ZoneInfo

from fabric_data_pipelines import Notebook, Pipeline, Weekday, weekly_at

WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"
NOTEBOOK_ID = "00000000-0000-0000-0000-000000000002"

refresh = Notebook(
    name="Refresh_Gold_Finance_Metrics",
    notebook_id=NOTEBOOK_ID,
    workspace_id=WORKSPACE_ID,
)

pipeline = Pipeline(
    name="Gold_Finance_Metrics_Refresh",
    description="Weeknight gold refresh for finance metrics dashboards.",
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

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "out"
    item_dir = pipeline.save_item(out)
    print(f"Wrote Fabric item folder: {item_dir}")
