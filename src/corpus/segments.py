"""Split an earnings call into prepared remarks and the analyst Q&A.

The two halves are different objects. Prepared remarks are written, reviewed and
often lawyered; the Q&A is unscripted and is where management is pushed into
saying something specific. Guidance appears in both, and any claim about where
forward-looking language lives has to keep them apart.

There is no field marking the boundary, so it is found in the text. The reliable
signal is the operator handing over to the first analyst, which appears in some
form in almost every call. Weaker phrasings are tried in turn after it.

Where the boundary lands is itself the check. A split at 2 per cent of the
transcript leaves no prepared remarks and is wrong however confident the pattern
match was, so the position is compared against the band in ``constants`` and
marked low confidence outside it. Nothing is dropped: a caller that needs only
prepared remarks can use the split, and one that needs certainty can filter on
confidence.
"""

# region Imports
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from constants import QA_SPLIT_MAX_FRACTION, QA_SPLIT_MIN_FRACTION

# endregion

# region Markers
class SplitConfidence(str, Enum):
    """How much to trust a boundary."""

    OK = "ok"
    IMPLAUSIBLE_POSITION = "implausible_position"
    NOT_FOUND = "not_found"
    EMPTY = "empty"


# Tried in order. The first pattern is the operator's explicit handover and
# accounts for four fifths of the corpus; the bare "first question" below it
# catches the rest but also matches an operator mentioning questions in the
# opening remarks, which is why it sits lower and why position is checked after.
MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("first_question_intro", re.compile(r"(?:our|the)\s+first\s+question\s+(?:comes|is|will come|today)", re.I)),
    ("qa_heading", re.compile(r"^\s*Question[- ]and[- ]Answer Session\s*$", re.I | re.M)),
    ("first_question", re.compile(r"first\s+question", re.I)),
    ("now_begin_questions", re.compile(r"we (?:will|'ll) now (?:begin|open|take)[^.]{0,40}question", re.I)),
    ("open_for_questions", re.compile(r"open (?:it |the (?:call|floor) )?(?:up )?(?:for|to) (?:your )?questions", re.I)),
)

# endregion

# region Model
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


# endregion

# region Splitting
def segment(text: str | None) -> Segmentation:
    """Find the prepared-remarks and Q&A boundary in one transcript.

    Args:
        text: The transcript, which may be empty or missing.

    Returns:
        The segmentation, including the reason when no usable boundary was found.
    """
    if not text:
        return Segmentation(chars=0, confidence=SplitConfidence.EMPTY)

    for name, pattern in MARKERS:
        match = pattern.search(text)
        if not match:
            continue
        fraction = match.start() / len(text)
        plausible = QA_SPLIT_MIN_FRACTION <= fraction <= QA_SPLIT_MAX_FRACTION
        return Segmentation(
            chars=len(text),
            split_offset=match.start(),
            marker=name,
            split_fraction=fraction,
            confidence=SplitConfidence.OK if plausible else SplitConfidence.IMPLAUSIBLE_POSITION,
        )

    return Segmentation(chars=len(text), confidence=SplitConfidence.NOT_FOUND)


def prepared_remarks(text: str, found: Segmentation) -> str:
    """Return the prepared-remarks half, or the whole call when unsplit.

    Args:
        text: The transcript the segmentation was computed from.
        found: The segmentation for that transcript.

    Returns:
        The text before the boundary. An unsplit call returns whole, because a
        call with no Q&A is a prepared statement rather than an empty one.
    """
    return text if found.split_offset is None else text[: found.split_offset]


def question_and_answer(text: str, found: Segmentation) -> str:
    """Return the Q&A half, or empty when no boundary was found.

    Args:
        text: The transcript the segmentation was computed from.
        found: The segmentation for that transcript.

    Returns:
        The text from the boundary onward, empty when unsplit.
    """
    return "" if found.split_offset is None else text[found.split_offset :]


# endregion
