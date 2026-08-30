"""Inventory the transcript corpus and write the coverage table.

Produces ``reference/transcript_coverage.csv``, one row per corpus symbol, saying
how much of the study window it covers and whether it maps to a filer in the
study. That table decides which filers the pilot can sample from: a filer with no
transcript contributes no claims however well its filings are covered.

Also writes ``data/interim/transcript_segments.parquet``, one row per call giving
the character offset where prepared remarks end and the analyst Q&A begins. That
file holds offsets, never text, because the transcripts are third-party content
this project does not redistribute.

Reads ``data/raw/episodes.parquet`` from ``scripts/00_pull_transcripts.py`` and
``reference/filers.csv`` with the submissions metadata from
``scripts/03_build_filing_dates.py``, which is where each filer's own tickers come
from. Nothing is fetched.
"""

# region Imports & setup
from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from constants import (  # noqa: E402
    FILERS_FILE,
    INTERIM_DIR,
    QA_SPLIT_MAX_FRACTION,
    QA_SPLIT_MIN_FRACTION,
    REFERENCE_DIR,
    STUDY_END_YEAR,
    STUDY_START_YEAR,
    TRANSCRIPT_COVERAGE_FILE,
    TRANSCRIPT_RAW_FILE,
    TRANSCRIPT_READ_COLUMNS,
    TRANSCRIPT_SEGMENTS_FILE,
)
from corpus import MatchMethod, SplitConfidence, coverage_for, match_all, segment  # noqa: E402
from run_logging import banner, log_detail, log_saved, logged_run, tee_to_logfile  # noqa: E402

PROVENANCE_FILE = REFERENCE_DIR / "transcript_coverage.provenance.json"
FILING_DATES_PROVENANCE = REFERENCE_DIR / "filing_dates.provenance.json"

CSV_COLUMNS = [
    "symbol", "company_name", "cik", "filer_name", "match_method",
    "first_period", "last_period", "quarters_present", "quarters_expected",
    "gaps", "continuous", "calls_split", "calls_unsplit", "calls_low_confidence",
]
SEGMENT_COLUMNS = [
    "episode_id", "symbol", "year", "quarter", "chars",
    "split_offset", "marker", "split_fraction", "confidence",
]

# endregion

# region Loading
def load_study_filers() -> dict[int, tuple[str, tuple[str, ...]]]:
    """Read each study filer's name and its own EDGAR tickers.

    Tickers come from the filer's submissions record rather than the SEC's global
    ticker file, which lists only current registrants and maps a reassigned ticker
    to whichever entity holds it now.

    Returns:
        Name and tickers by CIK, in selection order.

    Raises:
        SystemExit: If an input has not been generated yet.
    """
    for path in (FILERS_FILE, FILING_DATES_PROVENANCE):
        if not path.exists():
            raise SystemExit(f"{path} not found; run the earlier reference scripts first")

    with FILERS_FILE.open(encoding="utf-8") as handle:
        order = [int(row["cik"]) for row in csv.DictReader(handle)]

    meta = json.loads(FILING_DATES_PROVENANCE.read_text())["filers"]
    return {
        cik: (meta[str(cik)]["name"], tuple(meta[str(cik)].get("tickers") or ()))
        for cik in order
        if str(cik) in meta
    }


