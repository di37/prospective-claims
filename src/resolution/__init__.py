"""Claim text to a structured, checkable proposition.

Only the temporal half exists so far: mapping a phrase the manual names onto a
window of the filer's own fiscal quarters. The rest of the resolution fields are
separate work.
"""

# region Imports
from __future__ import annotations

from resolution.windows import (
    Anchor,
    FiscalCalendar,
    Phrase,
    Quarter,
    Window,
    WindowProvenance,
    resolve,
)

# endregion

# region Public surface
__all__ = [
    "Anchor",
    "FiscalCalendar",
    "Phrase",
    "Quarter",
    "Window",
    "WindowProvenance",
    "resolve",
]

# endregion
