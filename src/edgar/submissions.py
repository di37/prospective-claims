"""Retrieve a filer's periodic filings from the EDGAR submissions API.

The submissions endpoint returns a filer's most recent 1,000 filings inline and
pushes anything older into overflow files. For a large filer that thousand covers
only the last decade or so, and for an active one much less, so a study window
reaching back to 2012 must follow the overflow rather than trusting what arrives
first. Apple's inline set reaches 2015; its 10-K and 10-Q filings before that are
all in one overflow file.

Amendments are dropped here rather than downstream. A 10-Q/A published after the
evidence cutoff does not make a claim observable, while the original that arrived
on time does, so an amendment must never displace the filing it corrects.
"""

# region Imports
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from constants import (
    PERIODIC_FORMS,
    SEC_MAX_RETRIES,
    SEC_REQUEST_DELAY_SECONDS,
    SEC_SUBMISSIONS_OVERFLOW_URL,
    SEC_SUBMISSIONS_URL,
    SEC_TIMEOUT_SECONDS,
    SEC_USER_AGENT,
)

# endregion

# region Models
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


# endregion

# region Fetching
def _get_json(url: str) -> dict:
    """Fetch and parse one SEC JSON document, retrying transient failures.

    Args:
        url: Fully qualified URL.

    Returns:
        The parsed document.

    Raises:
        RuntimeError: If every attempt fails.
    """
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})
    last: str = "no attempt made"
    for attempt in range(SEC_MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=SEC_TIMEOUT_SECONDS) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise RuntimeError(f"not found: {url}") from exc
            last = f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001  network failures are varied and retryable
            last = type(exc).__name__
        time.sleep(SEC_REQUEST_DELAY_SECONDS * (attempt + 2))
    raise RuntimeError(f"{last} after {SEC_MAX_RETRIES} attempts: {url}")


def _extract(cik: int, block: dict) -> list[Filing]:
    """Pull the unamended periodic reports out of one filings block.

    Both the inline block and the overflow files share this column-oriented shape,
    so one reader serves both.

    Args:
        cik: The filer's SEC identifier.
        block: A filings block with parallel lists keyed by field name.

    Returns:
        The periodic filings found, unordered.
    """
    filings: list[Filing] = []
    forms = block.get("form", [])
    for index, form in enumerate(forms):
        if form not in PERIODIC_FORMS:
            continue
        period = block["reportDate"][index]
        filed = block["filingDate"][index]
        if not period or not filed:
            continue
        filings.append(
            Filing(
                cik=cik,
                form=form,
                period_end=date.fromisoformat(period),
                filed_date=date.fromisoformat(filed),
                accession=block["accessionNumber"][index],
            )
        )
    return filings


def fetch_filer(cik: int) -> FilerSubmissions:
    """Fetch one filer's periodic filings, following overflow files.

    Args:
        cik: The filer's SEC identifier.

    Returns:
        The filer's submissions, filings sorted earliest first.

    Raises:
        RuntimeError: If the filer cannot be retrieved.
    """
    payload = _get_json(SEC_SUBMISSIONS_URL.format(cik=cik))
    filings = _extract(cik, payload["filings"].get("recent", {}))

    for overflow in payload["filings"].get("files", []):
        time.sleep(SEC_REQUEST_DELAY_SECONDS)
        filings.extend(_extract(cik, _get_json(SEC_SUBMISSIONS_OVERFLOW_URL.format(name=overflow["name"]))))

    return FilerSubmissions(
        cik=cik,
        name=payload.get("name", ""),
        fiscal_year_end=payload.get("fiscalYearEnd") or None,
        tickers=tuple(payload.get("tickers", [])),
        filings=tuple(sorted(filings, key=lambda f: (f.period_end, f.filed_date))),
    )


# endregion

# region Deduplication
def first_filing_per_period(filings: tuple[Filing, ...]) -> list[Filing]:
    """Keep the earliest filing covering each period.

    A period can be reported more than once when a filer refiles. The earliest is
    the one that made the information available, so it is the one the evidence
    maturity date depends on. Amendments never reach here, having been dropped at
    extraction, but a duplicate original would be caught by the same rule.

    Args:
        filings: Periodic filings for one filer.

    Returns:
        One filing per period end, earliest period first.
    """
    earliest: dict[tuple[str, date], Filing] = {}
    for filing in filings:
        key = (filing.form, filing.period_end)
        held = earliest.get(key)
        if held is None or filing.filed_date < held.filed_date:
            earliest[key] = filing
    return sorted(earliest.values(), key=lambda f: (f.period_end, f.form))


# endregion
