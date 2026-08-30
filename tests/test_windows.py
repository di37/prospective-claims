"""Section 5.5 resolved against calendars that do not match the calendar year.

Every fixture here is synthetic. Real filer calendars are in
``reference/fiscal_quarters.csv``, and testing against them would mean a test
that fails when the SEC reissues a filing rather than when the logic breaks.

The five shapes are the ones that actually occur: a December year end that
matches the calendar, a January year end where "next year" lands eleven months
before the calendar year of the same name, a June year end, a 52/53-week retail
calendar with the 53rd week inserted, and a retailer whose quarters are unequal.
Between them they cover the cases the manual calls a known source of label noise.

Each fixture is modelled on a real shape in ``reference/fiscal_quarters.csv`` and
then written out by hand, so a test fails when the logic breaks rather than when
the SEC reissues a filing.
"""

# region Imports
from __future__ import annotations

from datetime import date

import pytest

from resolution import Anchor, FiscalCalendar, Phrase, Quarter, WindowProvenance, resolve

# endregion

# region Fixtures
def calendar(*ends: tuple[int, int, str]) -> FiscalCalendar:
    """Build a calendar from fiscal year, quarter and period end triples.

    Args:
        ends: Triples of fiscal year, quarter, and ISO period end.

    Returns:
        The calendar.
    """
    return FiscalCalendar(
        quarters=tuple(
            Quarter(fiscal_year=y, quarter=q, period_end=date.fromisoformat(d))
            for y, q, d in ends
        )
    )


@pytest.fixture
def december() -> FiscalCalendar:
    """A December year end, where fiscal and calendar quarters coincide."""
    return calendar(
        (2023, 1, "2023-03-31"), (2023, 2, "2023-06-30"),
        (2023, 3, "2023-09-30"), (2023, 4, "2023-12-31"),
        (2024, 1, "2024-03-31"), (2024, 2, "2024-06-30"),
        (2024, 3, "2024-09-30"), (2024, 4, "2024-12-31"),
    )


@pytest.fixture
def january() -> FiscalCalendar:
    """A January year end, the retailer shape. Fiscal 2024 ends 2024-01-31."""
    return calendar(
        (2024, 1, "2023-04-30"), (2024, 2, "2023-07-31"),
        (2024, 3, "2023-10-31"), (2024, 4, "2024-01-31"),
        (2025, 1, "2024-04-30"), (2025, 2, "2024-07-31"),
        (2025, 3, "2024-10-31"), (2025, 4, "2025-01-31"),
    )


@pytest.fixture
def june() -> FiscalCalendar:
    """A June year end. Fiscal 2023 starts in July 2022."""
    return calendar(
        (2023, 1, "2022-09-30"), (2023, 2, "2022-12-31"),
        (2023, 3, "2023-03-31"), (2023, 4, "2023-06-30"),
        (2024, 1, "2023-09-30"), (2024, 2, "2023-12-31"),
        (2024, 3, "2024-03-31"), (2024, 4, "2024-06-30"),
    )


@pytest.fixture
def retail_53_week() -> FiscalCalendar:
    """A 52/53-week calendar ending the Saturday nearest 31 January.

    Fiscal 2023 is 52 weeks and ends 2023-01-28. Fiscal 2024 is 53 weeks and ends
    2024-02-03, with the extra week added to the fourth quarter. Target and Best
    Buy both ran exactly this calendar, quarter for quarter.
    """
    return calendar(
        (2023, 1, "2022-04-30"), (2023, 2, "2022-07-30"),
        (2023, 3, "2022-10-29"), (2023, 4, "2023-01-28"),
        (2024, 1, "2023-04-29"), (2024, 2, "2023-07-29"),
        (2024, 3, "2023-10-28"), (2024, 4, "2024-02-03"),
    )


