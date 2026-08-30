"""Pull periodic filing dates from EDGAR and write the filing dates table.

Produces ``reference/filing_dates.csv``, which is what makes the evidence
maturity date computable. A claim is observable only once the filings covering
its evaluation window have actually been published, and the fiscal calendar
cannot supply that: it maps a phrase onto a period, not a period onto the date
its report reached the SEC.

Two rules the study depends on, both enforced in code rather than by convention.
Amendments never appear, because a 10-Q/A published after the evidence cutoff does
not make a claim observable while the original that arrived on time does. Where a
period was filed more than once, the earliest filing wins, since that is when the
information became available.

Filers come from ``reference/filers.csv``. Run ``scripts/02_select_filers.py``
first.
"""

# region Imports & setup
from __future__ import annotations

import csv
import json
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from constants import (  # noqa: E402
    FILERS_FILE,
    FILING_DATES_FILE,
    MAX_PLAUSIBLE_FILING_LAG_DAYS,
    MIN_PLAUSIBLE_FILING_LAG_DAYS,
    PERIODIC_FORMS,
    REFERENCE_DIR,
    SEC_REQUEST_DELAY_SECONDS,
    STUDY_END_YEAR,
    STUDY_START_YEAR,
)
from edgar import fetch_filer, first_filing_per_period  # noqa: E402
from run_logging import banner, log_detail, log_saved, logged_run, tee_to_logfile  # noqa: E402

PROVENANCE_FILE = REFERENCE_DIR / "filing_dates.provenance.json"
CSV_COLUMNS = ["cik", "fiscal_period", "form_type", "filed_date", "lag_days", "suspect", "accession"]

# A filer covering the whole window files four periodic reports a year: three
# 10-Qs and a 10-K that replaces the fourth quarter.
EXPECTED_PER_YEAR = 4

# endregion

# region Filers
def load_filers() -> list[tuple[int, str]]:
    """Read the selected filers.

    Returns:
        Tuples of CIK and entity name, in selection order.

    Raises:
        SystemExit: If the filer table has not been generated yet.
    """
    if not FILERS_FILE.exists():
        raise SystemExit(f"{FILERS_FILE} not found; run scripts/02_select_filers.py first")
    with FILERS_FILE.open(encoding="utf-8") as handle:
        return [(int(row["cik"]), row["name"]) for row in csv.DictReader(handle)]


# endregion

# region Collection
def classify_lag(form: str, lag: int) -> str:
    """Judge whether the gap between period end and filing date is plausible.

    A periodic report cannot be filed before the period it covers has ended, and
    in practice not within a fortnight of it. A lag below that means EDGAR's
    reportDate is wrong, not that the filer was fast.

    A lag far past the statutory deadline is ambiguous. It may be a wrong
    reportDate, or it may be genuine delinquency, which the study treats as its
    own case. Both are surfaced rather than resolved here.

    Args:
        form: Form type.
        lag: Days between period end and filing date.

    Returns:
        Empty string when plausible, otherwise a short reason.
    """
    if lag < MIN_PLAUSIBLE_FILING_LAG_DAYS:
        return "lag_implausibly_short"
    if lag > MAX_PLAUSIBLE_FILING_LAG_DAYS.get(form, 120):
        return "lag_long"
    return ""


def in_window(year: int) -> bool:
    """Check whether a period year falls inside the study window.

    Args:
        year: Calendar year of the period end.

    Returns:
        True if the year is inside the window.
    """
    return STUDY_START_YEAR <= year <= STUDY_END_YEAR


def collect(filers: list[tuple[int, str]]) -> tuple[list[dict], dict[str, object]]:
    """Fetch every filer's periodic filings and reduce them to one row per period.

    Args:
        filers: Tuples of CIK and entity name.

    Returns:
        The rows to write, and a per-filer coverage report.
    """
    rows: list[dict] = []
    coverage: dict[str, object] = {}
    failures: list[str] = []

    for position, (cik, name) in enumerate(filers, start=1):
        try:
            submissions = fetch_filer(cik)
        except Exception as exc:  # noqa: BLE001  one filer failing must not lose the rest
            failures.append(f"{cik} {name}: {type(exc).__name__}")
            log_detail(f"FAIL  {position:>3}/{len(filers)}  {name[:44]:<44} {type(exc).__name__}")
            continue

        deduped = first_filing_per_period(submissions.filings)
        windowed = [f for f in deduped if in_window(f.period_end.year)]

        for filing in windowed:
            lag = (filing.filed_date - filing.period_end).days
            rows.append({
                "cik": filing.cik,
                "fiscal_period": filing.period_end.isoformat(),
                "form_type": filing.form,
                "filed_date": filing.filed_date.isoformat(),
                "lag_days": lag,
                "suspect": classify_lag(filing.form, lag),
                "accession": filing.accession,
            })

        years = {f.period_end.year for f in windowed}
        expected = (STUDY_END_YEAR - STUDY_START_YEAR + 1) * EXPECTED_PER_YEAR
        coverage[str(cik)] = {
            "name": submissions.name,
            "fiscal_year_end": submissions.fiscal_year_end,
            "tickers": list(submissions.tickers),
            "filings_in_window": len(windowed),
            "years_covered": sorted(years),
            "complete": len(windowed) >= expected,
        }
        marker = "ok   " if len(windowed) >= expected else "PART "
        log_detail(f"{marker} {position:>3}/{len(filers)}  {submissions.name[:44]:<44} "
                   f"{len(windowed):>3} filings, {len(years):>2} years")
        time.sleep(SEC_REQUEST_DELAY_SECONDS)

    if failures:
        coverage["_failures"] = failures
    return rows, coverage


