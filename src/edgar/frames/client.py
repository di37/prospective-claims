"""The frames API: one request answers for every filer at once.

That makes it the cheap path and the right default. ``facts.py`` exists for the
gaps it leaves.
"""

# region Imports
from __future__ import annotations

import time

from constants import SEC_FRAMES_URL, SEC_REQUEST_DELAY_SECONDS
from edgar.frames.models import FrameFact, TaxonomyProbe
from edgar.transport import get_json

# endregion

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