@pytest.fixture
def uneven_quarters() -> FiscalCalendar:
    """A retailer whose quarters are not the same length.

    Kroger runs a sixteen-week first quarter and three twelve-week quarters, so
    the year is still 52 weeks and no quarter is a quarter of it. Any code that
    places a window by counting days from the start of the year lands in the
    wrong quarter for this filer, which is why the resolver counts quarters and
    reads their period ends instead.
    """
    return calendar(
        (2023, 1, "2022-05-21"), (2023, 2, "2022-08-13"),
        (2023, 3, "2022-11-05"), (2023, 4, "2023-01-28"),
        (2024, 1, "2023-05-20"), (2024, 2, "2023-08-12"),
        (2024, 3, "2023-11-04"), (2024, 4, "2024-02-03"),
    )


# endregion

# region Next quarter, across all five shapes
@pytest.mark.parametrize(
    ("shape", "t", "expected"),
    [
        ("december", 0, "2023-06-30"),
        ("january", 0, "2023-07-31"),
        ("june", 0, "2022-12-31"),
        ("retail_53_week", 0, "2022-07-30"),
        ("uneven_quarters", 0, "2022-08-13"),
        # From the third quarter, "next quarter" is the one that closes the year,
        # and in the 53-week calendar that quarter is fourteen weeks long.
        ("december", 2, "2023-12-31"),
        ("january", 2, "2024-01-31"),
        ("june", 2, "2023-06-30"),
        ("retail_53_week", 6, "2024-02-03"),
        ("uneven_quarters", 6, "2024-02-03"),
    ],
)
def test_next_quarter(shape, t, expected, request):
    """Next quarter lands on the filer's own quarter end, not the calendar's."""
    cal = request.getfixturevalue(shape)
    window = resolve(Phrase.NEXT_QUARTER, t, cal)
    assert window.resolved, f"next quarter from {shape} t={t} did not resolve: {window.reason}"
    assert window.offsets == (1, 1), f"next quarter should be [t+1, t+1], got {window.offsets}"
    assert window.period_ends == (date.fromisoformat(expected),), (
        f"next quarter from {shape} t={t} should end {expected}, "
        f"got {[str(d) for d in window.period_ends]}"
    )


def test_next_quarter_is_not_the_calendar_quarter(january):
    """A January filer in its third quarter points at January, not December."""
    window = resolve(Phrase.NEXT_QUARTER, 2, january)
    assert window.period_ends == (date(2024, 1, 31),), (
        "next quarter for a January year end should be the fiscal fourth quarter "
        f"ending 2024-01-31, got {[str(d) for d in window.period_ends]}"
    )


# endregion

# region The rest of the window table
@pytest.mark.parametrize("phrase", [Phrase.NEXT_TWO_QUARTERS, Phrase.FIRST_HALF])
def test_two_quarter_phrases(phrase, december):
    """Both phrases the manual assigns [t+1, t+2] produce two quarters."""
    window = resolve(phrase, 0, december)
    assert window.offsets == (1, 2), f"{phrase.value} should be [t+1, t+2], got {window.offsets}"
    assert window.period_ends == (date(2023, 6, 30), date(2023, 9, 30)), (
        f"{phrase.value} from 2023Q1 should cover Q2 and Q3, "
        f"got {[str(d) for d in window.period_ends]}"
    )


@pytest.mark.parametrize(
    ("t", "offsets", "ends"),
    [
        (0, (1, 3), ["2023-06-30", "2023-09-30", "2023-12-31"]),
        (1, (1, 2), ["2023-09-30", "2023-12-31"]),
        (2, (1, 1), ["2023-12-31"]),
    ],
)
def test_this_year_covers_the_remaining_quarters(t, offsets, ends, december):
    """"This year" shortens as the fiscal year runs down."""
    window = resolve(Phrase.THIS_YEAR, t, december)
    assert window.offsets == offsets, (
        f"this year from t={t} should be {offsets}, got {window.offsets}"
    )
    assert [str(d) for d in window.period_ends] == ends, (
        f"this year from t={t} should cover {ends}, got {[str(d) for d in window.period_ends]}"
    )


