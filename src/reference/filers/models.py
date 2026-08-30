"""What a filer is, before and after the screen.

``Filer`` extends ``Candidate`` rather than repeating it, so a filer is a candidate
that survived, and the extra fields are exactly what surviving records.
"""

# region Imports
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# endregion

class Candidate(BaseModel):
    """One filer eligible for ranking, before any screen has been applied.

    Attributes:
        cik: SEC identifier, the join key for every other reference table.
        name: Entity name as the SEC records it. Never a join key: U.S. Bancorp
            files as ``US BANCORP \\DE\\``.
        location: SEC location code, such as ``US-CA``.
        revenue: Annual revenue at the selection year, in USD, as tagged.
        source_element: Which taxonomy element supplied the revenue figure.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    name: str = Field(min_length=1)
    location: str
    revenue: float
    source_element: str

class Filer(Candidate):
    """A candidate that passed the screen and made the count.

    Attributes:
        rank: Position in the revenue ranking, one-based.
        assets: Total assets at the selection year, or None when no figure was
            available to screen against.
        revenue_to_assets: Revenue over total assets, or None when unscreened.
    """

    rank: int = Field(gt=0)
    assets: float | None = None
    revenue_to_assets: float | None = None

class Exclusion(BaseModel):
    """A candidate the screen removed, kept so the removal is auditable.

    Attributes:
        cik: SEC identifier for the excluded filer.
        name: Entity name as the SEC records it.
        revenue: The revenue figure that would have set its rank.
        assets: Total assets it was screened against.
        revenue_to_assets: The ratio that failed the threshold.
        would_have_ranked: Where it would have placed had the screen not run.
        reason: Short machine-readable reason.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    name: str
    revenue: float
    assets: float
    revenue_to_assets: float
    would_have_ranked: int = Field(gt=0)
    reason: str

class Selection(BaseModel):
    """The outcome of ranking and screening.

    Attributes:
        filers: The selected filers, largest first.
        excluded: Candidates the screen removed, in rank order.
        unscreened: CIKs of selected filers with no assets figure to screen on.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    filers: tuple[Filer, ...]
    excluded: tuple[Exclusion, ...]
    unscreened: tuple[int, ...]
