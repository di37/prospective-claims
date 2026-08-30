"""What the frames API returns: whether an element exists, and what filers reported.
"""

# region Imports
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# endregion

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
