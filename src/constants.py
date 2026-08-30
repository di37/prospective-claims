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
FISCAL_QUARTERS_FILE = REFERENCE_DIR / "fiscal_quarters.csv"
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
SEC_SUBMISSIONS_OVERFLOW_URL = "https://data.sec.gov/submissions/{name}"
SEC_COMPANY_CONCEPT_URL = (
    "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/{namespace}/{element}.json"
)

# Periodic reports the study adjudicates against. Amendments are excluded by
# construction rather than filtered later: a 10-Q/A published after the evidence
# cutoff does not make a claim observable, while the original that arrived on time
# does, so the amendment must never displace it.
PERIODIC_FORMS = ("10-K", "10-Q")

# EDGAR's reportDate is unreliable for a small share of filings. Two failure modes
# appear in the data: the field sometimes duplicates the filing date, giving a
# periodic report a zero-day lag, and it sometimes carries a plausible-looking but
# wrong period on a filing submitted a year later. Both matter because
# fiscal_period is the key the whole adjudication joins on, so a wrong period
# matches a claim to the wrong filing or to none.
#
# Rows are flagged rather than dropped. A short lag is almost certainly a bad
# reportDate; a long one may be genuine delinquency, which the study cares about.
#
# The short threshold is set from the observed distribution rather than picked.
# Lags of 0 to 3 days are six rows across three filers and are impossible: a
# periodic report cannot be filed before its accounting close. Nothing then
# appears until 9 days, after which Delta and Oracle form a coherent cluster at
# 10 to 14 days across dozens of filings. Those two file genuinely fast, and an
# earlier threshold of 15 flagged 40 of their legitimate filings as errors.
MIN_PLAUSIBLE_FILING_LAG_DAYS = 5
MAX_PLAUSIBLE_FILING_LAG_DAYS = {"10-Q": 60, "10-K": 120}

# endregion

# region Transcript corpus
# The transcripts come from a HuggingFace release rather than a vendor feed. The
# chain is kurry/sp500_earnings_transcripts -> Bose345/sp500_earnings_transcripts
# -> this one, each tagged MIT, and none of them naming the vendor the transcripts
# originally came from. Several carry a "TRANSCRIPT SPONSOR" line, which is a
# vendor artefact. An MIT tag applied by an uploader does not grant rights the
# uploader does not hold, so the study treats the text as third-party content:
# it is pulled, never committed, and never redistributed. Released artifacts carry
# offsets and labels plus a script that reconstructs the text from this source.
TRANSCRIPT_REPO = "RudrakshNanavaty/earnings-call-data"
TRANSCRIPT_REPO_FILE = "episodes.parquet"
TRANSCRIPT_RAW_FILE = RAW_DIR / "episodes.parquet"
TRANSCRIPT_SEGMENTS_FILE = INTERIM_DIR / "transcript_segments.parquet"
TRANSCRIPT_COVERAGE_FILE = REFERENCE_DIR / "transcript_coverage.csv"

# The release carries 72 columns of prices, XBRL fundamentals and return labels
# alongside the text. The study reads only identity and transcript: its financial
# facts come from EDGAR through this repository's own reference tables, where the
# as-first-reported rule is enforced, rather than from a third party's join.
TRANSCRIPT_READ_COLUMNS = (
    "episode_id",
    "symbol",
    "company_name",
    "year",
    "quarter",
    "date",
    "earnings_date",
    "sector",
    "earnings_transcript",
)

# A call splits into prepared remarks and Q&A, and the boundary is found by the
# operator handing over to the first analyst. Where the boundary lands is a check
# on whether it was found correctly: across the corpus the split sits at 39 per
# cent of the transcript at the median, with the first and ninety-ninth
# percentiles at 4.5 and 83 per cent. A split below 5 per cent leaves almost no
# prepared remarks and one above 90 per cent almost no Q&A, so both are marked
# low confidence rather than dropped. The band flags 1.7 per cent of splits;
# widening it to 10 and 85 per cent would flag 4.5 per cent, most of them
# ordinary calls.
QA_SPLIT_MIN_FRACTION = 0.05
QA_SPLIT_MAX_FRACTION = 0.90

# endregion

