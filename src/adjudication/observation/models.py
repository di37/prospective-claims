"""The vocabulary of observation status, and the records that carry it.

What the domain is, kept apart from what it does. Every type is frozen and forbids
unknown fields, so a mistyped keyword fails at construction rather than being
silently ignored.
"""

# region Imports
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# endregion

class ObservationStatus(str, Enum):
    """Whether a claim can be adjudicated yet."""

    OBSERVABLE = "OBSERVABLE"
    RIGHT_CENSORED = "RIGHT_CENSORED"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class CensoringReason(str, Enum):
    """Why a claim is not observable.

    These are reported separately because they say different things. An immature
    window is a property of the study's cutoff and would resolve itself given
    time. A late filing is a property of this filer's behaviour. A delinquent
    filer is a property the study treats as its own case, since the report may
    never arrive.
    """

    IMMATURE_WINDOW = "immature_window"
    AWAITING_FILING = "awaiting_filing"
    DELINQUENT_FILER = "delinquent_filer"

class RequiredReport(BaseModel):
    """A periodic report the window needs in order to be settled.

    Attributes:
        period_end: The fiscal period the report covers.
        form: ``10-K`` for a fiscal year end, ``10-Q`` otherwise. The 10-K
            replaces the fourth 10-Q, so a window ending on a year end requires
            the annual report rather than a quarterly one.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period_end: date
    form: str

class FiledReport(BaseModel):
    """A report that was actually filed, as ``filing_dates.csv`` records it.

    Attributes:
        period_end: The fiscal period covered.
        form: Form type as filed.
        filed_date: When it reached the SEC. This, never a deadline, is what the
            maturity date is built from.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period_end: date
    form: str
    filed_date: date

class Observation(BaseModel):
    """The computed status of one claim, with the evidence for it.

    Attributes:
        status: OBSERVABLE, RIGHT_CENSORED, or NOT_APPLICABLE.
        maturity_date: ``M(c)``, the latest filing date among the covering
            reports. None when a required report is missing, which is what the
            manual means by ``M(c)`` being undefined.
        censoring_reason: Why it is censored, when it is.
        delinquent_filer: Whether a required report is both missing and overdue.
        window_end: The last period the window covers.
        missing_periods: Periods with no covering filing, earliest first.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: ObservationStatus
    maturity_date: date | None = None
    censoring_reason: CensoringReason | None = None
    delinquent_filer: bool = False
    window_end: date | None = None
    missing_periods: tuple[date, ...] = ()

class CensoringRates(BaseModel):
    """The censoring rate, split by the reason claims were censored.

    Attributes:
        claims: How many claims were assigned a status.
        observable: How many are adjudicable.
        censored: How many are right-censored.
        not_applicable: How many have no resolved window.
        by_reason: Censored counts per reason.
        censoring_rate: Censored over claims with a status, so the
            not-applicable claims are excluded from the denominator rather than
            counted as censored. They are a different failure.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    claims: int = Field(ge=0)
    observable: int = Field(ge=0)
    censored: int = Field(ge=0)
    not_applicable: int = Field(ge=0)
    by_reason: dict[str, int]
    censoring_rate: float | None = None
