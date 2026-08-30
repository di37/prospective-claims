"""Curated metric definitions behind ``reference/metric_classes.csv``.

Validated at import, so a malformed entry fails here rather than surfacing later as
a confusing annotation.
"""

# region Imports
from __future__ import annotations

from reference.metrics.constructors import flow, instant
from reference.metrics.definitions import (
    BALANCE_SHEET,
    CASH_FLOW,
    INCOME_STATEMENT,
    MARGIN_NOTE,
    METRIC_DEFINITIONS,
    MIXED_NOTE,
    MIXED_RATIOS,
    RATIOS,
    SHARES,
    UNTAGGED,
)
from reference.metrics.models import MetricClass, MetricDefinition, TaxonomyElement

# endregion

# region Public surface
__all__ = [
    "BALANCE_SHEET",
    "CASH_FLOW",
    "INCOME_STATEMENT",
    "MARGIN_NOTE",
    "METRIC_DEFINITIONS",
    "MIXED_NOTE",
    "MIXED_RATIOS",
    "MetricClass",
    "MetricDefinition",
    "RATIOS",
    "SHARES",
    "TaxonomyElement",
    "UNTAGGED",
    "flow",
    "instant",
]

# endregion
