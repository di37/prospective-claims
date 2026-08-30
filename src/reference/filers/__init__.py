"""The rule that decides who is in the study, and what it costs.

Ranking by revenue is a survivorship filter, revenue is a size proxy rather than a
size measure, and whether a financial firm appears at all is decided by tagging
practice. All three are recorded rather than hidden; see ``models.py`` and the
notebook that reads the table.
"""

# region Imports
from __future__ import annotations

from reference.filers.models import Candidate, Exclusion, Filer, Selection
from reference.filers.ranking import rank_candidates
from reference.filers.screening import select

# endregion

# region Public surface
__all__ = [
    "Candidate",
    "Exclusion",
    "Filer",
    "Selection",
    "rank_candidates",
    "select",
]

# endregion
