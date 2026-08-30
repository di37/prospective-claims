"""The censoring rate, split by the reason claims were censored.

Reported by reason rather than as one number, because the three say different
things: a cutoff that has not caught up, a filer that has not filed yet, and a
filer that may never file.
"""

# region Imports
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from adjudication.observation.models import (
    CensoringRates,
    Observation,
    ObservationStatus,
)

# endregion

def censoring_rates(observations: Iterable[Observation]) -> CensoringRates:
    """Summarise a set of observations for the pilot's censoring report.

    Args:
        observations: One per claim.

    Returns:
        Counts by status and by censoring reason, with the rate.
    """
    items = list(observations)
    statuses = Counter(o.status for o in items)
    reasons = Counter(o.censoring_reason.value for o in items if o.censoring_reason)

    observable = statuses[ObservationStatus.OBSERVABLE]
    censored = statuses[ObservationStatus.RIGHT_CENSORED]
    with_status = observable + censored
    return CensoringRates(
        claims=len(items),
        observable=observable,
        censored=censored,
        not_applicable=statuses[ObservationStatus.NOT_APPLICABLE],
        by_reason=dict(reasons),
        censoring_rate=(censored / with_status) if with_status else None,
    )
