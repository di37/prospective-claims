"""Which filing covers a period, and whether a missing one is overdue.

Amendments are dropped rather than ranked and the earliest filing wins, because
availability starts when the information first reached the SEC. Statutory
deadlines appear only here, to tell a report that is merely pending from one that
is genuinely overdue; they never stand in for a filing date.
"""

# region Imports
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from adjudication.observation.models import FiledReport, RequiredReport
from constants import STATUTORY_DEADLINE_DAYS

# endregion

def first_covering_filings(filings: Iterable[FiledReport]) -> dict[date, FiledReport]:
    """Reduce a filer's reports to one per period: the first that covered it.

    Amendments are dropped rather than ranked. A 10-Q/A published after the cutoff
    does not make a claim observable, while the original that arrived on time
    does, so an amendment must never displace the filing that settled the period.
    Where a period was filed more than once without an amendment, the earliest
    wins, because that is when the information became available.

    Args:
        filings: A filer's reports, any order.

    Returns:
        The covering filing for each period.
    """
    covering: dict[date, FiledReport] = {}
    for filing in filings:
        if filing.form.endswith("/A"):
            continue
        held = covering.get(filing.period_end)
        if held is None or filing.filed_date < held.filed_date:
            covering[filing.period_end] = filing
    return covering

def _is_overdue(report: RequiredReport, cutoff: date) -> bool:
    """Check whether a missing report has passed its filing deadline.

    Args:
        report: The report that has not arrived.
        cutoff: The evidence cutoff.

    Returns:
        True when the deadline fell on or before the cutoff.
    """
    allowed = STATUTORY_DEADLINE_DAYS.get(report.form)
    if allowed is None:
        return False
    return report.period_end + timedelta(days=allowed) <= cutoff
