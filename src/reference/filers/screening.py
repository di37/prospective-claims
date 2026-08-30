"""The plausibility screen, and why it excludes rather than flags.

The frames API serves whatever a filer tagged, scale errors included. An
implausible revenue figure does not make a filer suspect, it makes its rank
fabricated, and the rule is the largest filers by revenue.
"""

# region Imports
from __future__ import annotations

from collections.abc import Mapping

from reference.filers.models import Candidate, Exclusion, Filer, Selection

# endregion

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
