"""Section 5.5: a phrase the manual names, onto a filer's own fiscal quarters.

Only the decidable half. Recognising an arbitrary paraphrase as one of the manual's
phrases is the model's job and is RQ1; nothing here reads text.
"""

# region Imports
from __future__ import annotations

from resolution.windows.models import FiscalCalendar, Phrase, Window, WindowProvenance

# endregion

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
