"""Derive each filer's fiscal calendar and write the calendar reference tables.

Produces ``reference/fiscal_calendar.csv``, one row per filer describing the
shape of its fiscal year, and ``reference/fiscal_quarters.csv``, one row per
observed fiscal period labelled with the quarter it closes. Section 5.5 of the
annotation manual resolves "next quarter" against these rather than against the
calendar year.

Nothing is fetched. The calendar is derived from ``reference/filing_dates.csv``,
which already holds every 10-K and 10-Q period end across the study window, so
this script is offline and its output changes only when the filing dates do.

Rows flagged ``suspect`` in the filing dates are excluded before deriving. A
wrong period end is exactly what would corrupt a calendar, and General Electric
demonstrates it: four of its filings carry the filing date as the period end, one
of them the annual report that anchors fiscal 2014.
"""

# region Imports & setup
from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from constants import (  # noqa: E402
    CALENDAR_FIXED_DAY_TOLERANCE,
    CALENDAR_MIN_ANCHORS,
    CALENDAR_MODAL_SHARE,
    CALENDAR_WEEK_DRIFT_DAYS,
    FILERS_FILE,
    FILING_DATES_FILE,
    FISCAL_CALENDAR_FILE,
    FISCAL_QUARTERS_FILE,
    FISCAL_YEAR_MAX_DAYS,
    REFERENCE_DIR,
    STUDY_END_YEAR,
    STUDY_START_YEAR,
)
from reference import CalendarType, derive  # noqa: E402
from run_logging import banner, log_detail, log_saved, logged_run, tee_to_logfile  # noqa: E402

PROVENANCE_FILE = REFERENCE_DIR / "fiscal_calendar.provenance.json"
FILING_DATES_PROVENANCE = REFERENCE_DIR / "filing_dates.provenance.json"

CALENDAR_COLUMNS = [
    "cik", "name", "calendar_type", "declared_year_end",
    "year_end_month", "year_end_day", "year_end_weekday",
    "year_end_changed", "changed_at", "earlier_calendar_type",
    "annual_anchors", "fiscal_years", "suspect_anchors", "missing_fiscal_years",
]
QUARTER_COLUMNS = ["cik", "fiscal_year", "quarter", "period_end", "form_type", "days_from_year_start"]

WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# endregion

# region Loading
def load_periods() -> tuple[dict[int, dict[str, list[date]]], int]:
    """Read the filing dates, dropping the rows the table does not trust.

    Returns:
        Tuple of period ends by CIK and form, and the number of rows dropped.

    Raises:
        SystemExit: If the filing dates table has not been generated yet.
    """
    if not FILING_DATES_FILE.exists():
        raise SystemExit(f"{FILING_DATES_FILE} not found; run scripts/03_build_filing_dates.py first")

    periods: dict[int, dict[str, list[date]]] = {}
    dropped = 0
    with FILING_DATES_FILE.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["suspect"]:
                dropped += 1
                continue
            cik = int(row["cik"])
            bucket = periods.setdefault(cik, {"10-K": [], "10-Q": []})
            bucket[row["form_type"]].append(date.fromisoformat(row["fiscal_period"]))
    return periods, dropped


def load_filer_metadata() -> tuple[list[int], dict[int, dict]]:
    """Read the study filers and the metadata the filing dates pull recorded.

    Returns:
        Tuple of CIKs in selection order and per-filer metadata by CIK.

    Raises:
        SystemExit: If either input has not been generated yet.
    """
    for path in (FILERS_FILE, FILING_DATES_PROVENANCE):
        if not path.exists():
            raise SystemExit(f"{path} not found; run the earlier reference scripts first")

    with FILERS_FILE.open(encoding="utf-8") as handle:
        ciks = [int(row["cik"]) for row in csv.DictReader(handle)]

    record = json.loads(FILING_DATES_PROVENANCE.read_text())
    meta = {int(k): v for k, v in record["filers"].items() if k != "_failures"}
    return ciks, meta


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


def write_calendar(calendars: list) -> None:
    """Write one row per filer describing its fiscal year.

    Args:
        calendars: Derived calendars, in selection order.

    Returns:
        None.
    """
    FISCAL_CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FISCAL_CALENDAR_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CALENDAR_COLUMNS)
        writer.writeheader()
        for calendar in calendars:
            years = sorted({q.fiscal_year for q in calendar.quarters})
            writer.writerow({
                "cik": calendar.cik,
                "name": calendar.name,
                "calendar_type": calendar.calendar_type.value,
                "declared_year_end": calendar.declared_year_end or "",
                "year_end_month": calendar.modal_month or "",
                "year_end_day": calendar.modal_day or "",
                "year_end_weekday": (
                    WEEKDAY_NAMES[calendar.modal_weekday] if calendar.modal_weekday is not None else ""
                ),
                "year_end_changed": "yes" if calendar.year_end_changed else "",
                "changed_at": calendar.changed_at.isoformat() if calendar.changed_at else "",
                "earlier_calendar_type": (
                    calendar.earlier_calendar_type.value if calendar.earlier_calendar_type else ""
                ),
                "annual_anchors": len(calendar.anchors),
                "fiscal_years": f"{years[0]}-{years[-1]}" if years else "",
                "suspect_anchors": " ".join(a.isoformat() for a in calendar.suspect_anchors),
                "missing_fiscal_years": " ".join(str(y) for y in calendar.missing_fiscal_years),
            })
    log_saved(FISCAL_CALENDAR_FILE)


