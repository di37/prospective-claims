"""Section 6 applied to synthetic filing calendars.

Every fixture here is invented. The point of these tests is that a status comes
from the calendar and never from whether a fact exists, so a test that reached
for a real filing would be testing the wrong thing.

The four branches are the ones the manual distinguishes and the pilot reports
separately: observable, an immature window, a filing that has not arrived, and a
filer that is overdue. They are different situations and collapsing any two of
them would hide something the censoring report is meant to show.
"""

# region Imports
from __future__ import annotations

from datetime import date

import pytest

from adjudication import (
    CensoringReason,
    FiledReport,
    ObservationStatus,
    RequiredReport,
    censoring_rates,
    first_covering_filings,
    observe,
)

# endregion

# region Fixtures
def required(*periods: tuple[str, str]) -> tuple[RequiredReport, ...]:
    """Build the reports a window needs from period end and form pairs."""
    return tuple(
        RequiredReport(period_end=date.fromisoformat(d), form=f) for d, f in periods
    )


def filed(*reports: tuple[str, str, str]) -> dict[date, FiledReport]:
    """Build covering filings from period end, form and filing date triples."""
    return first_covering_filings(
        FiledReport(
            period_end=date.fromisoformat(p), form=f, filed_date=date.fromisoformat(d)
        )
        for p, f, d in reports
    )


CUTOFF = date(2024, 6, 30)


@pytest.fixture
def two_quarter_window() -> tuple[RequiredReport, ...]:
    """A window spanning two ordinary quarters, both well inside the cutoff."""
    return required(("2023-09-30", "10-Q"), ("2023-12-31", "10-K"))


# endregion

# region Observable
def test_observable_when_window_closed_and_filings_published(two_quarter_window):
    """Both conditions hold, so the claim can be adjudicated."""
    filings = filed(
        ("2023-09-30", "10-Q", "2023-11-02"),
        ("2023-12-31", "10-K", "2024-02-15"),
    )
    result = observe(two_quarter_window, filings, CUTOFF)
    assert result.status is ObservationStatus.OBSERVABLE, result.censoring_reason
    assert result.censoring_reason is None


def test_maturity_is_the_latest_filing_not_the_earliest(two_quarter_window):
    """M(c) is a maximum: the window is settled only once its last report lands."""
    filings = filed(
        ("2023-09-30", "10-Q", "2023-11-02"),
        ("2023-12-31", "10-K", "2024-02-15"),
    )
    result = observe(two_quarter_window, filings, CUTOFF)
    assert result.maturity_date == date(2024, 2, 15), (
        f"maturity should be the later of the two filings, got {result.maturity_date}"
    )


def test_maturity_ignores_statutory_deadlines(two_quarter_window):
    """A filer who files early matures early; the deadline is not a stand-in."""
    filings = filed(
        ("2023-09-30", "10-Q", "2023-10-11"),
        ("2023-12-31", "10-K", "2024-01-19"),
    )
    result = observe(two_quarter_window, filings, CUTOFF)
    assert result.maturity_date == date(2024, 1, 19), (
        "maturity must come from the actual filing date, not period end plus a deadline"
    )


# endregion

# region The three censoring reasons
def test_immature_window_is_censored_before_filings_are_considered():
    """A window that has not closed cannot be settled, whatever has been filed."""
    window = required(("2024-09-30", "10-Q"))
    result = observe(window, filed(("2024-09-30", "10-Q", "2024-06-01")), CUTOFF)
    assert result.status is ObservationStatus.RIGHT_CENSORED
    assert result.censoring_reason is CensoringReason.IMMATURE_WINDOW, (
        f"a window ending after the cutoff is immature, got {result.censoring_reason}"
    )
    assert result.maturity_date is None


def test_awaiting_filing_when_the_report_is_late_but_not_overdue():
    """The window closed and the report has not arrived, but its deadline has not passed."""
    window = required(("2024-06-15", "10-Q"))
    result = observe(window, {}, CUTOFF)
    assert result.censoring_reason is CensoringReason.AWAITING_FILING, (
        f"a 10-Q 15 days past period end is pending, not overdue, got {result.censoring_reason}"
    )
    assert result.delinquent_filer is False
    assert result.maturity_date is None, "M(c) is undefined when a report is missing"
    assert result.missing_periods == (date(2024, 6, 15),)


def test_delinquent_filer_when_the_deadline_has_passed():
    """A 10-Q unfiled 40 days after period end is overdue, which is its own case."""
    window = required(("2024-01-31", "10-Q"))
    result = observe(window, {}, CUTOFF)
    assert result.censoring_reason is CensoringReason.DELINQUENT_FILER, (
        f"a 10-Q five months past period end is overdue, got {result.censoring_reason}"
    )
    assert result.delinquent_filer is True
    assert result.maturity_date is None


