"""The earnings-call transcript corpus: what it covers and how a call divides.

The transcripts are third-party content. Nothing here writes text to a committed
file, and the segmentation is expressed as character offsets so a derived artifact
can be published without redistributing the source.
"""

# region Imports
from __future__ import annotations

from corpus.bridge import VERIFIED_ALIASES, FilerMatch, MatchMethod, match_all, match_filer
from corpus.coverage import SymbolCoverage, coverage_for
from corpus.segments import (
    MARKERS,
    Segmentation,
    SplitConfidence,
    prepared_remarks,
    question_and_answer,
    segment,
)

# endregion

# region Public surface
__all__ = [
    "MARKERS",
    "VERIFIED_ALIASES",
    "FilerMatch",
    "MatchMethod",
    "Segmentation",
    "SplitConfidence",
    "SymbolCoverage",
    "coverage_for",
    "match_all",
    "match_filer",
    "prepared_remarks",
    "question_and_answer",
    "segment",
]

# endregion