def test_next_year_is_the_four_quarters_of_the_following_fiscal_year(january):
    """For a January filer, "next year" ends in January, not December."""
    window = resolve(Phrase.NEXT_YEAR, 0, january)
    assert window.offsets == (4, 7), f"next year from Q1 should be [t+4, t+7], got {window.offsets}"
    assert [str(d) for d in window.period_ends] == [
        "2024-04-30", "2024-07-31", "2024-10-31", "2025-01-31"
    ], (
        "next year for a January year end should be fiscal 2025, ending 2025-01-31, "
        f"got {[str(d) for d in window.period_ends]}"
    )


def test_next_year_from_the_final_quarter_is_the_next_four(december):
    """Said in the last quarter of a year, "next year" starts immediately."""
    window = resolve(Phrase.NEXT_YEAR, 3, december)
    assert window.offsets == (1, 4), f"next year from Q4 should be [t+1, t+4], got {window.offsets}"
    assert [str(d) for d in window.period_ends] == [
        "2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"
    ]


@pytest.mark.parametrize(
    ("t", "offsets", "ends"),
    [
        (0, (2, 3), ["2023-09-30", "2023-12-31"]),
        (1, (1, 2), ["2023-09-30", "2023-12-31"]),
    ],
)
def test_second_half_is_the_same_two_quarters_whenever_it_is_said(t, offsets, ends, december):
    """"Second half" names quarters of the fiscal year, so the offsets move but the quarters do not."""
    window = resolve(Phrase.SECOND_HALF, t, december)
    assert window.offsets == offsets, (
        f"second half from t={t} should be {offsets}, got {window.offsets}"
    )
    assert [str(d) for d in window.period_ends] == ends, (
        f"second half from t={t} should cover {ends}, got {[str(d) for d in window.period_ends]}"
    )


# endregion

# region What stays unresolved
@pytest.mark.parametrize("phrase", [Phrase.VAGUE, Phrase.ABSENT])
def test_vague_and_absent_never_default(phrase, december):
    """Section 5.5 marks these UNRESOLVED, and they must not fall back to next quarter."""
    window = resolve(phrase, 0, december)
    assert not window.resolved, f"{phrase.value} resolved to {window.offsets}; it must not"
    assert window.provenance is WindowProvenance.UNRESOLVED, (
        f"{phrase.value} should carry UNRESOLVED, got {window.provenance.value}"
    )
    assert window.period_ends == (), f"{phrase.value} should name no period, got {window.period_ends}"
    assert "never defaulted" in (window.reason or ""), (
        f"{phrase.value} should say why it is not defaulted, got {window.reason!r}"
    )


def test_this_year_in_the_final_quarter_is_unresolved(december):
    """Said in the fourth quarter, "this year" names no quarter that is still ahead."""
    window = resolve(Phrase.THIS_YEAR, 3, december)
    assert not window.resolved, (
        f"this year from the final quarter resolved to {window.offsets}; no quarters remain"
    )
    assert "last of its fiscal year" in (window.reason or ""), window.reason


@pytest.mark.parametrize("t", [2, 3])
def test_second_half_said_during_the_second_half_is_unresolved(t, december):
    """The manual assigns no window to a half that has already started."""
    window = resolve(Phrase.SECOND_HALF, t, december)
    assert not window.resolved, (
        f"second half from t={t} resolved to {window.offsets}; that half is already under way"
    )
    assert "already in the second half" in (window.reason or ""), window.reason


def test_a_window_past_the_end_of_the_calendar_is_unresolved(december):
    """A window needs quarters to point at, and the calendar is finite."""
    window = resolve(Phrase.NEXT_YEAR, 7, december)
    assert not window.resolved, (
        f"next year from the last known quarter resolved to {window.offsets}"
    )
    assert "past the end" in (window.reason or ""), window.reason


def test_a_claim_quarter_outside_the_calendar_is_unresolved(december):
    """An index that names no quarter cannot produce a window."""
    window = resolve(Phrase.NEXT_QUARTER, 99, december)
    assert not window.resolved
    assert "outside the calendar" in (window.reason or ""), window.reason


# endregion

