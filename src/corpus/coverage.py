"""Report what the transcript corpus actually covers, quarter by quarter.

A corpus advertised as spanning twenty years and several hundred companies says
nothing about whether any one company is covered continuously, and continuity is
what the study needs: a filer missing a year contributes no claims from it, and a
temporal split drawn across ragged coverage is not the split it claims to be.

Coverage is counted in calendar quarters rather than fiscal ones. The corpus
labels each call with a year and a quarter of its own, and reconciling those to
each filer's fiscal calendar is a separate problem solved by
``reference/fiscal_quarters.csv``. For deciding whether a company is covered
continuously, the corpus's own labels are enough, and mixing the two would hide
gaps behind a mapping.
"""

# region Imports
from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

# endregion

# region Model
class SymbolCoverage(BaseModel):
    """One symbol's coverage across the study window.

    Attributes:
        symbol: Corpus ticker.
        company_name: Company name as the corpus records it, when it carries one.
        first_period: Earliest covered period, ``YYYYQn``.
        last_period: Latest covered period.
        quarters_present: Distinct quarters with a call.
        quarters_expected: Quarters in the window between first and last.
        gaps: Quarters missing between first and last, which is what a mean
            coverage figure would hide.
        continuous: Whether the symbol covers every quarter of the study window.
        span_years: Distinct years covered.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str
    company_name: str | None = None
    first_period: str | None = None
    last_period: str | None = None
    quarters_present: int = Field(ge=0)
    quarters_expected: int = Field(ge=0)
    gaps: int = Field(ge=0)
    continuous: bool = False
    span_years: int = Field(ge=0)


# endregion

# region Counting
def _period(year: int, quarter: int) -> str:
    """Format a year and quarter as a sortable period label.

    Args:
        year: Calendar year.
        quarter: Quarter number.

    Returns:
        Label of the form ``2019Q3``.
    """
    return f"{year}Q{quarter}"


def coverage_for(
    symbol: str,
    company_name: str | None,
    periods: Iterable[tuple[int, int]],
    start_year: int,
    end_year: int,
) -> SymbolCoverage:
    """Summarise one symbol's coverage inside the study window.

    Args:
        symbol: Corpus ticker.
        company_name: Company name as the corpus records it.
        periods: Year and quarter pairs, any order, possibly outside the window.
        start_year: First year of the study window.
        end_year: Last year of the study window.

    Returns:
        The coverage summary.
    """
    inside = sorted(
        {(y, q) for y, q in periods if start_year <= y <= end_year and 1 <= q <= 4}
    )
    window = (end_year - start_year + 1) * 4
    if not inside:
        return SymbolCoverage(
            symbol=symbol, company_name=company_name,
            quarters_present=0, quarters_expected=window, gaps=window, span_years=0,
        )

    first, last = inside[0], inside[-1]
    expected = (last[0] - first[0]) * 4 + (last[1] - first[1]) + 1
    return SymbolCoverage(
        symbol=symbol,
        company_name=company_name,
        first_period=_period(*first),
        last_period=_period(*last),
        quarters_present=len(inside),
        quarters_expected=expected,
        gaps=expected - len(inside),
        continuous=len(inside) == window,
        span_years=len({y for y, _ in inside}),
    )


# endregion
