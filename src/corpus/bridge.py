"""Map the study's filers, which are keyed by CIK, onto a corpus keyed by ticker.

This join is where a transcript corpus meets a filing-derived study set, and it
is less mechanical than it looks. A ticker is not a stable identifier over a
thirteen-year window: it moves when a company reorganises, it is reassigned after
a delisting, and the SEC's public ticker file lists only current registrants, so
a company that went private has no entry at all.

Exxon Mobil is the case that makes the point. The study holds CIK 34088, taken
from a 2023 revenue frame. The SEC's current ticker file maps XOM to CIK 2115436,
a later holding entity, and the submissions record for 34088 carries no ticker.
Joining on the public ticker file would silently drop the seventh largest filer
in the study.

The bridge therefore reads tickers from each filer's own EDGAR submissions record
rather than the global file, and falls back to a short list of aliases that were
checked one at a time against the corpus's own company names. It does not guess.
An earlier attempt at fuzzy name matching mapped Metropolitan Life onto 3M and
Flex onto F5 Networks, which is exactly the sort of error that would be invisible
in a coverage count and fatal in an adjudication.

A filer with no match is reported with the reason, and there are two of them: the
filer has no ticker at all, meaning it is not listed, or it has one and the corpus
does not carry it, meaning the corpus is narrower than the study set.
"""

# region Imports
from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# endregion

# region Aliases
class MatchMethod(str, Enum):
    """How a filer was matched to a corpus symbol, or why it was not."""

    EDGAR_TICKER = "edgar_ticker"
    VERIFIED_ALIAS = "verified_alias"
    NOT_LISTED = "not_listed"
    ABSENT_FROM_CORPUS = "absent_from_corpus"


# CIK to symbol, each one checked against the corpus's own company_name rather
# than inferred. Keep this list short and evidenced: every entry is a case where
# EDGAR and the corpus disagree about identity, and the justification is the
# reason the disagreement exists.
VERIFIED_ALIASES: Mapping[int, tuple[str, str]] = {
    34088: (
        "XOM",
        "The study holds the predecessor CIK from a 2023 revenue frame; the SEC "
        "ticker file now maps XOM to a later holding entity, and 34088 carries no "
        "ticker. The corpus rows under XOM name Exxon Mobil Corporation.",
    ),
    1618921: (
        "WBA",
        "Delisted, so it has been removed from the SEC's current-registrant "
        "ticker file and its submissions record carries no ticker. The corpus "
        "rows under WBA name Walgreens Boots Alliance, Inc.",
    ),
    813828: (
        "PARA",
        "Succeeded by Paramount Skydance, so the submissions record for the "
        "predecessor carries no ticker. The corpus rows under PARA name "
        "Paramount Global.",
    ),
}

# endregion

# region Model
class FilerMatch(BaseModel):
    """One study filer's relationship to the transcript corpus.

    Attributes:
        cik: SEC identifier for the filer.
        name: Entity name as the SEC records it.
        symbol: Corpus symbol when matched, otherwise None.
        method: How the match was made, or why it was not.
        edgar_tickers: Tickers the filer's own submissions record carries, which
            is what distinguishes an unlisted filer from one the corpus omits.
        note: Justification, for aliases.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    name: str
    symbol: str | None = None
    method: MatchMethod
    edgar_tickers: tuple[str, ...] = ()
    note: str | None = None

    @property
    def matched(self) -> bool:
        """Whether this filer has a symbol in the corpus."""
        return self.symbol is not None


# endregion

# region Matching
def match_filer(
    cik: int,
    name: str,
    tickers: tuple[str, ...],
    corpus_symbols: frozenset[str],
) -> FilerMatch:
    """Decide whether one filer appears in the corpus, and on what evidence.

    Args:
        cik: SEC identifier for the filer.
        name: Entity name as the SEC records it.
        tickers: Tickers from the filer's EDGAR submissions record.
        corpus_symbols: Every symbol the corpus carries, upper case.

    Returns:
        The match, or the reason there is none.
    """
    upper = tuple(t.upper() for t in tickers)
    hit = next((t for t in upper if t in corpus_symbols), None)
    if hit:
        return FilerMatch(
            cik=cik, name=name, symbol=hit,
            method=MatchMethod.EDGAR_TICKER, edgar_tickers=upper,
        )

    alias = VERIFIED_ALIASES.get(cik)
    if alias and alias[0] in corpus_symbols:
        return FilerMatch(
            cik=cik, name=name, symbol=alias[0],
            method=MatchMethod.VERIFIED_ALIAS, edgar_tickers=upper, note=alias[1],
        )

    method = MatchMethod.ABSENT_FROM_CORPUS if upper else MatchMethod.NOT_LISTED
    return FilerMatch(cik=cik, name=name, method=method, edgar_tickers=upper)


def match_all(
    filers: Mapping[int, tuple[str, tuple[str, ...]]],
    corpus_symbols: frozenset[str],
) -> tuple[FilerMatch, ...]:
    """Match every study filer against the corpus.

    Args:
        filers: Name and EDGAR tickers by CIK.
        corpus_symbols: Every symbol the corpus carries, upper case.

    Returns:
        One match per filer, in the order given.
    """
    return tuple(
        match_filer(cik, name, tickers, corpus_symbols)
        for cik, (name, tickers) in filers.items()
    )


# endregion
