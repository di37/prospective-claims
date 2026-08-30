"""How a study filer relates to the transcript corpus, and on what evidence.

``VERIFIED_ALIASES`` is deliberately short and each entry carries its
justification. Every one is a case where EDGAR and the corpus disagree about
identity, and the note is the reason the disagreement exists.
"""

# region Imports
from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# endregion

class MatchMethod(str, Enum):
    """How a filer was matched to a corpus symbol, or why it was not."""

    EDGAR_TICKER = "edgar_ticker"
    VERIFIED_ALIAS = "verified_alias"
    NOT_LISTED = "not_listed"
    ABSENT_FROM_CORPUS = "absent_from_corpus"

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
