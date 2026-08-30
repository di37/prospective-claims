"""Find the boundary between prepared remarks and the analyst Q&A.

No field marks it, so it is found in the text by the operator handing over to the
first analyst. Where the boundary lands is the check: a split at two per cent of
the transcript leaves no prepared remarks and is wrong however confident the
pattern match was.
"""

# region Imports
from __future__ import annotations

from constants import QA_SPLIT_MAX_FRACTION, QA_SPLIT_MIN_FRACTION
from corpus.segments.models import MARKERS, Segmentation, SplitConfidence

# endregion

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
