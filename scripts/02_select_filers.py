"""Select the study's filers by revenue and write the filer table.

Produces ``reference/filers.csv``, the join key for every other reference table
and the set the pilot samples from. Filers are ranked by annual revenue from the
SEC frames API rather than chosen by hand, so the selection is reproducible and
its limitations are stated rather than implicit. ``src/reference/filers.py``
records what the rule costs.

Candidates are screened on revenue over total assets before the ranking is taken,
because the frames API serves whatever a filer tagged and some of those tags are
off by a factor of a thousand. Exclusions are named in the provenance record with
the figures that caused them.

The definitive study set is this list intersected with the transcript corpus,
since a filer with no transcript contributes no claims.
"""

# region Imports & setup
from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from constants import (  # noqa: E402
    ASSETS_ELEMENT,
    ASSETS_PERIOD,
    FILER_COUNT,
    FILER_LOCATION_PREFIX,
    FILER_SELECTION_ELEMENTS,
    FILER_SELECTION_YEAR,
    FILERS_FILE,
    MAX_REVENUE_TO_ASSETS,
    REFERENCE_DIR,
    SCREENING_POOL_MARGIN,
    SEC_REQUEST_DELAY_SECONDS,
)
from edgar import fetch_frame, latest_value_in_year  # noqa: E402
from reference import rank_candidates, select  # noqa: E402
from run_logging import banner, log_detail, log_saved, logged_run, tee_to_logfile  # noqa: E402

PROVENANCE_FILE = REFERENCE_DIR / "filers.provenance.json"
CSV_COLUMNS = [
    "cik", "name", "location", "revenue", "assets",
    "revenue_to_assets", "rank", "source_element",
]
SELECTION_CALENDAR_YEAR = int(FILER_SELECTION_YEAR.removeprefix("CY"))

# endregion

# region Assets
def resolve_assets(ciks: list[int]) -> tuple[dict[int, float], list[int]]:
    """Find total assets for the screening pool.

    One frame request covers roughly 98 per cent of the pool. The rest are filers
    whose year end sits away from the frame's instant or who registered recently,
    and each of those costs one request.

    Args:
        ciks: CIKs in the screening pool.

    Returns:
        Tuple of assets by CIK and the CIKs no figure was found for.
    """
    wanted = set(ciks)
    frame = fetch_frame(ASSETS_ELEMENT, "USD", ASSETS_PERIOD)
    assets = {fact.cik: fact.value for fact in frame if fact.cik in wanted}
    log_detail(f"{ASSETS_ELEMENT} at {ASSETS_PERIOD}: {len(frame):,} filers, {len(assets)} in pool")

    missing = [cik for cik in ciks if cik not in assets]
    unresolved: list[int] = []
    for cik in missing:
        found = latest_value_in_year(cik, ASSETS_ELEMENT, "USD", SELECTION_CALENDAR_YEAR)
        if found is None:
            unresolved.append(cik)
        else:
            assets[cik] = found.value
        time.sleep(SEC_REQUEST_DELAY_SECONDS)

    log_detail(f"{len(missing)} not in the frame, {len(missing) - len(unresolved)} resolved per filer")
    return assets, unresolved


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


def write_table(filers: tuple) -> None:
    """Write the filer CSV.

    Args:
        filers: Selected filers, largest first.

    Returns:
        None.
    """
    FILERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FILERS_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for filer in filers:
            writer.writerow({
                "cik": filer.cik,
                "name": filer.name,
                "location": filer.location,
                "revenue": int(filer.revenue),
                "assets": "" if filer.assets is None else int(filer.assets),
                "revenue_to_assets": (
                    "" if filer.revenue_to_assets is None else f"{filer.revenue_to_assets:.3f}"
                ),
                "rank": filer.rank,
                "source_element": filer.source_element,
            })
    log_saved(FILERS_FILE)


