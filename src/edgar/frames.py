"""Verify that an XBRL element exists in the SEC taxonomy and is actually used.

The frames API returns every filer reporting a given element for a given period.
That makes it a cheap existence check: an element name that is misspelled, has
been deprecated, or belongs to a different namespace returns 404, while a real one
returns the filers using it.

Filer counts matter as well as existence. An element that only three hundred
companies tag is real but sparse, and a reference table that says so lets an
annotator expect the gap rather than treat it as an error.

The same endpoint answers a second question. One request returns every filer's
value for an element in a period, which is how the study ranks filers by revenue
and screens them against their balance sheets without a request per company.
"""

# region Imports
from __future__ import annotations

import time

from pydantic import BaseModel, ConfigDict, Field

from constants import SEC_FRAMES_URL, SEC_REQUEST_DELAY_SECONDS
from edgar.transport import get_json

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

# region Frame values
class FrameFact(BaseModel):
    """One filer's reported value for an element in a period.

    Attributes:
        cik: SEC identifier for the filer.
        entity_name: Entity name as the SEC records it, which is not stable and
            must never be used as a join key.
        location: SEC location code, such as ``US-CA``. Empty when not given.
        value: The reported value, exactly as tagged. The SEC serves what the
            filer submitted, scale errors included.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    entity_name: str
    location: str = ""
    value: float


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
    payload, status, error = get_json(url)

    if payload is None:
        return TaxonomyProbe(
            element=element, unit=unit, period=period,
            exists=False, http_status=status, error=error,
        )
    return TaxonomyProbe(
        element=element,
        unit=unit,
        period=period,
        exists=True,
        filer_count=len(payload.get("data", [])),
        http_status=status,
    )


def fetch_frame(element: str, unit: str = "USD", period: str = "CY2023") -> tuple[FrameFact, ...]:
    """Fetch every filer's value for one element in one period.

    Args:
        element: Qualified element name.
        unit: Unit to query.
        period: Frames period. Instantaneous elements need the ``I`` suffix.

    Returns:
        One fact per filer, in the order the SEC returned them. Empty when the
        element does not exist for that unit and period.

    Raises:
        RuntimeError: If the request failed for a reason other than 404, since a
            partial frame would silently change which filers are in the study.
    """
    namespace, local = _split_namespace(element)
    url = SEC_FRAMES_URL.format(namespace=namespace, element=local, unit=unit, period=period)
    payload, status, error = get_json(url)

    if payload is None:
        if status == 404:
            return ()
        raise RuntimeError(f"frame {element} {unit} {period} failed: {error}")

    return tuple(
        FrameFact(
            cik=int(row["cik"]),
            entity_name=row["entityName"],
            location=row.get("loc", "") or "",
            value=float(row["val"]),
        )
        for row in payload.get("data", [])
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
