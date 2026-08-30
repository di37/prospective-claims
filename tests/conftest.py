"""Put ``src`` on the path so tests import the study's modules the way scripts do.

Scripts append ``src`` themselves before importing. Tests are collected by pytest
from the repository root instead, so the same thing has to happen once here.
"""

# region Imports
from __future__ import annotations

import sys
from pathlib import Path

# endregion

# region Path
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# endregion
