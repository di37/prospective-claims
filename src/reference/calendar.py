"""Derive each filer's fiscal calendar from the period ends it actually filed.

Section 5.5 of the annotation manual resolves "next quarter" against the filer's
own calendar rather than the calendar year. A retailer whose year ends in January
resolves the same phrase to a different period than a filer whose year ends in
December, and getting it wrong mislabels every temporal field for that filer
without producing anything that looks like an error.

EDGAR reports a ``fiscalYearEnd`` field, and it is not enough. It holds one
current value, so a filer that changed its year end during the study window
reports only where it ended up, and for a 52/53-week filer it reports whichever
date the most recent year happened to land on. The calendar is therefore derived
from observation: every 10-K period end is an anchor, and the quarters are the
10-Q period ends between consecutive anchors.

Two shapes cover all but a handful of filers. A fixed-date year end lands on the
same calendar date each year, so consecutive anchors are 365 or 366 days apart. A
52/53-week year ends on the same weekday, drifts by a day or two annually, and
inserts a 53rd week roughly every six years, so consecutive anchors are 364 or
371 days apart. The gap sets do not overlap, which is what makes this a decision
rather than a judgement.

What does not fit is reported rather than smoothed. A filer whose year end
changed mid-window carries both regimes and the date it switched. A single anchor
that disagrees with its neighbours is recorded as suspect, because a wrong period
end from EDGAR looks exactly like this and the filing-lag screen cannot see it. A
gap longer than any real fiscal year means an annual report is missing, and the
absent years are named.
"""

# region Imports
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from constants import (
    CALENDAR_FIXED_DAY_TOLERANCE,
    CALENDAR_WEEK_DRIFT_DAYS,
    CALENDAR_FIXED_YEAR_GAPS,
    CALENDAR_MIN_ANCHORS,
    CALENDAR_MODAL_SHARE,
    CALENDAR_WEEK_YEAR_GAPS,
    FISCAL_YEAR_MAX_DAYS,
)

# endregion

# region Models
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


# endregion

# region Classification
def _modal_share(values: list[int]) -> tuple[int | None, float]:
    """Return the most common value and the share of the list it covers.

    Args:
        values: Values to summarise.

    Returns:
        Tuple of the modal value and its share, or (None, 0.0) when empty.
    """
    if not values:
        return None, 0.0
    value, count = Counter(values).most_common(1)[0]
    return value, count / len(values)


def _real_gaps(anchors: list[date]) -> list[int]:
    """Return gaps between consecutive anchors, excluding those spanning a gap.

    A gap longer than any real fiscal year means an annual report is missing, so
    it says nothing about the shape of the calendar and would otherwise drag both
    shares below the threshold.

    Args:
        anchors: Annual period ends, earliest first.

    Returns:
        Gap lengths in days.
    """
    gaps = [(b - a).days for a, b in zip(anchors, anchors[1:])]
    return [gap for gap in gaps if gap <= FISCAL_YEAR_MAX_DAYS]


def classify(anchors: list[date]) -> tuple[CalendarType, int | None, int | None, int | None]:
    """Decide which shape a filer's year ends follow.

    Args:
        anchors: Annual period ends, earliest first.

    Returns:
        Tuple of calendar type, modal month, modal day, and modal weekday.
    """
    if len(anchors) < CALENDAR_MIN_ANCHORS:
        return CalendarType.INSUFFICIENT_DATA, None, None, None

    month, month_share = _modal_share([a.month for a in anchors])
    day, _ = _modal_share([a.day for a in anchors])
    weekday, weekday_share = _modal_share([a.weekday() for a in anchors])

    gaps = _real_gaps(anchors)
    week_share = sum(1 for g in gaps if g in CALENDAR_WEEK_YEAR_GAPS) / len(gaps) if gaps else 0.0
    fixed_share = sum(1 for g in gaps if g in CALENDAR_FIXED_YEAR_GAPS) / len(gaps) if gaps else 0.0

    if weekday_share >= CALENDAR_MODAL_SHARE and week_share >= CALENDAR_MODAL_SHARE:
        return CalendarType.WEEK_52_53, month, day, weekday
    if month_share >= CALENDAR_MODAL_SHARE and fixed_share >= CALENDAR_MODAL_SHARE:
        return CalendarType.FIXED_DATE, month, day, weekday
    return CalendarType.IRREGULAR, month, day, weekday


