"""The earnings-call transcript corpus: coverage, identity, and segmentation.

Nothing here writes transcript text to a file. Segmentation is expressed as
character offsets, so a derived artifact can be published without redistributing
the source.
"""

# region Imports
from __future__ import annotations

from corpus.bridge.matching import match_all, match_filer
from corpus.bridge.models import VERIFIED_ALIASES, FilerMatch, MatchMethod

# endregion

# region Public surface
__all__ = [
    "FilerMatch",
    "MatchMethod",
    "VERIFIED_ALIASES",
    "match_all",
    "match_filer",
]

# endregion
