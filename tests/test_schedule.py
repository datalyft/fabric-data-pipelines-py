from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from fabric_data_pipelines import (
    Cron,
    MonthlyOccurrence,
    Pipeline,
    Schedule,
    Weekday,
    Weekly,
    weekly_at,
)
from tests.helpers import assert_dict_matches_snapshot


def test_weekly_schedule_matches_snapshot() -> None:
    pipeline = Pipeline(
        name="sales_etl_history_full_load",
        activities=[],
        schedules=[
            Schedule(
                enabled=True,
                job_type="Execute",
                configuration=Weekly(
                    start_date_time="2026-07-10T00:00:00",
                    end_date_time="2027-07-10T00:00:00",
                    local_time_zone_id="Romance Standard Time",
                    times=["21:30"],
                    weekdays=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                ),
            )
        ],
    )

    schedules = pipeline.schedules_dict()
    assert schedules is not None
    assert_dict_matches_snapshot(schedules, "sales_etl_schedules.json")


def test_weekly_times_validator_rejects_bad_format() -> None:
    with pytest.raises(ValidationError):
        Weekly(times=["2:30"], weekdays=["Monday"])


def test_weekly_weekdays_validator_rejects_duplicates() -> None:
    with pytest.raises(ValidationError):
        Weekly(times=["21:30"], weekdays=["Monday", "Monday"])


def test_monthly_monthlyoccurrence_weekday_alias_serializes_as_WeekDay() -> None:
    occ = MonthlyOccurrence(
        occurrence_type="OrdinalWeekday",
        week_index="First",
        week_day="Monday",  # ensure it serializes to `WeekDay`
    )
    dumped = occ.model_dump(by_alias=True, exclude_none=True, mode="json")
    assert "WeekDay" in dumped
    assert dumped["WeekDay"] == "Monday"
    assert "weekDay" not in dumped


def test_monthly_occurrence_requires_fields_for_ordinal_weekday() -> None:
    with pytest.raises(ValidationError):
        MonthlyOccurrence(
            occurrence_type="OrdinalWeekday",
            week_index="First",
            week_day=None,
        )


def test_schedule_accepts_python_datetime_time_and_zoneinfo_objects() -> None:
    pipeline = Pipeline(
        name="pythonic_inputs",
        activities=[],
        schedules=[
            Schedule(
                configuration=Weekly(
                    start_date_time=date(2026, 7, 10),
                    end_date_time=datetime(2027, 7, 10, 0, 0, 0),
                    local_time_zone_id=ZoneInfo("Europe/Amsterdam"),
                    times=[time(21, 30)],
                    weekdays=["Monday"],
                )
            )
        ],
    )

    schedules = pipeline.schedules_dict()
    assert schedules is not None
    config = schedules["schedules"][0]["configuration"]
    assert config["startDateTime"] == "2026-07-10T00:00:00"
    assert config["endDateTime"] == "2027-07-10T00:00:00"
    assert config["localTimeZoneId"] == "Europe/Amsterdam"
    assert config["times"] == ["21:30"]


def test_cron_accepts_timedelta_interval() -> None:
    schedule = Schedule(configuration=Cron(interval=timedelta(minutes=15)))
    dumped = schedule.model_dump(by_alias=True, exclude_none=True, mode="json")
    assert dumped["configuration"]["interval"] == 15


def test_cron_rejects_non_whole_minute_timedelta() -> None:
    with pytest.raises(ValidationError):
        Cron(interval=timedelta(seconds=90))


def test_schedule_accepts_timezone_utc_object() -> None:
    schedule = Schedule(
        configuration=Weekly(
            start_date_time=datetime(2026, 7, 10, 0, 0, 0),
            local_time_zone_id=timezone.utc,
            times=[time(8, 0)],
            weekdays=["Monday"],
        )
    )
    dumped = schedule.model_dump(by_alias=True, exclude_none=True, mode="json")
    assert dumped["configuration"]["localTimeZoneId"] == "UTC"


def test_weekly_accepts_weekday_enum_values() -> None:
    schedule = Schedule(
        configuration=Weekly(
            times=["21:30"],
            weekdays=[Weekday.MONDAY, Weekday.FRIDAY],
        )
    )
    dumped = schedule.model_dump(by_alias=True, exclude_none=True, mode="json")
    assert dumped["configuration"]["weekdays"] == ["Monday", "Friday"]


def test_weekly_at_helper_builds_schedule() -> None:
    schedule = weekly_at(
        time(21, 30),
        weekdays=[Weekday.MONDAY, Weekday.TUESDAY],
        start_date_time=date(2026, 7, 10),
        local_time_zone_id=ZoneInfo("Europe/Amsterdam"),
    )
    dumped = schedule.model_dump(by_alias=True, exclude_none=True, mode="json")
    config = dumped["configuration"]
    assert dumped["enabled"] is True
    assert dumped["jobType"] == "Execute"
    assert config["type"] == "Weekly"
    assert config["times"] == ["21:30"]
    assert config["weekdays"] == ["Monday", "Tuesday"]
    assert config["startDateTime"] == "2026-07-10T00:00:00"
    assert config["localTimeZoneId"] == "Europe/Amsterdam"


def _sample_schedule() -> Schedule:
    return Schedule(configuration=Weekly(times=["21:30"], weekdays=["Monday"]))


def test_pipeline_accepts_up_to_twenty_attached_schedules() -> None:
    schedules = [_sample_schedule() for _ in range(20)]
    pipeline = Pipeline(name="max_schedules", activities=[], schedules=schedules)
    assert pipeline.schedules is not None
    assert len(pipeline.schedules) == 20
    assert pipeline.schedules_dict() is not None


def test_pipeline_rejects_more_than_twenty_schedules() -> None:
    schedules = [_sample_schedule() for _ in range(21)]
    with pytest.raises(ValidationError, match="at most 20 schedules"):
        Pipeline(name="too_many_schedules", activities=[], schedules=schedules)
