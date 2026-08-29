"""Verify the curated metric definitions against the SEC and write the metric class table.

Produces ``reference/metric_classes.csv`` from the definitions in
``src/reference/metrics.py``. Nothing about the table is authored here: this
script checks and serialises, so re-running it reproduces the file and re-proves
every taxonomy element against the live SEC frames API.

Verification is the point of running it at all. An element name that is
misspelled, deprecated, or in the wrong namespace returns 404, and the script
fails rather than writing a table that points at nothing. Filer counts are
recorded alongside, because an element that only a few hundred companies tag is
real but sparse, and an annotator should expect the gap rather than treat it as an
error.

A provenance record is written next to the table with the probe results, the
generating script, and the commit it ran from, so a reader can tell where the
table came from and when it was last proved.
"""

# region Imports & setup
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from constants import (  # noqa: E402
    METRIC_CLASSES_FILE,
    REFERENCE_DIR,
    TAXONOMY_PROBE_YEARS,
    probe_periods,
)
from edgar import probe_elements  # noqa: E402
from reference import METRIC_DEFINITIONS, MetricDefinition  # noqa: E402
from run_logging import banner, log_detail, log_saved, logged_run, tee_to_logfile  # noqa: E402

PROVENANCE_FILE = REFERENCE_DIR / "metric_classes.provenance.json"
CSV_COLUMNS = ["metric", "class", "taxonomy_element", "in_evidence_store", "window_coverage", "ambiguous", "note"]

# endregion

# region Verification
def probe_requests(definitions: tuple[MetricDefinition, ...]) -> list[tuple[str, str, str]]:
    """Build the deduplicated list of element probes the definitions require.

    Each element is probed once per period in the study window. An element used by
    several metrics is probed once per period, not once per metric. Instantaneous
    elements need the ``I`` period suffix, which is why the element carries that
    flag.

    Args:
        definitions: Curated metric definitions.

    Returns:
        Tuples of element, unit, and period, in a stable order.
    """
    requests: dict[tuple[str, str, str], None] = {}
    for definition in definitions:
        for element in definition.elements:
            for period in probe_periods(element.instantaneous):
                requests[(element.name, element.unit, period)] = None
    return sorted(requests)


def verify(definitions: tuple[MetricDefinition, ...]) -> dict[str, dict[str, object]]:
    """Probe every element the definitions name and report the outcome.

    Args:
        definitions: Curated metric definitions.

    Returns:
        Mapping of element name to its probe result.

    Raises:
        SystemExit: If any element does not exist in the SEC taxonomy.
    """
    requests = probe_requests(definitions)
    log_detail(f"{len(requests)} distinct elements to verify")

    results = probe_elements(requests)
    by_element: dict[str, dict[str, object]] = {}

    for probe in results:
        entry = by_element.setdefault(probe.element, {"unit": probe.unit, "periods": {}})
        entry["periods"][probe.period] = {
            "exists": probe.exists,
            "filer_count": probe.filer_count,
            "http_status": probe.http_status,
            "error": probe.error,
        }

    never_found: list[str] = []
    for element, entry in sorted(by_element.items()):
        periods = entry["periods"]
        counts = [periods[p]["filer_count"] if periods[p]["exists"] else None for p in sorted(periods)]
        entry["window_coverage"] = (
            "full" if all(c is not None for c in counts)
            else "none" if all(c is None for c in counts)
            else "partial"
        )
        rendered = "  ".join(f"{y}:{c:>5}" if c is not None else f"{y}:{'-':>5}"
                             for y, c in zip(TAXONOMY_PROBE_YEARS, counts))
        marker = {"full": "ok   ", "partial": "PART ", "none": "FAIL "}[entry["window_coverage"]]
        log_detail(f"{marker} {element:<58} {rendered}")
        if entry["window_coverage"] == "none":
            never_found.append(element)

    if never_found:
        raise SystemExit(
            f"\n{len(never_found)} element(s) exist in no probed period:\n  "
            + "\n  ".join(never_found)
            + "\n\nFix src/reference/metrics.py rather than the CSV."
        )
    return by_element


# endregion

