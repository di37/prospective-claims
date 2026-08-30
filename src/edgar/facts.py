"""Read one filer's reported values for a single XBRL concept.

The frames API answers "who reported this element in this period" for every filer
at once, which is what the study ranks and screens on. It cannot answer "what did
this one filer report", and it has gaps: a company whose fiscal year does not end
near the frame's instant, or that registered recently, has no row in the frame at
all even though the fact exists.

This module fills those gaps one filer at a time. It is deliberately narrow. The
full Company Facts client, which pulls every concept a filer has ever tagged, is
a separate piece of work.
"""

# region Imports
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from constants import SEC_COMPANY_CONCEPT_URL
from edgar.transport import get_json

# endregion

# region Model
class ConceptValue(BaseModel):
    """One reported value for one concept, with the filing it came from.

    Attributes:
        cik: SEC identifier for the filer.
        element: Qualified element name.
        unit: Unit the value is reported in.
        end: Period end the value applies to, ``YYYY-MM-DD``.
        value: The reported value, exactly as tagged.
        form: Form the value was reported on, such as ``10-K``.
        filed: Date that form was filed, ``YYYY-MM-DD``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    cik: int = Field(gt=0)
    element: str
    unit: str
    end: str
    value: float
    form: str
    filed: str


# endregion

# region Reading
def latest_value_in_year(
    cik: int,
    element: str,
    unit: str = "USD",
    year: int = 2023,
) -> ConceptValue | None:
    """Return a filer's last reported value for a concept within one calendar year.

    Where a period end was reported more than once, the most recently filed value
    wins. That is the opposite of the rule used for filing dates, and deliberately
    so: there the question is when evidence first became available, here it is
    what the figure actually is, and a later filing corrects an earlier one.

    Args:
        cik: SEC identifier for the filer.
        element: Qualified element name.
        unit: Unit to read.
        year: Calendar year the period end must fall in.

    Returns:
        The value, or None when the filer has never tagged the concept, has no
        value ending in that year, or the request failed.
    """
    namespace, local = element.split(":", 1)
    url = SEC_COMPANY_CONCEPT_URL.format(cik=cik, namespace=namespace, element=local)
    payload, _status, _error = get_json(url)
    if payload is None:
        return None

    entries = [
        entry
        for entry in payload.get("units", {}).get(unit, [])
        if str(entry.get("end", "")).startswith(str(year))
    ]
    if not entries:
        return None

    best = max(entries, key=lambda entry: (entry["end"], entry.get("filed", "")))
    return ConceptValue(
        cik=cik,
        element=element,
        unit=unit,
        end=best["end"],
        value=float(best["val"]),
        form=best.get("form", ""),
        filed=best.get("filed", ""),
    )


# endregion