# endregion

# region Serialisation
def commit_sha() -> str:
    """Return the current commit, or a marker when git is unavailable.

    Returns:
        Short commit hash, or ``"unknown"``.
    """
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001  git absent or not a repository
        return "unknown"


def write_table(rows: list[dict]) -> None:
    """Write the filing dates CSV, sorted so re-runs are byte-identical.

    Args:
        rows: One row per filer and period.

    Returns:
        None.
    """
    FILING_DATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda r: (r["cik"], r["fiscal_period"], r["form_type"]))
    with FILING_DATES_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(ordered)
    log_saved(FILING_DATES_FILE)


def write_provenance(rows: list[dict], coverage: dict[str, object]) -> None:
    """Write the record of what was pulled and how complete it is.

    Args:
        rows: The rows written.
        coverage: Per-filer coverage report.

    Returns:
        None.
    """
    filers = [v for k, v in coverage.items() if k != "_failures"]
    lags = [r["lag_days"] for r in rows]
    suspects = Counter(r["suspect"] for r in rows if r["suspect"])
    record = {
        "generated_by": "scripts/03_build_filing_dates.py",
        "commit": commit_sha(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "study_window": [STUDY_START_YEAR, STUDY_END_YEAR],
        "forms": list(PERIODIC_FORMS),
        "rules": [
            "Amendments are excluded at extraction, never filtered later.",
            "Where a period was filed more than once, the earliest filing wins.",
            "Rows whose filing lag is implausible are flagged in the suspect column, not dropped.",
        ],
        "lag_thresholds": {
            "min_plausible_days": MIN_PLAUSIBLE_FILING_LAG_DAYS,
            "max_plausible_days": MAX_PLAUSIBLE_FILING_LAG_DAYS,
        },
        "counts": {
            "filers_requested": len(filers),
            "filers_with_rows": sum(1 for f in filers if f["filings_in_window"] > 0),
            "filers_complete": sum(1 for f in filers if f["complete"]),
            "rows": len(rows),
            "form_breakdown": dict(Counter(r["form_type"] for r in rows)),
            "suspect_rows": dict(suspects),
        },
        "filing_lag_days": {
            "median": sorted(lags)[len(lags) // 2] if lags else None,
            "min": min(lags) if lags else None,
            "max": max(lags) if lags else None,
        },
        "filers": coverage,
    }
    PROVENANCE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log_saved(PROVENANCE_FILE)


# endregion

# region Main
def main() -> None:
    """Pull filing dates for every selected filer and write the table.

    Returns:
        None.
    """
    filers = load_filers()
    banner("Filing dates")
    log_detail(f"{len(filers)} filers, window {STUDY_START_YEAR} to {STUDY_END_YEAR}, forms {', '.join(PERIODIC_FORMS)}")

    with logged_run("Fetching submissions"):
        rows, coverage = collect(filers)

    banner("Writing")
    write_table(rows)
    write_provenance(rows, coverage)

    entries = [v for k, v in coverage.items() if k != "_failures"]
    incomplete = sorted(
        (v for v in entries if not v["complete"]),
        key=lambda v: v["filings_in_window"],
    )
    log_detail(f"{len(rows)} rows across {len(entries)} filers")

    flagged = [r for r in rows if r["suspect"]]
    if flagged:
        banner("Rows with an implausible filing lag")
        log_detail("EDGAR's reportDate is wrong for a small share of filings, and")
        log_detail("fiscal_period is the key adjudication joins on, so these are")
        log_detail("flagged rather than dropped.")
        for reason, n in Counter(r["suspect"] for r in flagged).most_common():
            log_detail(f"  {reason:<24} {n:>4} rows")
        for row in sorted(flagged, key=lambda r: r["lag_days"])[:5]:
            log_detail(f"    {row['lag_days']:>4}d  cik {row['cik']:<8} {row['form_type']}  "
                       f"period={row['fiscal_period']} filed={row['filed_date']}")
    if incomplete:
        banner("Filers not covering the full window")
        log_detail("A claim from a year with no filing cannot be scored, so these")
        log_detail("reduce the sample rather than producing a wrong answer.")
        for entry in incomplete[:15]:
            years = entry["years_covered"]
            span = f"{years[0]}-{years[-1]}" if years else "none"
            log_detail(f"  {entry['name'][:44]:<44} {entry['filings_in_window']:>3} filings, {span}")
        if len(incomplete) > 15:
            log_detail(f"  and {len(incomplete) - 15} more; see the provenance record")


if __name__ == "__main__":
    tee_to_logfile()
    main()
# endregion