def read_corpus():
    """Stream the corpus, segmenting each call and collecting coverage.

    The transcript column is the bulk of a 1.2 GB file, so it is read in batches
    and discarded after segmentation rather than held in memory.

    Returns:
        Tuple of segment rows, periods by symbol, company name by symbol, and
        counts by symbol and confidence.

    Raises:
        SystemExit: If the corpus has not been pulled.
    """
    import pyarrow.parquet as pq

    if not TRANSCRIPT_RAW_FILE.exists():
        raise SystemExit(
            f"{TRANSCRIPT_RAW_FILE} not found; run scripts/00_pull_transcripts.py first"
        )

    segments: list[dict] = []
    periods: dict[str, set[tuple[int, int]]] = defaultdict(set)
    names: dict[str, str] = {}
    confidence: dict[str, Counter] = defaultdict(Counter)

    reader = pq.ParquetFile(TRANSCRIPT_RAW_FILE)
    for batch in reader.iter_batches(batch_size=2000, columns=list(TRANSCRIPT_READ_COLUMNS)):
        table = batch.to_pydict()
        for i in range(len(table["symbol"])):
            symbol = (table["symbol"][i] or "").upper()
            if not symbol:
                continue
            year, quarter = table["year"][i], table["quarter"][i]
            found = segment(table["earnings_transcript"][i])

            periods[symbol].add((int(year), int(quarter)))
            if table["company_name"][i] and symbol not in names:
                names[symbol] = table["company_name"][i]
            confidence[symbol][found.confidence.value] += 1

            segments.append({
                "episode_id": table["episode_id"][i],
                "symbol": symbol,
                "year": year,
                "quarter": quarter,
                "chars": found.chars,
                "split_offset": found.split_offset,
                "marker": found.marker,
                "split_fraction": found.split_fraction,
                "confidence": found.confidence.value,
            })
    return segments, periods, names, confidence


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


def write_coverage(rows: list[dict]) -> None:
    """Write the coverage table, sorted so re-runs are byte-identical.

    Args:
        rows: One row per corpus symbol.

    Returns:
        None.
    """
    TRANSCRIPT_COVERAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRANSCRIPT_COVERAGE_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["symbol"]))
    log_saved(TRANSCRIPT_COVERAGE_FILE)


def write_segments(segments: list[dict]) -> None:
    """Write the per-call segmentation offsets.

    Args:
        segments: One row per call.

    Returns:
        None.
    """
    import pandas as pd

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(segments, columns=SEGMENT_COLUMNS)
    frame = frame.sort_values(["symbol", "year", "quarter"]).reset_index(drop=True)
    frame.to_parquet(TRANSCRIPT_SEGMENTS_FILE, index=False)
    log_saved(TRANSCRIPT_SEGMENTS_FILE)


