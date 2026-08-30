"""Curated definitions behind the frozen reference tables.

The authored source behind the generated tables under ``reference/``. Validated at
import, so a malformed entry fails here rather than surfacing later as a confusing
annotation.
"""

# region Imports
from __future__ import annotations

from reference.filers import Candidate, Exclusion, Filer, Selection, rank_candidates, select
from reference.metrics import (
    METRIC_DEFINITIONS,
    MetricClass,
    MetricDefinition,
    TaxonomyElement,
)

# endregion

# region Public surface
__all__ = [
    "METRIC_DEFINITIONS",
    "Candidate",
    "Exclusion",
    "Filer",
    "MetricClass",
    "MetricDefinition",
    "Selection",
    "TaxonomyElement",
    "rank_candidates",
    "select",
]

# endregion
