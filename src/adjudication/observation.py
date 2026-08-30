"""Decide whether a claim can be checked yet, without looking at any evidence.

Section 6 defines observability on the evidence maturity date ``M(c)``: the latest
filing date among the periodic reports covering the claim's evaluation window. A
claim is OBSERVABLE when its window has closed and those reports have been
published, both by the evidence cutoff ``T``.

The rule is deliberately independent of whether the adjudicating fact exists, and
that independence is the whole point. A claim whose evidence turns out to be
ABSENT has no fact whose publication date could be inspected, and a claim
resolving to a non-GAAP measure has no XBRL fact at all. Deciding observability by
first locating the evidence would make the test depend on the thing it gates.
Nothing in this module reads a value; it reads a calendar.

Filing dates are actual EDGAR dates. Statutory deadlines appear once, to decide
whether a report that never arrived is overdue rather than merely pending, and
never to stand in for a filing date.

The window arrives here as concrete period ends rather than as offsets from the
claim quarter. That keeps one open question out of this module: the manual calls
the window relative to "the claim quarter" in one line and "the quarter of the
call" in the next, and those differ by one for every earnings call. Resolving that
is ``src/resolution``'s problem, and by the time a window reaches this function it
has already been settled.
"""

# region Imports
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from constants import STATUTORY_DEADLINE_DAYS

# endregion

# region Vocabulary
class ObservationStatus(str, Enum):
    """Whether a claim can be adjudicated yet."""

    OBSERVABLE = "OBSERVABLE"
    RIGHT_CENSORED = "RIGHT_CENSORED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CensoringReason(str, Enum):
    """Why a claim is not observable.

    These are reported separately because they say different things. An immature
    window is a property of the study's cutoff and would resolve itself given
    time. A late filing is a property of this filer's behaviour. A delinquent
    filer is a property the study treats as its own case, since the report may
    never arrive.
    """

    IMMATURE_WINDOW = "immature_window"
    AWAITING_FILING = "awaiting_filing"
    DELINQUENT_FILER = "delinquent_filer"


# endregion

# region Models
class RequiredReport(BaseModel):
    """A periodic report the window needs in order to be settled.

    Attributes:
        period_end: The fiscal period the report covers.
        form: ``10-K`` for a fiscal year end, ``10-Q`` otherwise. The 10-K
            replaces the fourth 10-Q, so a window ending on a year end requires
            the annual report rather than a quarterly one.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period_end: date
    form: str


class FiledReport(BaseModel):
    """A report that was actually filed, as ``filing_dates.csv`` records it.

    Attributes:
        period_end: The fiscal period covered.
        form: Form type as filed.
        filed_date: When it reached the SEC. This, never a deadline, is what the
            maturity date is built from.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period_end: date
    form: str
    filed_date: date


class Observation(BaseModel):
    """The computed status of one claim, with the evidence for it.

    Attributes:
        status: OBSERVABLE, RIGHT_CENSORED, or NOT_APPLICABLE.
        maturity_date: ``M(c)``, the latest filing date among the covering
            reports. None when a required report is missing, which is what the
            manual means by ``M(c)`` being undefined.
        censoring_reason: Why it is censored, when it is.
        delinquent_filer: Whether a required report is both missing and overdue.
        window_end: The last period the window covers.
        missing_periods: Periods with no covering filing, earliest first.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: ObservationStatus
    maturity_date: date | None = None
    censoring_reason: CensoringReason | None = None
    delinquent_filer: bool = False
    window_end: date | None = None
    missing_periods: tuple[date, ...] = ()


class CensoringRates(BaseModel):
    """The censoring rate, split by the reason claims were censored.

    Attributes:
        claims: How many claims were assigned a status.
        observable: How many are adjudicable.
        censored: How many are right-censored.
        not_applicable: How many have no resolved window.
        by_reason: Censored counts per reason.
        censoring_rate: Censored over claims with a status, so the
            not-applicable claims are excluded from the denominator rather than
            counted as censored. They are a different failure.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    claims: int = Field(ge=0)
    observable: int = Field(ge=0)
    censored: int = Field(ge=0)
    not_applicable: int = Field(ge=0)
    by_reason: dict[str, int]
    censoring_rate: float | None = None


