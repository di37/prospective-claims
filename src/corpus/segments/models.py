"""Where a call divides, recorded as offsets rather than text.

Offsets because the transcripts are third-party content this project does not
redistribute. An offset plus the source row rebuilds the segment exactly and
carries no licensed text with it.
"""

# region Imports
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# endregion

class SplitConfidence(str, Enum):
    """How much to trust a boundary."""

    OK = "ok"
    IMPLAUSIBLE_POSITION = "implausible_position"
    NOT_FOUND = "not_found"
    EMPTY = "empty"

MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("first_question_intro", re.compile(r"(?:our|the)\s+first\s+question\s+(?:comes|is|will come|today)", re.I)),
    ("qa_heading", re.compile(r"^\s*Question[- ]and[- ]Answer Session\s*$", re.I | re.M)),
    ("first_question", re.compile(r"first\s+question", re.I)),
    ("now_begin_questions", re.compile(r"we (?:will|'ll) now (?:begin|open|take)[^.]{0,40}question", re.I)),
    ("open_for_questions", re.compile(r"open (?:it |the (?:call|floor) )?(?:up )?(?:for|to) (?:your )?questions", re.I)),
)

class Segmentation(BaseModel):
    """Where one transcript divides, recorded as offsets rather than text.

    Offsets rather than text because the transcripts are third-party content that
    this project does not redistribute. An offset plus the source row rebuilds the
    segment exactly, and carries no licensed text with it.

    Attributes:
        chars: Length of the transcript.
        split_offset: Character offset where the Q&A begins, or None when no
            boundary was found.
        marker: Which pattern matched, or None.
        split_fraction: The offset as a fraction of the transcript.
        confidence: Whether the boundary is usable.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chars: int = Field(ge=0)
    split_offset: int | None = None
    marker: str | None = None
    split_fraction: float | None = None
    confidence: SplitConfidence
