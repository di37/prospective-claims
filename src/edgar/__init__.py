"""Clients for SEC EDGAR and the XBRL company facts API.

Everything in the study that talks to the SEC goes through this package, so the
User-Agent, the rate limit, and the retry policy are set in one place rather than
at each call site.
"""

# region Imports
from __future__ import annotations

from edgar.facts import ConceptValue, latest_value_in_year
from edgar.frames import FrameFact, TaxonomyProbe, element_exists, fetch_frame, probe_elements
from edgar.submissions import Filing, FilerSubmissions, fetch_filer, first_filing_per_period

# endregion

# region Public surface
__all__ = [
    "ConceptValue",
    "Filing",
    "FilerSubmissions",
    "FrameFact",
    "TaxonomyProbe",
    "element_exists",
    "fetch_filer",
    "fetch_frame",
    "first_filing_per_period",
    "latest_value_in_year",
    "probe_elements",
]

# endregion