# endregion

# region Covering filings
def first_covering_filings(filings: Iterable[FiledReport]) -> dict[date, FiledReport]:
    """Reduce a filer's reports to one per period: the first that covered it.

    Amendments are dropped rather than ranked. A 10-Q/A published after the cutoff
    does not make a claim observable, while the original that arrived on time
    does, so an amendment must never displace the filing that settled the period.
    Where a period was filed more than once without an amendment, the earliest
    wins, because that is when the information became available.

    Args:
        filings: A filer's reports, any order.

    Returns:
        The covering filing for each period.
    """
    covering: dict[date, FiledReport] = {}
    for filing in filings:
        if filing.form.endswith("/A"):
            continue
        held = covering.get(filing.period_end)
        if held is None or filing.filed_date < held.filed_date:
            covering[filing.period_end] = filing
    return covering


def _is_overdue(report: RequiredReport, cutoff: date) -> bool:
    """Check whether a missing report has passed its filing deadline.

    Args:
        report: The report that has not arrived.
        cutoff: The evidence cutoff.

    Returns:
        True when the deadline fell on or before the cutoff.
    """
    allowed = STATUTORY_DEADLINE_DAYS.get(report.form)
    if allowed is None:
        return False
    return report.period_end + timedelta(days=allowed) <= cutoff


# endregion

# region The rule
def observe(
    required: Sequence[RequiredReport],
    filings: Mapping[date, FiledReport],
    cutoff: date,
) -> Observation:
    """Assign observation status to one resolved claim.

    Args:
        required: The reports covering the claim's window, in any order. Empty
            means the window is UNRESOLVED.
        filings: Covering filings by period, from ``first_covering_filings``.
        cutoff: The evidence cutoff ``T``.

    Returns:
        The status, with the maturity date when one is defined and the reason
        when it is censored.
    """
    if not required:
        return Observation(status=ObservationStatus.NOT_APPLICABLE)

    window_end = max(report.period_end for report in required)

    # The window has to have closed before any report covering it can exist.
    # Checking this first keeps the two censoring reasons apart: a window still
    # open is not the same as a filing that has not arrived.
    if window_end > cutoff:
        return Observation(
            status=ObservationStatus.RIGHT_CENSORED,
            censoring_reason=CensoringReason.IMMATURE_WINDOW,
            window_end=window_end,
        )

    missing = sorted(r.period_end for r in required if r.period_end not in filings)
    if missing:
        overdue = any(_is_overdue(r, cutoff) for r in required if r.period_end in missing)
        return Observation(
            status=ObservationStatus.RIGHT_CENSORED,
            censoring_reason=(
                CensoringReason.DELINQUENT_FILER if overdue else CensoringReason.AWAITING_FILING
            ),
            delinquent_filer=overdue,
            window_end=window_end,
            missing_periods=tuple(missing),
        )

    maturity = max(filings[r.period_end].filed_date for r in required)
    if maturity > cutoff:
        return Observation(
            status=ObservationStatus.RIGHT_CENSORED,
            maturity_date=maturity,
            censoring_reason=CensoringReason.AWAITING_FILING,
            window_end=window_end,
        )

    return Observation(
        status=ObservationStatus.OBSERVABLE,
        maturity_date=maturity,
        window_end=window_end,
    )


# endregion

# region Reporting
def censoring_rates(observations: Iterable[Observation]) -> CensoringRates:
    """Summarise a set of observations for the pilot's censoring report.

    Args:
        observations: One per claim.

    Returns:
        Counts by status and by censoring reason, with the rate.
    """
    items = list(observations)
    statuses = Counter(o.status for o in items)
    reasons = Counter(o.censoring_reason.value for o in items if o.censoring_reason)

    observable = statuses[ObservationStatus.OBSERVABLE]
    censored = statuses[ObservationStatus.RIGHT_CENSORED]
    with_status = observable + censored
    return CensoringRates(
        claims=len(items),
        observable=observable,
        censored=censored,
        not_applicable=statuses[ObservationStatus.NOT_APPLICABLE],
        by_reason=dict(reasons),
        censoring_rate=(censored / with_status) if with_status else None,
    )


# endregion
