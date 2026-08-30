"""Merge the revenue frames into one ranking.

A filer reporting under both revenue elements is counted once at the larger figure,
because the two overlap during the ASC 606 transition and summing them would
double-count.
"""

# region Imports
from __future__ import annotations

from collections.abc import Mapping

from edgar.frames import FrameFact
from reference.filers.models import Candidate

# endregion

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
