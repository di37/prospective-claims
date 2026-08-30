"""What EDGAR's submissions endpoint returns, filtered to periodic reports.

Amendments are rejected by a validator at construction rather than filtered later:
a 10-Q/A published after the evidence cutoff must never displace the original that
arrived on time.
"""

# region Imports
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from constants import (
    PERIODIC_FORMS,
)

# endregion

class Filing(BaseModel):
    """One periodic report as filed.

    Attributes:
        cik: The filer's SEC identifier.
        form: Form type, one of ``PERIODIC_FORMS``.
        period_end: The last day of the period the report covers.
        filed_date: The day the report reached the SEC, which is what the evidence
            maturity date is computed from.
        accession: The filing's accession number, kept so a value can be traced
            back to the document it came from.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    form: str
    period_end: date
    filed_date: date
    accession: str

    @field_validator("form")
    @classmethod
    def _periodic_only(cls, value: str) -> str:
        """Reject anything that is not an unamended periodic report.

        Args:
            value: Form type.

        Returns:
            The form type unchanged.

        Raises:
            ValueError: If the form is not in ``PERIODIC_FORMS``.
        """
        if value not in PERIODIC_FORMS:
            raise ValueError(f"expected one of {PERIODIC_FORMS}, got {value!r}")
        return value

class FilerSubmissions(BaseModel):
    """Everything the study needs from one filer's submissions payload.

    Attributes:
        cik: The filer's SEC identifier.
        name: Entity name as the SEC records it.
        fiscal_year_end: Fiscal year end as ``MMDD``, which the fiscal calendar
            table in issue 5 is built from.
        tickers: Ticker symbols, used to join against the transcript corpus.
        filings: Unamended periodic reports, earliest first.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    name: str
    fiscal_year_end: str | None = None
    tickers: tuple[str, ...] = ()
    filings: tuple[Filing, ...] = ()
