"""Central constants for the prospective claim verification study.

Single source of truth for every fixed path, seed, and external-service setting
used by the harness modules, the scripts, and the notebooks. Keeping them here
prevents the drift where a value is redefined in two places and silently diverges.

This module imports only the standard library, so it is cheap to import from
anywhere, including code paths that must not pull in pandas or any other heavy
dependency.
"""

# region Imports
from __future__ import annotations

from pathlib import Path

# endregion

# region Identity
STUDY_NAME = "prospective-claims"

# endregion

# region Repository layout
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

REFERENCE_DIR = PROJECT_ROOT / "reference"
ANNOTATIONS_DIR = PROJECT_ROOT / "annotations"

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
LOGS_DIR = REPORTS_DIR / "logs"
REPRO_DIR = REPORTS_DIR / "repro"

OUTPUT_DIRS = (
    INTERIM_DIR,
    PROCESSED_DIR,
    REFERENCE_DIR,
    ANNOTATIONS_DIR,
    FIGURES_DIR,
    TABLES_DIR,
    LOGS_DIR,
    REPRO_DIR,
)

# endregion

# region Reference tables
METRIC_CLASSES_FILE = REFERENCE_DIR / "metric_classes.csv"
FISCAL_CALENDAR_FILE = REFERENCE_DIR / "fiscal_calendar.csv"
FILING_DATES_FILE = REFERENCE_DIR / "filing_dates.csv"
EVIDENCE_CUTOFF_FILE = REFERENCE_DIR / "evidence_cutoff.txt"

# endregion

# region Study window
STUDY_START_YEAR = 2012
STUDY_END_YEAR = 2024

# endregion

# region Seeds
# Fixed and recorded in reports/repro. Changing any of these invalidates every
# result committed under them, so treat them as protocol rather than tuning knobs.
SAMPLING_SEED = 100_101
SPLIT_SEED = 100_102
MODEL_SEED = 1_001
SEEDS = (1_001, 1_002, 1_003)

# endregion

# region SEC access
# The SEC requires a descriptive User-Agent naming a contact address, and asks for
# no more than ten requests per second. The delay below is deliberately slower
# than the published limit: these scripts are not latency-sensitive and being a
# well-behaved client costs nothing.
SEC_USER_AGENT = "prospective-claims research (d.isham.993@gmail.com)"
SEC_REQUEST_DELAY_SECONDS = 0.15
SEC_TIMEOUT_SECONDS = 30
SEC_MAX_RETRIES = 3

SEC_FRAMES_URL = "https://data.sec.gov/api/xbrl/frames/{namespace}/{element}/{unit}/{period}.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"

# Periods used to prove an element exists in the taxonomy, spanning the study
# window rather than sampling one quarter. A single probe cannot distinguish an
# element that has always been available from one adopted mid-window: the ASC 606
# concepts do not exist before 2018, and their predecessors are being retired, so
# an element that looks universal in 2023 may be missing for a 2013 claim.
TAXONOMY_PROBE_YEARS = (2012, 2018, 2024)
TAXONOMY_PROBE_QUARTER = "Q1"


def probe_periods(instantaneous: bool) -> tuple[str, ...]:
    """Return the frames periods used to verify an element across the study window.

    Args:
        instantaneous: Whether the element is measured at a point in time, which
            requires the ``I`` suffix.

    Returns:
        Frames period strings, earliest first.
    """
    suffix = "I" if instantaneous else ""
    return tuple(f"CY{year}{TAXONOMY_PROBE_QUARTER}{suffix}" for year in TAXONOMY_PROBE_YEARS)

# endregion
