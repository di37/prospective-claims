"""The vocabulary of a resolved window, and the calendar it is resolved against.

``Anchor`` is the one piece of unfinished business. Section 4.1 calls the window
relative to "the claim quarter" in one line and "the quarter of the call" in the
next, and those differ by exactly one for every earnings call, because a call
reporting the third quarter is held during the fourth. Both readings live here so
the choice stays a decision about the manual rather than one buried in code.
"""

# region Imports
from __future__ import annotations

from datetime import date, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# endregion

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