def _days_apart_in_year(left: date, right: date) -> int:
    """Distance between two dates ignoring the year, the short way round.

    A year end near the turn of the year sits at day 365 one year and day 1 the
    next, which is two days apart rather than three hundred and sixty four.

    Args:
        left: First date.
        right: Second date.

    Returns:
        Days between them, at most half a year.
    """
    straight = abs(left.timetuple().tm_yday - right.timetuple().tm_yday)
    return min(straight, 365 - straight)


def _conforms(
    anchor: date,
    reference: date,
    kind: CalendarType,
    month: int | None,
    day: int | None,
    weekday: int | None,
) -> bool:
    """Check one anchor against the shape the filer usually follows.

    A 52/53-week anchor has to match on weekday and on where it sits in the year.
    Weekday alone is not enough: a filer that moved its year end from March to
    January still lands on the same weekday, so the change would pass unnoticed.

    Args:
        anchor: The annual period end to check.
        reference: A conforming anchor to measure position in the year against.
        kind: The filer's calendar type.
        month: Modal month.
        day: Modal day of month.
        weekday: Modal weekday.

    Returns:
        True when the anchor matches the shape.
    """
    if kind is CalendarType.WEEK_52_53:
        return (
            anchor.weekday() == weekday
            and _days_apart_in_year(anchor, reference) <= CALENDAR_WEEK_DRIFT_DAYS
        )
    if kind is CalendarType.FIXED_DATE:
        return anchor.month == month and abs(anchor.day - (day or 0)) <= CALENDAR_FIXED_DAY_TOLERANCE
    return True


def _different_regime(
    anchor: date,
    reference: date,
    kind: CalendarType,
    month: int | None,
) -> bool:
    """Check whether an anchor sits in a different part of the year entirely.

    This separates the two reasons an anchor can disagree with its neighbours. A
    filer that changed its year end moves it to a different part of the year, so
    the month changes or the position in the year jumps by weeks. A wrong period
    end from EDGAR keeps the year end roughly where it was and is off by days.
    Both fail the conformance test; only the first is a change of calendar.

    Args:
        anchor: The annual period end to check.
        reference: A conforming anchor to measure against.
        kind: The filer's calendar type.
        month: Modal month.

    Returns:
        True when the anchor belongs to a different calendar regime.
    """
    if kind is CalendarType.WEEK_52_53:
        return _days_apart_in_year(anchor, reference) > CALENDAR_WEEK_DRIFT_DAYS
    if kind is CalendarType.FIXED_DATE:
        return anchor.month != month
    return False


def _split_regimes(anchors: list[date]) -> int | None:
    """Find where an irregular filer switched between the two calendar shapes.

    A change shows up as a run of fixed-date gaps followed by a run of 52/53-week
    gaps, or the reverse, with at most one transition year between them that
    belongs to neither.

    Args:
        anchors: Annual period ends, earliest first.

    Returns:
        Index of the first anchor under the new regime, or None if the anchors do
        not split cleanly.
    """
    gaps = [(b - a).days for a, b in zip(anchors, anchors[1:])]
    kinds = [
        "week" if g in CALENDAR_WEEK_YEAR_GAPS else "fixed" if g in CALENDAR_FIXED_YEAR_GAPS else "other"
        for g in gaps
    ]
    for cut in range(1, len(kinds)):
        head = {k for k in kinds[:cut] if k != "other"}
        tail = {k for k in kinds[cut:] if k != "other"}
        if len(head) == 1 and len(tail) == 1 and head != tail:
            if sum(1 for k in kinds if k == "other") <= 1:
                return cut + 1
    return None


# endregion

# region Derivation
def _label_quarter(period_end: date, start: date, end: date) -> int:
    """Label a period end by how far through the fiscal year it falls.

    Quarters are not assumed to be evenly spaced; elapsed fraction is used only to
    decide which of the four an observed date is, and the actual dates are kept.

    Args:
        period_end: The period end to label.
        start: Previous annual anchor, the start of the fiscal year.
        end: This annual anchor, the end of the fiscal year.

    Returns:
        Quarter number from 1 to 4.
    """
    span = (end - start).days
    fraction = (period_end - start).days / span
    return min((1, 2, 3, 4), key=lambda k: abs(fraction - k / 4))