def test_awaiting_filing_when_the_report_arrives_after_the_cutoff():
    """A filing that exists but lands past T does not make the claim observable."""
    window = required(("2024-05-31", "10-Q"))
    filings = filed(("2024-05-31", "10-Q", "2024-07-09"))
    result = observe(window, filings, CUTOFF)
    assert result.status is ObservationStatus.RIGHT_CENSORED
    assert result.censoring_reason is CensoringReason.AWAITING_FILING
    assert result.maturity_date == date(2024, 7, 9), (
        "M(c) is defined here: the report exists, it is simply later than the cutoff"
    )


def test_a_10k_gets_the_longer_deadline():
    """60 days for an annual report against 40 for a quarterly one."""
    fifty_days = date(2024, 5, 11)
    assert (fifty_days - date(2024, 3, 22)).days == 50
    quarterly = observe(required(("2024-03-22", "10-Q")), {}, fifty_days)
    annual = observe(required(("2024-03-22", "10-K")), {}, fifty_days)
    assert quarterly.censoring_reason is CensoringReason.DELINQUENT_FILER, (
        "a 10-Q is overdue 50 days after period end"
    )
    assert annual.censoring_reason is CensoringReason.AWAITING_FILING, (
        "a 10-K is not overdue until 60 days after period end"
    )


def test_one_overdue_report_makes_the_window_delinquent():
    """A window is only as settled as its worst report."""
    window = required(("2023-03-31", "10-Q"), ("2024-06-20", "10-Q"))
    result = observe(window, {}, CUTOFF)
    assert result.delinquent_filer is True, (
        "the 2023 report is long overdue even though the 2024 one is merely pending"
    )
    assert result.missing_periods == (date(2023, 3, 31), date(2024, 6, 20))


# endregion

# region Unresolved windows
def test_an_unresolved_window_is_not_applicable():
    """No window means no status, rather than a guessed one."""
    result = observe((), {}, CUTOFF)
    assert result.status is ObservationStatus.NOT_APPLICABLE
    assert result.censoring_reason is None, (
        "an unresolved window is not censored; it is a different exclusion"
    )
    assert result.maturity_date is None


# endregion

# region Amendments
def test_an_amendment_never_displaces_the_original():
    """A 10-Q/A after the cutoff must not un-observe a claim the original settled."""
    window = required(("2023-12-31", "10-Q"))
    filings = filed(
        ("2023-12-31", "10-Q", "2024-02-01"),
        ("2023-12-31", "10-Q/A", "2024-08-14"),
    )
    assert filings[date(2023, 12, 31)].form == "10-Q", "the amendment should be dropped"
    result = observe(window, filings, CUTOFF)
    assert result.status is ObservationStatus.OBSERVABLE
    assert result.maturity_date == date(2024, 2, 1)


def test_the_earliest_filing_wins_when_a_period_is_filed_twice():
    """Where a period was filed more than once, availability starts at the first."""
    filings = filed(
        ("2023-12-31", "10-K", "2024-03-01"),
        ("2023-12-31", "10-K", "2024-02-15"),
    )
    assert filings[date(2023, 12, 31)].filed_date == date(2024, 2, 15)


def test_an_amendment_alone_leaves_the_period_uncovered():
    """Dropping amendments must not silently invent coverage from one."""
    filings = filed(("2023-12-31", "10-Q/A", "2024-02-01"))
    assert filings == {}
    result = observe(required(("2023-12-31", "10-Q")), filings, CUTOFF)
    assert result.status is ObservationStatus.RIGHT_CENSORED
    assert result.missing_periods == (date(2023, 12, 31),)


# endregion

# region Nothing here reads evidence
def test_status_does_not_depend_on_any_fact_existing():
    """Two claims with identical calendars get identical statuses.

    This is the circularity section 6 removes. The function takes no evidence
    argument at all, so a claim whose figure is absent and one whose figure is
    tagged in XBRL cannot be told apart here, which is exactly the intent.
    """
    window = required(("2023-12-31", "10-K"))
    filings = filed(("2023-12-31", "10-K", "2024-02-15"))
    assert observe(window, filings, CUTOFF) == observe(window, filings, CUTOFF)


# endregion

# region Censoring report
def test_censoring_rates_split_by_reason():
    """The pilot reports the rate and its reasons, not one number."""
    window = required(("2023-12-31", "10-K"))
    filings = filed(("2023-12-31", "10-K", "2024-02-15"))
    observations = [
        observe(window, filings, CUTOFF),
        observe(required(("2024-09-30", "10-Q")), {}, CUTOFF),
        observe(required(("2024-01-31", "10-Q")), {}, CUTOFF),
        observe((), {}, CUTOFF),
    ]
    rates = censoring_rates(observations)
    assert rates.claims == 4
    assert rates.observable == 1
    assert rates.censored == 2
    assert rates.not_applicable == 1
    assert rates.by_reason == {"immature_window": 1, "delinquent_filer": 1}
    assert rates.censoring_rate == pytest.approx(2 / 3), (
        "not-applicable claims are excluded from the denominator, so the rate is 2 of 3"
    )


def test_censoring_rate_is_none_when_nothing_has_a_status():
    """A set of only unresolved windows has no rate to report."""
    rates = censoring_rates([observe((), {}, CUTOFF)])
    assert rates.censoring_rate is None
    assert rates.not_applicable == 1


# endregion