def write_provenance(rows: list[dict], matches, segments: list[dict], symbols: int) -> None:
    """Record how the inventory was built and what it found.

    Args:
        rows: Coverage rows.
        matches: Study filer matches.
        segments: Segmentation rows.
        symbols: Symbols in the corpus.

    Returns:
        None.
    """
    confidence = Counter(s["confidence"] for s in segments)
    methods = Counter(m.method.value for m in matches)
    in_study = [r for r in rows if r["cik"]]
    record = {
        "generated_by": "scripts/05_build_transcript_inventory.py",
        "source_of_truth": "src/corpus/",
        "commit": commit_sha(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "derived_from": [
            "data/raw/episodes.parquet",
            "reference/filers.csv",
            "reference/filing_dates.provenance.json",
        ],
        "study_window": [STUDY_START_YEAR, STUDY_END_YEAR],
        "rules": [
            "Coverage is counted in the corpus's own calendar quarters, not fiscal ones, so a gap is a gap rather than a mapping artefact.",
            "Study filers are matched on tickers from their own EDGAR submissions record, never on the SEC's current-registrant ticker file, which maps a reassigned ticker to whichever entity holds it now.",
            "Where EDGAR and the corpus disagree about identity, the match comes from a short list of aliases checked one at a time against the corpus's company names. Nothing is fuzzy matched.",
            "Segmentation is stored as character offsets, never text, because the transcripts are third-party content this project does not redistribute.",
        ],
        "qa_split_band": [QA_SPLIT_MIN_FRACTION, QA_SPLIT_MAX_FRACTION],
        "counts": {
            "corpus_symbols": symbols,
            "corpus_calls": len(segments),
            "study_filers": len(matches),
            "study_filers_matched": sum(1 for m in matches if m.matched),
            "match_methods": dict(methods),
            "symbols_continuous_in_window": sum(1 for r in rows if r["continuous"]),
            "study_filers_continuous": sum(1 for r in in_study if r["continuous"]),
            "segmentation": dict(confidence),
        },
        "unmatched_study_filers": [
            {"cik": m.cik, "name": m.name, "reason": m.method.value,
             "edgar_tickers": list(m.edgar_tickers)}
            for m in matches if not m.matched
        ],
        "aliases_used": [
            {"cik": m.cik, "name": m.name, "symbol": m.symbol, "why": m.note}
            for m in matches if m.method is MatchMethod.VERIFIED_ALIAS
        ],
        "limitations": [
            "The corpus is a 685-ticker subset rather than full S&P 500 history: Arrow Electronics, Avnet, Flex, US Foods and others are listed, in the study set, and absent from it.",
            "Partnerships and debt-issuing subsidiaries hold no earnings call, so their absence is structural rather than a gap in the corpus.",
            "The corpus labels each call with its own year and quarter. Reconciling those to a filer's fiscal calendar is left to reference/fiscal_quarters.csv.",
        ],
    }
    PROVENANCE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log_saved(PROVENANCE_FILE)


# endregion

# region Main
def main() -> None:
    """Inventory the corpus and write the tables.

    Returns:
        None.
    """
    banner("Transcript inventory")
    log_detail("derived from the pulled corpus and the reference tables; nothing is fetched")

    filers = load_study_filers()
    with logged_run("Reading and segmenting the corpus"):
        segments, periods, names, confidence = read_corpus()

    symbols = frozenset(periods)
    matches = match_all(filers, symbols)
    by_symbol = {m.symbol: m for m in matches if m.matched}

    rows = []
    for symbol in sorted(periods):
        cover = coverage_for(
            symbol, names.get(symbol), periods[symbol], STUDY_START_YEAR, STUDY_END_YEAR
        )
        match = by_symbol.get(symbol)
        counts = confidence[symbol]
        rows.append({
            "symbol": cover.symbol,
            "company_name": cover.company_name or "",
            "cik": match.cik if match else "",
            "filer_name": match.name if match else "",
            "match_method": match.method.value if match else "",
            "first_period": cover.first_period or "",
            "last_period": cover.last_period or "",
            "quarters_present": cover.quarters_present,
            "quarters_expected": cover.quarters_expected,
            "gaps": cover.gaps,
            "continuous": "yes" if cover.continuous else "",
            "calls_split": counts[SplitConfidence.OK.value],
            "calls_unsplit": counts[SplitConfidence.NOT_FOUND.value] + counts[SplitConfidence.EMPTY.value],
            "calls_low_confidence": counts[SplitConfidence.IMPLAUSIBLE_POSITION.value],
        })

    banner("Writing")
    write_coverage(rows)
    write_segments(segments)
    write_provenance(rows, matches, segments, len(symbols))

    in_study = [r for r in rows if r["cik"]]
    log_detail(f"{len(segments):,} calls across {len(symbols)} symbols")
    log_detail(f"{sum(1 for r in rows if r['continuous'])} symbols cover every quarter of "
               f"{STUDY_START_YEAR}-{STUDY_END_YEAR}")

    banner("The study set against the corpus")
    methods = Counter(m.method.value for m in matches)
    for method, count in methods.most_common():
        log_detail(f"  {method:<22} {count:>3} filers")
    log_detail(f"{len(in_study)} of {len(filers)} study filers have transcripts")
    log_detail(f"{sum(1 for r in in_study if r['continuous'])} of those cover the whole window")

    unmatched = [m for m in matches if not m.matched]
    if unmatched:
        banner("Study filers with no transcript")
        log_detail("Absent from the corpus means listed but not carried; not listed")
        log_detail("means the filer has no ticker and holds no public call.")
        for m in sorted(unmatched, key=lambda m: m.method.value):
            log_detail(f"  {m.method.value:<22} {m.name[:38]:<38} "
                       f"{','.join(m.edgar_tickers)[:16]}")

    banner("Prepared remarks and Q&A")
    confidence_counts = Counter(s["confidence"] for s in segments)
    total = len(segments)
    for label in (SplitConfidence.OK, SplitConfidence.IMPLAUSIBLE_POSITION,
                  SplitConfidence.NOT_FOUND, SplitConfidence.EMPTY):
        count = confidence_counts[label.value]
        if count:
            log_detail(f"  {label.value:<22} {count:>6,}  {100*count/total:>5.1f}%")
    log_detail(f"failure rate: {100*(total - confidence_counts[SplitConfidence.OK.value])/total:.1f}%")


if __name__ == "__main__":
    tee_to_logfile()
    main()
# endregion