def write_provenance(selection, candidates: int, frame_sizes: dict[str, int], unresolved: list[int]) -> None:
    """Write the record of how the selection was made.

    Args:
        selection: The selection outcome, including exclusions.
        candidates: How many US candidates were ranked.
        frame_sizes: Row count per source element.
        unresolved: CIKs in the pool with no assets figure anywhere.

    Returns:
        None.
    """
    filers = selection.filers
    record = {
        "generated_by": "scripts/02_select_filers.py",
        "source_of_truth": "src/reference/filers.py",
        "commit": commit_sha(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "selection": {
            "year": FILER_SELECTION_YEAR,
            "elements": list(FILER_SELECTION_ELEMENTS),
            "location_prefix": FILER_LOCATION_PREFIX,
            "count": FILER_COUNT,
        },
        "screen": {
            "rule": "revenue / total assets must not exceed the threshold",
            "assets_element": ASSETS_ELEMENT,
            "assets_period": ASSETS_PERIOD,
            "max_revenue_to_assets": MAX_REVENUE_TO_ASSETS,
            "pool_size": FILER_COUNT + SCREENING_POOL_MARGIN,
            "excluded": [exclusion.model_dump() for exclusion in selection.excluded],
            "kept_without_an_assets_figure": list(selection.unscreened),
            "no_assets_figure_anywhere": unresolved,
        },
        "candidates_per_element": frame_sizes,
        "candidates_after_location_filter": candidates,
        "limitations": [
            "Ranking at one recent year is a survivorship filter: filers large in 2012 that have since shrunk or delisted cannot appear.",
            "Revenue is a size proxy, not market capitalisation, and over-weights low-margin distribution: three drug wholesalers outrank Microsoft.",
            "Whether a financial firm appears is decided by tagging practice rather than size. Goldman Sachs, Morgan Stanley, Wells Fargo and Truist tag neither revenue element, so no cutoff admits them.",
            "The per-CIK dedupe cannot see one business filing under two CIKs, so several corporate families hold more than one slot.",
            "The definitive study set is this list intersected with the transcript corpus.",
        ],
        "selected": len(filers),
        "revenue_range_usd": [int(filers[-1].revenue), int(filers[0].revenue)] if filers else [],
    }
    PROVENANCE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log_saved(PROVENANCE_FILE)


# endregion

# region Main
def main() -> None:
    """Select filers and write the table.

    Returns:
        None.
    """
    banner("Filer selection")
    log_detail(f"ranking by revenue at {FILER_SELECTION_YEAR}, keeping the largest {FILER_COUNT}")

    frames = {}
    with logged_run("Fetching revenue frames"):
        for element in FILER_SELECTION_ELEMENTS:
            facts = fetch_frame(element, "USD", FILER_SELECTION_YEAR)
            frames[element] = facts
            log_detail(f"{element:<58} {len(facts):>5} filers")
            time.sleep(SEC_REQUEST_DELAY_SECONDS)

    candidates = rank_candidates(frames, FILER_LOCATION_PREFIX)
    log_detail(f"{len(candidates):,} US candidates after the location filter")

    pool = candidates[: FILER_COUNT + SCREENING_POOL_MARGIN]
    with logged_run("Screening on revenue over total assets"):
        assets, unresolved = resolve_assets([candidate.cik for candidate in pool])

    selection = select(pool, assets, FILER_COUNT, MAX_REVENUE_TO_ASSETS)

    banner("Writing")
    write_table(selection.filers)
    write_provenance(selection, len(candidates), {k: len(v) for k, v in frames.items()}, unresolved)

    filers = selection.filers
    log_detail(f"selected {len(filers)} filers")
    log_detail(f"revenue range: {filers[-1].revenue/1e9:,.1f}B to {filers[0].revenue/1e9:,.0f}B")

    if selection.excluded:
        log_detail(f"excluded {len(selection.excluded)} on the plausibility screen:")
        for exclusion in selection.excluded:
            log_detail(
                f"  would have ranked {exclusion.would_have_ranked:>3}. "
                f"{exclusion.name[:34]:<34} "
                f"revenue {exclusion.revenue/1e9:>8,.1f}B against assets {exclusion.assets/1e9:>6,.2f}B "
                f"= {exclusion.revenue_to_assets:,.0f}x"
            )
    else:
        log_detail("no candidate failed the plausibility screen")

    if selection.unscreened:
        log_detail(f"{len(selection.unscreened)} selected filers had no assets figure to screen against")

    log_detail("largest five:")
    for filer in filers[:5]:
        log_detail(f"  {filer.rank:>3}. {filer.name[:44]:<44} {filer.revenue/1e9:>8,.0f}B")


if __name__ == "__main__":
    tee_to_logfile()
    main()
# endregion