def derive(
    cik: int,
    name: str,
    declared_year_end: str | None,
    annual: list[date],
    quarterly: list[date],
) -> FilerCalendar:
    """Build one filer's calendar from its filed period ends.

    Args:
        cik: SEC identifier for the filer.
        name: Entity name as the SEC records it.
        declared_year_end: EDGAR's ``fiscalYearEnd``, ``MMDD``, or None.
        annual: 10-K period ends, any order.
        quarterly: 10-Q period ends, any order.

    Returns:
        The filer's calendar, including everything that did not fit it.
    """
    anchors = sorted(annual)
    quarters_in = sorted(quarterly)
    kind, month, day, weekday = classify(anchors)

    suspect: list[date] = []
    changed_at: date | None = None
    earlier: CalendarType | None = None
    if kind in (CalendarType.WEEK_52_53, CalendarType.FIXED_DATE):
        # The most recent anchor is the reference for position in the year: where
        # a filer ended up is the regime it is in now.
        reference = anchors[-1]
        odd = [
            i for i, a in enumerate(anchors)
            if not _conforms(a, reference, kind, month, day, weekday)
        ]
        leading = [i for i in odd if i < len(anchors) - 1 and all(j in odd for j in range(i + 1))]
        # A leading run is only a change of calendar if every anchor in it sits in
        # a different part of the year. Otherwise it is a wrong period end that
        # happens to be first, which reads identically until you check where in
        # the year it falls.
        if leading and all(_different_regime(anchors[i], reference, kind, month) for i in leading):
            changed_at = anchors[max(leading) + 1]
        else:
            leading = []
        suspect = [anchors[i] for i in odd if i not in leading]
    elif kind is CalendarType.IRREGULAR:
        cut = _split_regimes(anchors)
        if cut is not None:
            changed_at = anchors[cut]

    # Where the year end changed, the shape reported is the one in force now.
    # Calling a filer irregular for the whole window says nothing useful about
    # how to resolve a quarter under either regime, and "irregular" was never a
    # third kind of calendar, only a window containing two.
    if changed_at is not None:
        index = anchors.index(changed_at)
        kind, month, day, weekday = classify(anchors[index:])
        earlier, _, _, _ = classify(anchors[:index])

    missing: list[int] = []
    quarters: list[FiscalQuarter] = []
    previous: date | None = None
    for anchor in anchors:
        floor = anchor - timedelta(days=FISCAL_YEAR_MAX_DAYS)
        start = max(previous, floor) if previous is not None else floor
        if previous is not None and (anchor - previous).days > FISCAL_YEAR_MAX_DAYS:
            missing.extend(range(previous.year + 1, anchor.year))

        for period_end in [q for q in quarters_in if start < q < anchor]:
            quarters.append(
                FiscalQuarter(
                    cik=cik,
                    fiscal_year=anchor.year,
                    quarter=_label_quarter(period_end, start, anchor),
                    period_end=period_end,
                    form_type="10-Q",
                    days_from_year_start=(period_end - start).days,
                )
            )
        quarters.append(
            FiscalQuarter(
                cik=cik,
                fiscal_year=anchor.year,
                quarter=4,
                period_end=anchor,
                form_type="10-K",
                days_from_year_start=(anchor - start).days,
            )
        )
        previous = anchor

    # A fixed-date year end falls on every weekday in turn, and a 52/53-week year
    # end falls on a different day of the month each year. Reporting the one the
    # shape does not fix would put a meaningless number in the table.
    return FilerCalendar(
        cik=cik,
        name=name,
        calendar_type=kind,
        declared_year_end=declared_year_end,
        modal_month=month,
        modal_day=day if kind is not CalendarType.WEEK_52_53 else None,
        modal_weekday=weekday if kind is CalendarType.WEEK_52_53 else None,
        year_end_changed=changed_at is not None,
        changed_at=changed_at,
        earlier_calendar_type=earlier,
        anchors=tuple(anchors),
        suspect_anchors=tuple(suspect),
        missing_fiscal_years=tuple(missing),
        quarters=tuple(sorted(quarters, key=lambda q: q.period_end)),
    )


# endregion