def write_quarters(calendars: list) -> None:
    """Write one row per observed fiscal period, labelled with its quarter.

    Args:
        calendars: Derived calendars.

    Returns:
        None.
    """
    rows = [
        {
            "cik": quarter.cik,
            "fiscal_year": quarter.fiscal_year,
            "quarter": quarter.quarter,
            "period_end": quarter.period_end.isoformat(),
            "form_type": quarter.form_type,
            "days_from_year_start": quarter.days_from_year_start,
        }
        for calendar in calendars
        for quarter in calendar.quarters
    ]
    rows.sort(key=lambda r: (r["cik"], r["period_end"]))
    with FISCAL_QUARTERS_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUARTER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    log_saved(FISCAL_QUARTERS_FILE)


def count_unassigned(
    periods: dict[int, dict[str, list[date]]],
    calendars: list,
) -> dict[str, int]:
    """Account for every clean filing that carries no quarter label.

    There are two reasons, and they are not the same thing. A quarter filed after
    the filer's last annual report belongs to a fiscal year the study window never
    closes, which is expected at the edge of any window. A quarter sitting inside a
    gap between anchors belongs to a year whose annual report is missing or was a
    transition period, which is a defect in the source rather than an edge effect.

    Args:
        periods: Clean period ends by CIK and form.
        calendars: Derived calendars.

    Returns:
        Counts by reason. Reporting one total would hide the difference.
    """
    labelled = {(c.cik, q.period_end) for c in calendars for q in c.quarters}
    after, inside = 0, 0
    for calendar in calendars:
        bucket = periods.get(calendar.cik, {"10-K": [], "10-Q": []})
        last_anchor = max(bucket["10-K"], default=None)
        for period_end in bucket["10-Q"]:
            if (calendar.cik, period_end) in labelled:
                continue
            if last_anchor is None or period_end > last_anchor:
                after += 1
            else:
                inside += 1
    return {"after_the_last_annual_anchor": after, "inside_a_gap_between_anchors": inside}


