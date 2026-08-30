"""Match study filers to corpus symbols without guessing.

Tickers come from each filer's own submissions record, never from the SEC's
current-registrant file, which maps a reassigned ticker to whichever entity holds
it now. Fuzzy name matching was tried and mapped Metropolitan Life onto 3M.
"""

# region Imports
from __future__ import annotations

from collections.abc import Mapping

from corpus.bridge.models import VERIFIED_ALIASES, FilerMatch, MatchMethod

# endregion

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
