"""What a fiscal calendar is: quarters, the shapes they take, and what did not fit.

``FilerCalendar`` validates on construction that its quarters are ordered and
contiguous, because a gap would make "two quarters ahead" mean two filed quarters
rather than two elapsed ones.
"""

# region Imports
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# endregion

class CalendarType(str, Enum):
    """How a filer's fiscal year end behaves across the study window."""

    WEEK_52_53 = "week_52_53"
    FIXED_DATE = "fixed_date"
    IRREGULAR = "irregular"
    INSUFFICIENT_DATA = "insufficient_data"

class FiscalQuarter(BaseModel):
    """One observed fiscal period, labelled with the quarter it closes.

    Attributes:
        cik: SEC identifier for the filer.
        fiscal_year: Calendar year the fiscal year ends in. This is a convention
            chosen because it is decidable from the dates alone, not the filer's
            own name for the year: Walmart calls the year ending January 2024
            fiscal 2024 while Target calls the year ending January 2023 fiscal
            2022, so no single rule matches every filer. Join on ``period_end``.
        quarter: 1 to 4. Quarter 4 is the annual period end, since the 10-K
            covers it rather than a fourth 10-Q.
        period_end: The period end as filed.
        form_type: Form the period end came from.
        days_from_year_start: Days between the previous annual anchor and this
            period end, so uneven quarters are visible rather than assumed away.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    fiscal_year: int
    quarter: int = Field(ge=1, le=4)
    period_end: date
    form_type: str
    days_from_year_start: int = Field(ge=0)

class FilerCalendar(BaseModel):
    """One filer's calendar shape and everything that did not fit it.

    Attributes:
        cik: SEC identifier for the filer.
        name: Entity name as the SEC records it.
        calendar_type: Which shape the anchors follow.
        declared_year_end: EDGAR's ``fiscalYearEnd``, ``MMDD``, for comparison.
            None when EDGAR reports none, which one filer in the study does.
        modal_month: Month the year end usually falls in, None when unclassified.
        modal_day: Day of month the year end usually falls on, for fixed dates.
        modal_weekday: Weekday the year end falls on, Monday is 0, for 52/53-week
            filers.
        year_end_changed: Whether the year end changed during the window.
        changed_at: The first anchor under the new regime, when it changed.
        earlier_calendar_type: The shape before the change, when there was one.
            Often ``insufficient_data``, because a change early in the window
            leaves too few anchors before it to classify.
        anchors: Annual period ends used, earliest first.
        suspect_anchors: Anchors that disagree with their neighbours and are
            probably wrong period ends rather than a real change.
        missing_fiscal_years: Fiscal years with no annual report between anchors.
        quarters: Every labelled period, earliest first.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    name: str
    calendar_type: CalendarType
    declared_year_end: str | None = None
    modal_month: int | None = None
    modal_day: int | None = None
    modal_weekday: int | None = None
    year_end_changed: bool = False
    changed_at: date | None = None
    earlier_calendar_type: CalendarType | None = None
    anchors: tuple[date, ...] = ()
    suspect_anchors: tuple[date, ...] = ()
    missing_fiscal_years: tuple[int, ...] = ()
    quarters: tuple[FiscalQuarter, ...] = ()
