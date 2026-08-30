"""The earnings-call transcript corpus: coverage, identity, and segmentation.
"""

# region Imports
from __future__ import annotations

from corpus.segments.models import MARKERS, Segmentation, SplitConfidence
from corpus.segments.splitting import prepared_remarks, question_and_answer, segment

# endregion

# region Public surface
__all__ = [
    "MARKERS",
    "Segmentation",
    "SplitConfidence",
    "prepared_remarks",
    "question_and_answer",
    "segment",
]

# endregion
