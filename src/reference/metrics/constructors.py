"""Build a taxonomy element with its periodicity attached.

Periodicity belongs to the element rather than the metric, because a metric can
name a flow and a level at once: days sales outstanding puts receivables, an
instant, over revenue, a period. Probing a balance-sheet element at a flow period
returns nothing, so getting this wrong looks like a missing element.
"""

# region Imports
from __future__ import annotations

from reference.metrics.models import TaxonomyElement

# endregion

def flow(name: str, unit: str = "USD") -> TaxonomyElement:
    """Build an element measured over a period.

    Args:
        name: Qualified element name.
        unit: Frames unit.

    Returns:
        The element.
    """
    return TaxonomyElement(name=name, unit=unit, instantaneous=False)

def instant(name: str, unit: str = "USD") -> TaxonomyElement:
    """Build an element measured at a point in time.

    Args:
        name: Qualified element name.
        unit: Frames unit.

    Returns:
        The element.
    """
    return TaxonomyElement(name=name, unit=unit, instantaneous=True)