# region Serialisation
def to_row(definition: MetricDefinition, probes: dict[str, dict[str, object]]) -> dict[str, str]:
    """Render one definition as a CSV row.

    Window coverage is the best of the metric's elements, because alternatives are
    tried in turn: a metric whose post-606 element starts in 2018 and whose
    predecessor runs to 2024 is covered throughout even though neither element is.

    Args:
        definition: A curated metric definition.
        probes: Probe results keyed by element.

    Returns:
        Mapping of column name to value.
    """
    if definition.expression:
        element = definition.expression
    elif definition.elements_are_alternatives:
        element = " | ".join(e.name for e in definition.elements)
    else:
        element = " ".join(e.name for e in definition.elements)

    if not definition.elements:
        coverage = "n/a"
    else:
        seen = [probes[e.name]["window_coverage"] for e in definition.elements]
        if definition.elements_are_alternatives:
            # Union: a period is covered if any alternative covers it.
            periods = sorted(probes[definition.elements[0].name]["periods"])
            covered = [
                any(probes[e.name]["periods"][p]["exists"] for e in definition.elements)
                for p in periods
            ]
            coverage = "full" if all(covered) else "partial" if any(covered) else "none"
        else:
            coverage = "full" if all(c == "full" for c in seen) else "partial"

    return {
        "metric": definition.metric,
        "class": definition.metric_class.value,
        "taxonomy_element": element,
        "in_evidence_store": "yes" if definition.in_evidence_store else "no",
        "window_coverage": coverage,
        "ambiguous": "yes" if definition.ambiguous else "no",
        "note": definition.note,
    }


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


def write_table(definitions: tuple[MetricDefinition, ...], probes: dict[str, dict[str, object]]) -> None:
    """Write the metric class CSV.

    Args:
        definitions: Curated metric definitions.
        probes: Probe results keyed by element.

    Returns:
        None.
    """
    METRIC_CLASSES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with METRIC_CLASSES_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(to_row(d, probes) for d in definitions)
    log_saved(METRIC_CLASSES_FILE)


def write_provenance(probes: dict[str, dict[str, object]], definitions: tuple[MetricDefinition, ...]) -> None:
    """Write the record of where the table came from and when it was proved.

    Args:
        probes: Probe results keyed by element.
        definitions: Curated metric definitions.

    Returns:
        None.
    """
    record = {
        "generated_by": "scripts/01_build_reference_tables.py",
        "source_of_truth": "src/reference/metrics.py",
        "commit": commit_sha(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "probe_years": list(TAXONOMY_PROBE_YEARS),
        "counts": {
            "metrics": len(definitions),
            "flow": sum(1 for d in definitions if d.metric_class.value == "FLOW"),
            "level": sum(1 for d in definitions if d.metric_class.value == "LEVEL"),
            "in_evidence_store": sum(1 for d in definitions if d.in_evidence_store),
            "ambiguous": sum(1 for d in definitions if d.ambiguous),
            "elements_verified": len(probes),
        },
        "elements": probes,
    }
    PROVENANCE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log_saved(PROVENANCE_FILE)


# endregion

# region Main
def main() -> None:
    """Verify the definitions and write the reference table.

    Returns:
        None.
    """
    banner("Metric class table")
    log_detail(f"{len(METRIC_DEFINITIONS)} metrics defined in src/reference/metrics.py")

    with logged_run("Verifying taxonomy elements against the SEC frames API"):
        probes = verify(METRIC_DEFINITIONS)

    banner("Writing")
    write_table(METRIC_DEFINITIONS, probes)
    write_provenance(probes, METRIC_DEFINITIONS)

    partial = sorted(e for e, p in probes.items() if p["window_coverage"] == "partial")
    if partial:
        banner("Elements that do not span the study window")
        log_detail("A claim from a period the element does not cover resolves to ABSENT,")
        log_detail("even where the quantity was disclosed under another name.")
        for element in partial:
            years = ", ".join(str(y) for y, p in zip(TAXONOMY_PROBE_YEARS, sorted(probes[element]["periods"]))
                              if not probes[element]["periods"][p]["exists"])
            log_detail(f"  {element}  missing in {years}")


if __name__ == "__main__":
    tee_to_logfile()
    main()
# endregion
