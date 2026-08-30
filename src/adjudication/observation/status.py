"""The rule from section 6: observable when the window has closed and the reports
covering it have been published, both by the cutoff.

``observe`` takes no evidence argument, and that is the design. A claim whose
figure turns out to be absent has no fact whose publication date could be
inspected, so a status that consulted the evidence could not be assigned to the
claims that need it most.
"""

# region Imports
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from adjudication.observation.covering import _is_overdue
from adjudication.observation.models import (
    CensoringReason,
    FiledReport,
    Observation,
    ObservationStatus,
    RequiredReport,
)

# endregion

def observe(
    required: Sequence[RequiredReport],
    filings: Mapping[date, FiledReport],
    cutoff: date,
) -> Observation:
    """Assign observation status to one resolved claim.

    Args:
        required: The reports covering the claim's window, in any order. Empty
            means the window is UNRESOLVED.
        filings: Covering filings by period, from ``first_covering_filings``.
        cutoff: The evidence cutoff ``T``.

    Returns:
        The status, with the maturity date when one is defined and the reason
        when it is censored.
    """
    if not required:
        return Observation(status=ObservationStatus.NOT_APPLICABLE)

    window_end = max(report.period_end for report in required)

    # The window has to have closed before any report covering it can exist.
    # Checking this first keeps the two censoring reasons apart: a window still
    # open is not the same as a filing that has not arrived.
    if window_end > cutoff:
        return Observation(
            status=ObservationStatus.RIGHT_CENSORED,
            censoring_reason=CensoringReason.IMMATURE_WINDOW,
            window_end=window_end,
        )

    missing = sorted(r.period_end for r in required if r.period_end not in filings)
    if missing:
        overdue = any(_is_overdue(r, cutoff) for r in required if r.period_end in missing)
        return Observation(
            status=ObservationStatus.RIGHT_CENSORED,
            censoring_reason=(
                CensoringReason.DELINQUENT_FILER if overdue else CensoringReason.AWAITING_FILING
            ),
            delinquent_filer=overdue,
            window_end=window_end,
            missing_periods=tuple(missing),
        )

    maturity = max(filings[r.period_end].filed_date for r in required)
    if maturity > cutoff:
        return Observation(
            status=ObservationStatus.RIGHT_CENSORED,
            maturity_date=maturity,
            censoring_reason=CensoringReason.AWAITING_FILING,
            window_end=window_end,
        )

    return Observation(
        status=ObservationStatus.OBSERVABLE,
        maturity_date=maturity,
        window_end=window_end,
    )
