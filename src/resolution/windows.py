"""Resolve a temporal phrase onto a filer's own fiscal quarters.

Section 5.5 of the annotation guidelines maps a phrase like "next quarter" onto
an evaluation window, and does it against the filer's fiscal calendar rather than
the calendar year. A retailer whose year ends in January means something different
by "next year" than a filer whose year ends in December, and the difference is
never visible as an error: the claim is simply scored against the wrong quarter.

This module does the decidable half of that. It maps a phrase the manual already
names onto a window and then onto concrete period ends. Recognising an arbitrary
paraphrase as one of those phrases is the model's job and one of the study's
research questions; nothing here guesses at language.

Two rules from the manual are enforced rather than left to the caller. A phrase
the manual does not cover resolves to UNRESOLVED, never to next quarter, because
defaulting the window would manufacture easy labels for the capability under
test. And a window that does not lie strictly ahead of the claim quarter is
UNRESOLVED too: "the second half" said during the second half is a case section 5
does not cover, and section 5 says to log the gap rather than invent a rule.

Where ``t`` sits is a parameter rather than a decision taken here. The manual says
the window is relative to "the quarter of the call" in one place and "the claim
quarter" in another, and those differ by one for every earnings call ever held: a
call reporting the third quarter happens during the fourth. Both readings are
implemented, both are tested, and the choice belongs in the manual.
"""

# region Imports
from __future__ import annotations

from datetime import date, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# endregion

# region Vocabulary
class Phrase(str, Enum):
    """The temporal phrases section 5.5 assigns a window to.

    ``VAGUE`` covers "over time", "longer term", "in the coming years" and
    "eventually"; ``ABSENT`` is a claim with no temporal expression at all. Both
    resolve to UNRESOLVED, and they are kept apart because the rate of each says
    something different about how management talks.
    """

    NEXT_QUARTER = "next_quarter"
    NEXT_TWO_QUARTERS = "next_two_quarters"
    FIRST_HALF = "first_half"
    THIS_YEAR = "this_year"
    NEXT_YEAR = "next_year"
    SECOND_HALF = "second_half"
    VAGUE = "vague"
    ABSENT = "absent"


class WindowProvenance(str, Enum):
    """The four-way refinement section 4.2 applies to ``w``."""

    EXPLICIT = "EXPLICIT"
    CONTEXT_INFERRED = "CONTEXT_INFERRED"
    POLICY_DEFAULT = "POLICY_DEFAULT"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Anchor(str, Enum):
    """Which fiscal quarter ``t`` denotes.

    ``CALL_QUARTER`` reads "the quarter of the call" literally: t is the quarter
    the call date falls inside. ``REPORTED_QUARTER`` reads "the claim quarter" as
    the quarter being reported on, which is the one that has just closed. They
    differ by exactly one, always, so the reading changes every window in the
    study.
    """

    CALL_QUARTER = "call_quarter"
    REPORTED_QUARTER = "reported_quarter"


# endregion

# region Calendar
class Quarter(BaseModel):
    """One fiscal quarter of one filer.

    Attributes:
        fiscal_year: The year the fiscal year ends in.
        quarter: 1 to 4.
        period_end: Last day of the quarter.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    fiscal_year: int
    quarter: int = Field(ge=1, le=4)
    period_end: date


class FiscalCalendar(BaseModel):
    """One filer's quarters in order, which is all a window needs.

    Attributes:
        quarters: Every known quarter, earliest first and contiguous. A gap would
            make ``t+2`` mean two filed quarters rather than two elapsed ones, so
            the constructor rejects one rather than resolving against it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    quarters: tuple[Quarter, ...]

    def model_post_init(self, _context: object) -> None:
        """Check the quarters are ordered and contiguous.

        Args:
            _context: Unused pydantic hook argument.

        Returns:
            None.

        Raises:
            ValueError: If the quarters are out of order or skip one.
        """
        for earlier, later in zip(self.quarters, self.quarters[1:]):
            if later.period_end <= earlier.period_end:
                raise ValueError(f"quarters out of order at {later.period_end}")
            expected = (earlier.fiscal_year + 1, 1) if earlier.quarter == 4 else (earlier.fiscal_year, earlier.quarter + 1)
            if (later.fiscal_year, later.quarter) != expected:
                raise ValueError(
                    f"calendar skips a quarter: {earlier.fiscal_year}Q{earlier.quarter} "
                    f"is followed by {later.fiscal_year}Q{later.quarter}"
                )

    def _opens_after(self, i: int) -> date | None:
        """Return the day a quarter opens after, which bounds it below.

        Every quarter but the first opens the day after its predecessor closes.
        The first has no predecessor, so its span is taken from its neighbour:
        quarters within a calendar are the same length to within a week, and
        without some lower bound every date in history would fall inside it.

        Args:
            i: Index of the quarter.

        Returns:
            The bounding day, or None for a calendar of one quarter, where there
            is nothing to infer a span from.
        """
        if i > 0:
            return self.quarters[i - 1].period_end
        if len(self.quarters) < 2:
            return None
        span = (self.quarters[1].period_end - self.quarters[0].period_end).days
        return self.quarters[0].period_end - timedelta(days=span)

    def index_containing(self, day: date) -> int | None:
        """Find the quarter a date falls inside.

        Args:
            day: The date to place.

        Returns:
            Index into ``quarters``, or None when the date is outside the
            calendar entirely.
        """
        for i, quarter in enumerate(self.quarters):
            opens_after = self._opens_after(i)
            if opens_after is None:
                continue
            if opens_after < day <= quarter.period_end:
                return i
        return None

    def claim_quarter(self, call_date: date, anchor: Anchor) -> int | None:
        """Find the index of ``t`` for a call on a given day.

        Args:
            call_date: When the call was held.
            anchor: Which reading of ``t`` to use.

        Returns:
            Index into ``quarters``, or None when the date is outside the
            calendar or the anchor would fall before it starts.
        """
        containing = self.index_containing(call_date)
        if containing is None:
            return None
        if anchor is Anchor.CALL_QUARTER:
            return containing
        return containing - 1 if containing > 0 else None


