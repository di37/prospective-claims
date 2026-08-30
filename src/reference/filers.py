"""Select the study's filers by a rule rather than by hand.

The study needs 120 to 150 large US filers with continuous coverage across 2012
to 2024. Market capitalisation would be the natural size measure and is not in
XBRL, so filers are ranked by annual revenue, which is.

Three limitations this rule carries, all recorded rather than hidden.

Ranking at a single recent year is a survivorship filter. A company that was large
in 2012 and has since shrunk, been acquired, or delisted cannot appear, and those
are disproportionately the companies whose management claims failed. Any result
about claim reliability drawn from this set is conditioned on survival. Removing
that requires point-in-time index membership, which is not free and is out of
scope here.

Revenue is a size proxy, not a size measure. It over-weights low-margin
distribution against high-margin software: three drug wholesalers outrank
Microsoft.

Whether a financial firm appears at all is decided by tagging practice rather than
by size. Goldman Sachs, Morgan Stanley, Wells Fargo and Truist report interest and
non-interest income and tag neither revenue element, so no cutoff admits them,
while JPMorgan and Bank of America are in. This is closer to arbitrary exclusion
than to under-weighting, and anything the study says about financial-sector claims
is conditioned on it.

The rule also has to survive the data. The frames API serves whatever a filer
tagged, scale errors included, so candidates are screened on revenue over total
assets before the ranking is taken. See ``constants.MAX_REVENUE_TO_ASSETS`` for
where the threshold comes from.

This module decides who is in the study. The definitive set is the intersection of
that decision with the transcript corpus, since a filer with no transcript
contributes no claims.
"""

# region Imports
from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

from edgar.frames import FrameFact

# endregion

# region Models
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


# endregion

# region Ranking
def rank_candidates(
    frames: Mapping[str, tuple[FrameFact, ...]],
    location_prefix: str,
) -> tuple[Candidate, ...]:
    """Merge the revenue frames into one ranking, largest first.

    A filer reporting under both revenue elements is counted once, keeping the
    larger figure, because the two overlap during the ASC 606 transition and
    summing them would double-count.

    Args:
        frames: Frame facts keyed by the element that produced them.
        location_prefix: Keep only filers whose location starts with this, which
            restricts the study to US filers.

    Returns:
        Every eligible candidate, largest revenue first.
    """
    best: dict[int, tuple[FrameFact, str]] = {}
    for element, facts in frames.items():
        for fact in facts:
            if not fact.location.startswith(location_prefix):
                continue
            held = best.get(fact.cik)
            if held is None or fact.value > held[0].value:
                best[fact.cik] = (fact, element)

    ordered = sorted(best.values(), key=lambda pair: -pair[0].value)
    return tuple(
        Candidate(
            cik=fact.cik,
            name=fact.entity_name,
            location=fact.location,
            revenue=fact.value,
            source_element=element,
        )
        for fact, element in ordered
    )


# endregion

# region Screening
def select(
    candidates: tuple[Candidate, ...],
    assets: Mapping[int, float],
    count: int,
    max_ratio: float,
) -> Selection:
    """Screen candidates from the top down and take the first that pass.

    A candidate whose revenue exceeds ``max_ratio`` times its total assets is
    excluded rather than flagged: an implausible revenue figure does not make a
    filer suspect, it makes its rank fabricated. A candidate with no assets figure
    is kept, because absence of a balance sheet to check against is not evidence
    of an error, and its CIK is recorded so the gap is visible.

    Args:
        candidates: Eligible candidates, largest revenue first.
        assets: Total assets by CIK, for those where a figure was found.
        count: How many filers to keep.
        max_ratio: Largest plausible revenue over total assets.

    Returns:
        The selection, with every exclusion recorded.

    Raises:
        ValueError: If the screen leaves fewer than ``count`` candidates, which
            means the pool was too shallow and the result would silently be a
            shorter study set.
    """
    kept: list[Filer] = []
    excluded: list[Exclusion] = []
    unscreened: list[int] = []

    for position, candidate in enumerate(candidates, start=1):
        held = assets.get(candidate.cik)
        # A zero or negative assets figure is itself unusable, so it screens
        # nothing rather than dividing by it.
        screenable = held is not None and held > 0
        ratio = candidate.revenue / held if screenable else None

        if ratio is not None and ratio > max_ratio:
            excluded.append(
                Exclusion(
                    cik=candidate.cik,
                    name=candidate.name,
                    revenue=candidate.revenue,
                    assets=held,
                    revenue_to_assets=ratio,
                    would_have_ranked=position,
                    reason="revenue_implausible_against_assets",
                )
            )
            continue

        if not screenable:
            unscreened.append(candidate.cik)

        kept.append(
            Filer(
                **candidate.model_dump(),
                rank=len(kept) + 1,
                assets=held if screenable else None,
                revenue_to_assets=ratio,
            )
        )
        if len(kept) == count:
            break

    if len(kept) < count:
        raise ValueError(
            f"screen left {len(kept)} filers from {len(candidates)} candidates, "
            f"needed {count}: deepen the screening pool"
        )

    return Selection(
        filers=tuple(kept),
        excluded=tuple(excluded),
        unscreened=tuple(unscreened),
    )


# endregion
