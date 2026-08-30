"""Claim text to a structured, checkable proposition.

Only the temporal half exists so far.
"""

# region Imports
from __future__ import annotations

from resolution.windows.models import (
    Anchor,
    FiscalCalendar,
    Phrase,
    Quarter,
    Window,
    WindowProvenance,
)
from resolution.windows.windows import resolve

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
