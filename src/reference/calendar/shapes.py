"""Decide which shape a filer's year ends follow, and which anchors do not fit.

The two shapes are separable because their year lengths do not overlap: a
fixed-date year end puts consecutive years 365 or 366 days apart, a 52/53-week one
364 or 371. What makes this more than a classification is telling a changed year
end from a wrong period end, since both disagree with their neighbours and only
one is a change of calendar.
"""

# region Imports
from __future__ import annotations

from collections import Counter
from datetime import date

from constants import (
    CALENDAR_FIXED_DAY_TOLERANCE,
    CALENDAR_FIXED_YEAR_GAPS,
    CALENDAR_MIN_ANCHORS,
    CALENDAR_MODAL_SHARE,
    CALENDAR_WEEK_DRIFT_DAYS,
    CALENDAR_WEEK_YEAR_GAPS,
    FISCAL_YEAR_MAX_DAYS,
)
from reference.calendar.models import CalendarType

# endregion

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
