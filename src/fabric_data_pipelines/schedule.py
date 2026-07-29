"""Pipeline schedule (job scheduler) configuration for Fabric Git integration.

Fabric represents schedules in a separate `.schedules` file alongside
`pipeline-content.json` and `.platform`. This module models that JSON.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import AliasChoices, Field, field_validator, model_validator

from fabric_data_pipelines.errors import ScheduleValidationError
from fabric_data_pipelines.serialization import FabricModel

_TIME_RE = re.compile(r"^(?P<hour>\d{2}):(?P<minute>\d{2})$")
DayOfWeekValues = Literal[
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]

# Expose a typed alias for user ergonomics.
DayOfWeek = DayOfWeekValues


class Weekday(str, Enum):
    """Enum-style weekday values for ergonomic schedule declarations."""

    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"


class ScheduleParameter(FabricModel):
    """A job parameter reference passed to scheduled jobs."""

    name: str
    type: Literal["VariableReference"] = "VariableReference"
    value: str


class MonthlyOccurrence(FabricModel):
    """Monthly occurrence definition for a schedule config."""

    occurrence_type: Literal["DayOfMonth", "OrdinalWeekday"]
    day_of_month: int | None = None
    week_index: Literal["First", "Second", "Third", "Fourth", "Fifth"] | None = None
    # Fabric JSON uses `WeekDay` (capital W); keep the Python field name for __init__.
    week_day: DayOfWeekValues | None = Field(
        default=None,
        validation_alias=AliasChoices("WeekDay", "week_day", "weekDay"),
        serialization_alias="WeekDay",
    )

    @model_validator(mode="after")
    def _validate_occurrence(self) -> MonthlyOccurrence:
        if self.occurrence_type == "DayOfMonth" and self.day_of_month is None:
            raise ScheduleValidationError(
                "MonthlyOccurrence.day_of_month is required when occurrence_type='DayOfMonth'"
            )
        if self.occurrence_type == "OrdinalWeekday" and (
            self.week_index is None or self.week_day is None
        ):
            raise ScheduleValidationError(
                "MonthlyOccurrence.week_index and week_day are required when "
                "occurrence_type='OrdinalWeekday'"
            )
        return self

    @field_validator("day_of_month")
    @classmethod
    def _validate_day_of_month(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if not (1 <= v <= 31):
            raise ScheduleValidationError("MonthlyOccurrence.day_of_month must be between 1 and 31")
        return v


class ScheduleConfigurationBase(FabricModel):
    """Common configuration fields across all schedule kinds."""

    # Discriminator. Each subclass narrows this to a literal enum member.
    type: str
    # Accept date/str/tzinfo at construction; validators normalize to datetime/str.
    start_date_time: datetime | date | str | None = None
    end_date_time: datetime | date | str | None = None
    local_time_zone_id: str | tzinfo | None = None
    parameters: list[ScheduleParameter] | None = None

    @field_validator("start_date_time", "end_date_time", mode="before")
    @classmethod
    def _coerce_datetime_like(cls, v: Any) -> Any:
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, time.min)
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError as exc:
                raise ScheduleValidationError(
                    f"Invalid datetime '{v}'; expected an ISO-8601 datetime"
                ) from exc
        return v

    @field_validator("local_time_zone_id", mode="before")
    @classmethod
    def _coerce_timezone_like(cls, v: Any) -> Any:
        if v is None or isinstance(v, str):
            return v
        if isinstance(v, tzinfo):
            zone_name = getattr(v, "key", None)
            if isinstance(zone_name, str) and zone_name:
                return zone_name

            if v is timezone.utc:
                return "UTC"

            zone_name = v.tzname(None)
            if zone_name:
                return zone_name

            raise ScheduleValidationError(
                "local_time_zone_id tzinfo values must provide a stable zone name"
            )
        return v


class CronScheduleConfiguration(ScheduleConfigurationBase):
    type: Literal["Cron"] = "Cron"
    # Accept timedelta at construction; validator normalizes to whole minutes.
    interval: int | timedelta

    @field_validator("interval", mode="before")
    @classmethod
    def _coerce_interval(cls, v: Any) -> Any:
        if isinstance(v, timedelta):
            total_seconds = v.total_seconds()
            if total_seconds % 60 != 0:
                raise ScheduleValidationError(
                    "Cron interval timedeltas must resolve to a whole number of minutes"
                )
            return int(total_seconds // 60)
        return v

    @field_validator("interval")
    @classmethod
    def _validate_interval(cls, v: int) -> int:
        if v < 1:
            raise ScheduleValidationError("Cron interval must be a positive number of minutes")
        return v


class _TimesMixin(FabricModel):
    # Accept time/datetime at construction; validator normalizes to "HH:MM" strings.
    times: list[str | time | datetime]

    @field_validator("times", mode="before")
    @classmethod
    def _coerce_times(cls, v: Any) -> Any:
        if not isinstance(v, list):
            return v

        normalized: list[str] = []
        for item in v:
            if isinstance(item, (datetime, time)):
                normalized.append(item.strftime("%H:%M"))
            else:
                normalized.append(item)
        return normalized

    @field_validator("times")
    @classmethod
    def _validate_times(cls, v: list[str | time | datetime]) -> list[str]:
        if len(v) > 100:
            raise ScheduleValidationError("Schedule times must have at most 100 entries")
        parsed: list[str] = []
        for t in v:
            if not isinstance(t, str):
                raise ScheduleValidationError(f"Invalid time '{t}'; expected 'hh:mm'")
            m = _TIME_RE.fullmatch(t)
            if not m:
                raise ScheduleValidationError(f"Invalid time '{t}'; expected 'hh:mm'")
            hour = int(m.group("hour"))
            minute = int(m.group("minute"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ScheduleValidationError(
                    f"Invalid time '{t}'; expected a valid 24h clock time"
                )
            parsed.append(t)
        return parsed


class DailyScheduleConfiguration(_TimesMixin, ScheduleConfigurationBase):
    type: Literal["Daily"] = "Daily"
    times: list[str | time | datetime]


class WeeklyScheduleConfiguration(_TimesMixin, ScheduleConfigurationBase):
    type: Literal["Weekly"] = "Weekly"
    weekdays: list[DayOfWeekValues | Weekday]

    @field_validator("weekdays", mode="before")
    @classmethod
    def _coerce_weekdays(cls, v: Any) -> Any:
        if not isinstance(v, list):
            return v
        return [item.value if isinstance(item, Weekday) else item for item in v]

    @field_validator("weekdays")
    @classmethod
    def _validate_weekdays(cls, v: list[DayOfWeekValues | Weekday]) -> list[DayOfWeekValues]:
        normalized = [item.value if isinstance(item, Weekday) else item for item in v]
        if len(normalized) > 7:
            raise ScheduleValidationError("Schedule weekdays must have at most 7 entries")
        if len(set(normalized)) != len(normalized):
            raise ScheduleValidationError("Schedule weekdays must not contain duplicates")
        return normalized


class MonthlyScheduleConfiguration(_TimesMixin, ScheduleConfigurationBase):
    type: Literal["Monthly"] = "Monthly"
    times: list[str | time | datetime]
    recurrence: int | None = None
    occurrence: MonthlyOccurrence | None = None

    @field_validator("recurrence")
    @classmethod
    def _validate_recurrence(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if v < 1:
            raise ScheduleValidationError("Monthly recurrence must be a positive number of months")
        return v


ScheduleConfiguration = Annotated[
    CronScheduleConfiguration
    | DailyScheduleConfiguration
    | WeeklyScheduleConfiguration
    | MonthlyScheduleConfiguration,
    Field(discriminator="type"),
]


class Schedule(FabricModel):
    """One schedule entry in `.schedules`."""

    enabled: bool = True
    job_type: str = "Execute"
    configuration: ScheduleConfiguration


# Public aliases for the schedule configuration kinds.
Cron = CronScheduleConfiguration
Daily = DailyScheduleConfiguration
Weekly = WeeklyScheduleConfiguration
Monthly = MonthlyScheduleConfiguration


def weekly_at(
    at: str | time | datetime,
    *,
    weekdays: list[DayOfWeekValues | Weekday],
    start_date_time: datetime | date | None = None,
    end_date_time: datetime | date | None = None,
    local_time_zone_id: str | tzinfo | None = None,
    parameters: list[ScheduleParameter] | None = None,
    enabled: bool = True,
    job_type: str = "Execute",
) -> Schedule:
    """Convenience helper for the most common weekly schedule shape."""

    return Schedule(
        enabled=enabled,
        job_type=job_type,
        configuration=Weekly(
            start_date_time=start_date_time,
            end_date_time=end_date_time,
            local_time_zone_id=local_time_zone_id,
            parameters=parameters,
            times=[at],
            weekdays=weekdays,
        ),
    )
