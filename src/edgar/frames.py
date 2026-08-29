"""Verify that an XBRL element exists in the SEC taxonomy and is actually used.

The frames API returns every filer reporting a given element for a given period.
That makes it a cheap existence check: an element name that is misspelled, has
been deprecated, or belongs to a different namespace returns 404, while a real one
returns the filers using it.

Filer counts matter as well as existence. An element that only three hundred
companies tag is real but sparse, and a reference table that says so lets an
annotator expect the gap rather than treat it as an error.
"""

# region Imports
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from pydantic import BaseModel, ConfigDict, Field

from constants import (
    SEC_FRAMES_URL,
    SEC_MAX_RETRIES,
    SEC_REQUEST_DELAY_SECONDS,
    SEC_TIMEOUT_SECONDS,
    SEC_USER_AGENT,
)

# endregion

# region Probe result
class TaxonomyProbe(BaseModel):
    """Outcome of checking one element against the SEC frames API.

    Attributes:
        element: Qualified element name, such as ``us-gaap:Revenues``.
        unit: Unit the element is reported in.
        period: Frames period used for the probe.
        exists: Whether the SEC returned data for it.
        filer_count: Number of filers reporting it in that period, zero if absent.
        http_status: Status returned, or None if the request never completed.
        error: Short description when the probe failed for a reason other than 404.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    element: str
    unit: str
    period: str
    exists: bool
    filer_count: int = Field(default=0, ge=0)
    http_status: int | None = None
    error: str | None = None


# endregion

# region Probing
def _split_namespace(element: str) -> tuple[str, str]:
    """Split a qualified element name into namespace and local name.

    Args:
        element: Name such as ``us-gaap:Revenues`` or ``dei:EntityCommonStockSharesOutstanding``.

    Returns:
        Tuple of namespace and local name.

    Raises:
        ValueError: If the name is not namespace-qualified.
    """
    if ":" not in element:
        raise ValueError(f"element must be namespace-qualified, got {element!r}")
    namespace, local = element.split(":", 1)
    return namespace, local


def element_exists(element: str, unit: str = "USD", period: str = "CY2023Q1") -> TaxonomyProbe:
    """Check one element against the frames API.

    Retries on transient failures but not on 404, which is a definite answer that
    the element does not exist for that unit and period.

    Args:
        element: Qualified element name.
        unit: Unit to query, such as ``USD``, ``USD-per-shares``, or ``shares``.
        period: Frames period. Instantaneous elements need the ``I`` suffix.

    Returns:
        The probe result.
    """
    namespace, local = _split_namespace(element)
    url = SEC_FRAMES_URL.format(namespace=namespace, element=local, unit=unit, period=period)
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})

    last_error: str | None = None
    for attempt in range(SEC_MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=SEC_TIMEOUT_SECONDS) as response:
                payload = json.load(response)
            return TaxonomyProbe(
                element=element,
                unit=unit,
                period=period,
                exists=True,
                filer_count=len(payload.get("data", [])),
                http_status=200,
            )
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return TaxonomyProbe(
                    element=element, unit=unit, period=period,
                    exists=False, http_status=404,
                )
            last_error = f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001  network failures are varied and all retryable
            last_error = type(exc).__name__
        time.sleep(SEC_REQUEST_DELAY_SECONDS * (attempt + 2))

    return TaxonomyProbe(
        element=element, unit=unit, period=period,
        exists=False, http_status=None, error=last_error,
    )


def probe_elements(requests: list[tuple[str, str, str]]) -> list[TaxonomyProbe]:
    """Check several elements, pausing between requests.

    Args:
        requests: Tuples of element, unit, and period.

    Returns:
        One probe result per request, in the order given.
    """
    results = []
    for element, unit, period in requests:
        results.append(element_exists(element, unit, period))
        time.sleep(SEC_REQUEST_DELAY_SECONDS)
    return results


# endregion