# region Where t sits
@pytest.mark.parametrize(
    ("anchor", "expected_index"),
    [(Anchor.CALL_QUARTER, 3), (Anchor.REPORTED_QUARTER, 2)],
)
def test_the_two_readings_of_t_differ_by_one(anchor, expected_index, december):
    """A call held in the fourth quarter reports the third, and the manual names both.

    Section 4.1 says the window is relative to "the claim quarter" and section 4.1
    prose says "the quarter of the call". For any real earnings call those differ
    by exactly one, so the reading is a decision the manual has to make.
    """
    call = date(2023, 11, 2)
    assert december.claim_quarter(call, anchor) == expected_index, (
        f"a call on {call} under {anchor.value} should anchor at index {expected_index}"
    )


def test_the_anchor_changes_which_quarter_next_quarter_means(december):
    """The same call and phrase land on different quarters under each reading."""
    call = date(2023, 11, 2)
    on_call = resolve(Phrase.NEXT_QUARTER, december.claim_quarter(call, Anchor.CALL_QUARTER), december)
    on_report = resolve(
        Phrase.NEXT_QUARTER, december.claim_quarter(call, Anchor.REPORTED_QUARTER), december
    )
    assert on_call.period_ends == (date(2024, 3, 31),)
    assert on_report.period_ends == (date(2023, 12, 31),)
    assert on_call.period_ends != on_report.period_ends, (
        "the two readings must differ, or the ambiguity would not matter"
    )


def test_a_date_before_the_calendar_starts_has_no_claim_quarter(december):
    """A call outside the known calendar anchors nowhere rather than at zero."""
    assert december.claim_quarter(date(2019, 1, 1), Anchor.CALL_QUARTER) is None
    assert december.claim_quarter(date(2023, 1, 15), Anchor.REPORTED_QUARTER) is None


# endregion

# region Calendar validation
def test_a_calendar_that_skips_a_quarter_is_rejected():
    """A gap would make t+2 mean two filed quarters rather than two elapsed ones."""
    with pytest.raises(ValueError, match="skips a quarter"):
        calendar((2023, 1, "2023-03-31"), (2023, 3, "2023-09-30"))


def test_a_calendar_out_of_order_is_rejected():
    """Quarters are indexed by position, so order is not cosmetic."""
    with pytest.raises(ValueError, match="out of order"):
        calendar((2023, 2, "2023-06-30"), (2023, 3, "2023-03-31"))


def test_uneven_quarters_are_not_placed_by_counting_days(uneven_quarters):
    """A window spans whole quarters however unequal they are.

    The first quarter here is sixteen weeks and the rest are twelve, so the two
    quarters after Q1 span 168 days while the two after Q4 span 196, because the
    second pair contains the long quarter. Both are still [t+1, t+2].
    """
    early = resolve(Phrase.NEXT_TWO_QUARTERS, 0, uneven_quarters)
    late = resolve(Phrase.NEXT_TWO_QUARTERS, 3, uneven_quarters)
    assert early.offsets == late.offsets == (1, 2)
    assert [str(d) for d in early.period_ends] == ["2022-08-13", "2022-11-05"], (
        f"next two quarters from the sixteen-week Q1 should end 2022-08-13 and "
        f"2022-11-05, got {[str(d) for d in early.period_ends]}"
    )
    assert [str(d) for d in late.period_ends] == ["2023-05-20", "2023-08-12"], (
        f"next two quarters from Q4 should end 2023-05-20 and 2023-08-12, "
        f"got {[str(d) for d in late.period_ends]}"
    )
    spans = [
        (early.period_ends[1] - uneven_quarters.quarters[0].period_end).days,
        (late.period_ends[1] - uneven_quarters.quarters[3].period_end).days,
    ]
    assert spans == [168, 196], (
        f"two quarters should span 168 days after Q1 and 196 after Q4, got {spans}"
    )


def test_the_53_week_year_is_seven_days_longer(retail_53_week):
    """The fixture is a real 53-week year, not four even quarters."""
    ends = [q.period_end for q in retail_53_week.quarters]
    assert (ends[7] - ends[3]).days == 371, (
        f"fiscal 2024 should span 371 days, got {(ends[7] - ends[3]).days}"
    )
    assert (ends[7] - ends[6]).days == 98, (
        f"the extra week belongs to the fourth quarter, got {(ends[7] - ends[6]).days} days"
    )


# endregion
