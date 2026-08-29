"""Clients for SEC EDGAR and the XBRL company facts API.

Everything in the study that talks to the SEC goes through this package, so the
User-Agent, the rate limit, and the retry policy are set in one place rather than
at each call site.
"""

# region Imports
from __future__ import annotations

from edgar.frames import TaxonomyProbe, element_exists, probe_elements

# endregion

# region Public surface
__all__ = ["TaxonomyProbe", "element_exists", "probe_elements"]

# endregion