def write_provenance(calendars: list, dropped: int, unassigned: dict[str, int]) -> None:
    """Write the record of how the calendars were derived.

    Args:
        calendars: Derived calendars.
        dropped: Suspect filing rows excluded before deriving.
        unassigned: Clean filing rows outside every fiscal year, by reason.

    Returns:
        None.
    """
    changed = [c for c in calendars if c.year_end_changed]
    suspect = [c for c in calendars if c.suspect_anchors]
    missing = [c for c in calendars if c.missing_fiscal_years]
    record = {
        "generated_by": "scripts/04_build_fiscal_calendar.py",
        "source_of_truth": "src/reference/calendar.py",
        "commit": commit_sha(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "derived_from": ["reference/filing_dates.csv", "reference/filers.csv"],
        "study_window": [STUDY_START_YEAR, STUDY_END_YEAR],
        "rules": [
            "Every 10-K period end is an annual anchor; the 10-Q period ends between consecutive anchors are its quarters.",
            "Rows flagged suspect in filing_dates.csv are excluded, because a wrong period end corrupts the calendar it anchors.",
            "A fiscal year is labelled by the calendar year it ends in. Filers do not agree with each other on this, so the label is a deterministic convention rather than the filer's own name for the year.",
            "Quarters are labelled by elapsed fraction of the fiscal year, and the observed dates are kept rather than assumed evenly spaced.",
            "Where the year end changed, the shape reported is the one in force after the change and the earlier one is recorded beside it.",
        ],
        "thresholds": {
            "modal_share": CALENDAR_MODAL_SHARE,
            "min_anchors_to_classify": CALENDAR_MIN_ANCHORS,
            "fixed_day_tolerance": CALENDAR_FIXED_DAY_TOLERANCE,
            "week_drift_days": CALENDAR_WEEK_DRIFT_DAYS,
            "fiscal_year_max_days": FISCAL_YEAR_MAX_DAYS,
        },
        "counts": {
            "filers": len(calendars),
            "calendar_types": dict(Counter(c.calendar_type.value for c in calendars)),
            "year_end_changed": len(changed),
            "with_suspect_anchors": len(suspect),
            "with_missing_years": len(missing),
            "quarters": sum(len(c.quarters) for c in calendars),
            "suspect_filing_rows_excluded": dropped,
            "clean_rows_outside_any_fiscal_year": unassigned,
            "quarters_labelled": sum(len(c.quarters) for c in calendars),
        },
        "year_end_changes": [
            {
                "cik": c.cik, "name": c.name, "changed_at": c.changed_at.isoformat(),
                "from": c.earlier_calendar_type.value if c.earlier_calendar_type else None,
                "to": c.calendar_type.value,
            }
            for c in changed
        ],
        "suspect_anchors": [
            {"cik": c.cik, "name": c.name, "anchors": [a.isoformat() for a in c.suspect_anchors]}
            for c in suspect
        ],
        "missing_fiscal_years": [
            {"cik": c.cik, "name": c.name, "years": list(c.missing_fiscal_years)} for c in missing
        ],
        "limitations": [
            "A year end that changed in the last year or two of the window cannot be told from a wrong period end, because one or two anchors do not establish a regime. Such a filer is reported as having suspect anchors instead.",
            "Filers with fewer than three annual anchors are classified insufficient_data rather than guessed at.",
            "The fiscal_year column does not match every filer's own name for the year. Walmart calls the year ending January 2024 fiscal 2024 and Target calls the year ending January 2023 fiscal 2022, so no single rule matches both. Join on period_end, not on fiscal_year.",
            "Quarter labels come from elapsed fraction of the fiscal year, so a filer that filed an unusual number of 10-Qs in a year may carry a repeated or missing quarter number.",
        ],
    }
    PROVENANCE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log_saved(PROVENANCE_FILE)


# endregion

# region Main
def main() -> None:
    """Derive every filer's calendar and write the tables.

    Returns:
        None.
    """
    banner("Fiscal calendars")
    log_detail("derived from filing_dates.csv; nothing is fetched")

    periods, dropped = load_periods()
    ciks, meta = load_filer_metadata()
    log_detail(f"{len(ciks)} filers, {dropped} suspect filing rows excluded")

    calendars = []
    with logged_run("Deriving"):
        for cik in ciks:
            bucket = periods.get(cik, {"10-K": [], "10-Q": []})
            calendars.append(
                derive(
                    cik,
                    meta[cik]["name"],
                    meta[cik]["fiscal_year_end"],
                    bucket["10-K"],
                    bucket["10-Q"],
                )
            )

    unassigned = count_unassigned(periods, calendars)

    banner("Writing")
    write_calendar(calendars)
    write_quarters(calendars)
    write_provenance(calendars, dropped, unassigned)

    counts = Counter(c.calendar_type.value for c in calendars)
    labelled = sum(len(c.quarters) for c in calendars)
    log_detail(f"{labelled:,} labelled periods across {len(calendars)} filers")
    for kind in (CalendarType.FIXED_DATE, CalendarType.WEEK_52_53, CalendarType.IRREGULAR,
                 CalendarType.INSUFFICIENT_DATA):
        if counts.get(kind.value):
            log_detail(f"  {kind.value:<20} {counts[kind.value]:>3} filers")
    log_detail(f"{unassigned['after_the_last_annual_anchor']} quarters belong to a fiscal year "
               "the window does not close")
    log_detail(f"{unassigned['inside_a_gap_between_anchors']} quarters fall in a gap left by a "
               "missing or transition annual report")

    changed = [c for c in calendars if c.year_end_changed]
    if changed:
        banner("Filers whose fiscal year end changed")
        log_detail("These need their own handling; the manual resolves a quarter")
        log_detail("differently on each side of the change.")
        for c in changed:
            was = c.earlier_calendar_type.value if c.earlier_calendar_type else "unknown"
            log_detail(f"  {c.name[:38]:<38} {was} -> {c.calendar_type.value} at {c.changed_at}")

    flagged = [c for c in calendars if c.suspect_anchors or c.missing_fiscal_years]
    if flagged:
        banner("Anchors the derivation does not trust")
        log_detail("A period end that disagrees with its neighbours is more likely")
        log_detail("a wrong reportDate than a real change of calendar.")
        for c in flagged:
            parts = []
            if c.suspect_anchors:
                parts.append("suspect " + " ".join(a.isoformat() for a in c.suspect_anchors))
            if c.missing_fiscal_years:
                parts.append("missing " + " ".join(str(y) for y in c.missing_fiscal_years))
            log_detail(f"  {c.name[:38]:<38} {', '.join(parts)}")


if __name__ == "__main__":
    tee_to_logfile()
    main()
# endregion