# endregion

# region Resolution
class Window(BaseModel):
    """A resolved evaluation window.

    Attributes:
        phrase: The phrase this came from.
        offsets: Closed interval of quarters relative to ``t``, as the manual
            writes it: ``(1, 2)`` is ``[t+1, t+2]``. None when unresolved.
        period_ends: The period end of every quarter in the window.
        provenance: The section 4.2 tag for ``w``.
        reason: Why it is unresolved, when it is.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    phrase: Phrase
    offsets: tuple[int, int] | None = None
    period_ends: tuple[date, ...] = ()
    provenance: WindowProvenance
    reason: str | None = None

    @property
    def resolved(self) -> bool:
        """Whether the phrase produced a usable window."""
        return self.offsets is not None


def _unresolved(phrase: Phrase, reason: str) -> Window:
    """Build an unresolved window with its reason.

    Args:
        phrase: The phrase that could not be resolved.
        reason: Why not, in words a policy-gap log can carry.

    Returns:
        The unresolved window.
    """
    return Window(phrase=phrase, provenance=WindowProvenance.UNRESOLVED, reason=reason)


def _offsets_for(phrase: Phrase, t: int, calendar: FiscalCalendar) -> tuple[int, int] | str:
    """Compute the relative interval a phrase names, or why it has none.

    Args:
        phrase: The phrase to resolve.
        t: Index of the claim quarter.
        calendar: The filer's quarters.

    Returns:
        A closed interval relative to ``t``, or a string giving the reason there
        is not one.
    """
    if phrase is Phrase.NEXT_QUARTER:
        return (1, 1)
    if phrase in (Phrase.NEXT_TWO_QUARTERS, Phrase.FIRST_HALF):
        return (1, 2)

    current = calendar.quarters[t]
    if phrase is Phrase.THIS_YEAR:
        remaining = 4 - current.quarter
        if remaining == 0:
            return "the claim quarter is the last of its fiscal year, so no quarters of it remain"
        return (1, remaining)
    if phrase is Phrase.NEXT_YEAR:
        first = 4 - current.quarter + 1
        return (first, first + 3)
    if phrase is Phrase.SECOND_HALF:
        if current.quarter >= 3:
            return "the claim quarter is already in the second half of its fiscal year"
        return (3 - current.quarter, 4 - current.quarter)
    return "the manual assigns no window to this phrase"


def resolve(phrase: Phrase, t: int, calendar: FiscalCalendar) -> Window:
    """Map a phrase onto a window of the filer's own fiscal quarters.

    Args:
        phrase: The phrase, already recognised. This function does not read text.
        t: Index of the claim quarter in ``calendar``.
        calendar: The filer's quarters, contiguous and in order.

    Returns:
        The window, resolved or not. An unresolved window carries the reason,
        which is what an annotator logs in ``annotations/policy_gaps.md``.
    """
    if phrase in (Phrase.VAGUE, Phrase.ABSENT):
        return _unresolved(
            phrase,
            "section 5.5 marks this UNRESOLVED; it is never defaulted to next quarter",
        )
    if not 0 <= t < len(calendar.quarters):
        return _unresolved(phrase, "the claim quarter is outside the calendar")

    offsets = _offsets_for(phrase, t, calendar)
    if isinstance(offsets, str):
        return _unresolved(phrase, offsets)

    start, end = offsets
    last = t + end
    if last >= len(calendar.quarters):
        return _unresolved(
            phrase, "the window runs past the end of the filer's known calendar"
        )

    return Window(
        phrase=phrase,
        offsets=offsets,
        period_ends=tuple(calendar.quarters[t + n].period_end for n in range(start, end + 1)),
        provenance=WindowProvenance.EXPLICIT,
    )


# endregion
