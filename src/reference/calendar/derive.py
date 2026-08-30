"""Build one filer's calendar from the period ends it actually filed.

EDGAR reports a fiscalYearEnd field and it is not enough: it holds one value, so
for a 52/53-week filer it names whichever date the most recent year landed on, and
for a filer that changed its year end it names only where it ended up.
"""

# region Imports
from __future__ import annotations

from datetime import date, timedelta

from constants import (
    FISCAL_YEAR_MAX_DAYS,
)
from reference.calendar.models import CalendarType, FilerCalendar, FiscalQuarter
from reference.calendar.shapes import (
    _conforms,
    _different_regime,
    _split_regimes,
    classify,
)

# endregion

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