# region Fiscal calendars
# A filer's own calendar decides what "next quarter" means, and it is derived
# from the period ends it actually filed rather than from the fiscalYearEnd field
# EDGAR reports. That field holds one current value, so a filer that changed its
# year end during the window reports only where it ended up.
#
# Two calendar shapes account for all but a handful of filers. A fixed-date year
# end lands on the same calendar date every year, so consecutive years are 365 or
# 366 days apart. A 52/53-week year ends on the same weekday, which makes it drift
# by a day or two annually and inserts a 53rd week roughly every six years, so
# consecutive years are 364 or 371 days apart. The two gap sets do not overlap,
# which is what makes the classification decidable rather than a judgement call.
#
# A filer is classified when at least four fifths of its anchors and gaps agree.
# Below that it is irregular, which in this data means the year end changed
# mid-window rather than that the filer is unclassifiable.
CALENDAR_WEEK_YEAR_GAPS = (364, 371)
CALENDAR_FIXED_YEAR_GAPS = (365, 366)
CALENDAR_MODAL_SHARE = 0.8
CALENDAR_MIN_ANCHORS = 3

# A fixed-date year end may still move by a day: February ends on the 28th or the
# 29th, and a filer whose year ends on the last day of a month follows the month.
CALENDAR_FIXED_DAY_TOLERANCE = 2

# How far a 52/53-week year end may sit from where the filer's most recent one
# sits before it counts as a different year end rather than drift. A 52/53-week
# year end moves by a day or two most years and jumps a week when the 53rd week is
# inserted, so ten days is generous for drift and far short of a month.
CALENDAR_WEEK_DRIFT_DAYS = 10

# No fiscal year is longer than this. A larger gap between annual reports means an
# annual report is missing, not that the year was long, and treating it as one
# year would stretch the quarter boundaries and mislabel every quarter inside it.
FISCAL_YEAR_MAX_DAYS = 380

# endregion

# region Filer selection
# The study set is drawn by revenue rather than market capitalisation, because
# revenue is in XBRL and market capitalisation is not. Filers are ranked at a
# single recent year, which is a survivorship filter: a company that was large in
# 2012 and has since shrunk or delisted cannot appear. See src/reference/filers.py
# for what that costs and why it is accepted here.
FILER_SELECTION_YEAR = "CY2023"
FILER_SELECTION_ELEMENTS = (
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:Revenues",
)
FILER_COUNT = 150
FILER_LOCATION_PREFIX = "US-"
FILERS_FILE = REFERENCE_DIR / "filers.csv"

# The frames API serves whatever a filer tagged, including the scale errors. Tigo
# Energy tagged CY2023 revenue as 145,233,000,000 against total assets of
# 127,777,000, a factor of a thousand out, and ranked 25th on it, above Meta.
#
# Revenue over total assets separates that cleanly. Across the top 300 candidates
# the median is 0.70, the 99th percentile 4.96, and the largest genuine reading is
# 6.5 for World Kinect, a fuel distributor that turns enormous throughput on a
# small balance sheet. The next value up is Tigo at 1,137. Nothing lies between.
#
# The threshold sits at 25 rather than in the middle of that gap. A thousand-fold
# error on an asset-heavy filer, a bank or a utility whose true ratio is near
# 0.05, lands around 50, so a higher cut would let those through while still
# catching Tigo. Four times the largest real observation is far enough above the
# genuine distribution and far enough below any scale error to catch both.
#
# A filer failing the screen is excluded from the ranking, not flagged in place.
# An implausible revenue figure does not make a filer suspect, it makes its rank
# fabricated, and the rule is the largest filers by revenue. Every exclusion is
# named in the provenance record with the figures that caused it.
MAX_REVENUE_TO_ASSETS = 25.0
ASSETS_ELEMENT = "us-gaap:Assets"
ASSETS_PERIOD = f"{FILER_SELECTION_YEAR}Q4I"

# Candidates are screened from the top down, so the pool must be deep enough to
# refill the count after exclusions. Fifty spare is far more than the observed
# exclusion rate of one, and it bounds the per-filer requests needed when the
# assets frame has no row for a candidate.
SCREENING_POOL_MARGIN = 50

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
