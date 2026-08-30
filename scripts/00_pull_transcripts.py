"""Pull the earnings-call transcript corpus into data/raw.

Lands ``episodes.parquet`` from the HuggingFace release named in ``constants``.
Nothing is filtered or edited: ``data/raw`` holds what was pulled, and everything
downstream is derived from it by script.

The transcripts are third-party content and are never committed. ``data/`` is
gitignored in full, and the licence position is recorded in the provenance file
this script writes rather than assumed from the dataset card: the release is
tagged MIT, so are the two datasets it derives from, and none of them names the
vendor the transcripts originally came from. An MIT tag applied by an uploader
does not grant rights the uploader does not hold.

The download is about 1.2 GB and resumes if interrupted. Run it once.
"""

# region Imports & setup
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from constants import (  # noqa: E402
    RAW_DIR,
    TRANSCRIPT_RAW_FILE,
    TRANSCRIPT_REPO,
    TRANSCRIPT_REPO_FILE,
)
from run_logging import banner, log_detail, log_saved, logged_run, tee_to_logfile  # noqa: E402

PROVENANCE_FILE = RAW_DIR / "transcripts.provenance.json"

LICENCE_POSITION = [
    "The release is tagged MIT, as are Bose345/sp500_earnings_transcripts and kurry/sp500_earnings_transcripts beneath it.",
    "None of the three names the vendor the transcripts originally came from, and several transcripts carry a TRANSCRIPT SPONSOR line, which is a vendor artefact.",
    "An MIT tag applied by an uploader does not grant rights the uploader does not hold, so the text is treated as third-party content.",
    "The corpus is pulled, never committed, and never redistributed. Released artifacts carry character offsets and labels plus a script that rebuilds the text from this source.",
]

# endregion

# region Pulling
def download() -> Path:
    """Fetch the corpus file, resuming a partial download if one exists.

    Returns:
        Path to the local file.
    """
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(
        TRANSCRIPT_REPO,
        TRANSCRIPT_REPO_FILE,
        repo_type="dataset",
        local_dir=str(RAW_DIR),
    )
    return Path(path)


def digest(path: Path) -> str:
    """Return the file's SHA-256, so a later run can tell whether it changed.

    Args:
        path: File to hash.

    Returns:
        Hex digest.
    """
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


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


def write_provenance(path: Path, rows: int, columns: int, sha: str) -> None:
    """Record what was pulled, from where, and on what terms.

    Args:
        path: The downloaded file.
        rows: Row count.
        columns: Column count.
        sha: SHA-256 of the file.

    Returns:
        None.
    """
    record = {
        "generated_by": "scripts/00_pull_transcripts.py",
        "commit": commit_sha(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "repo": TRANSCRIPT_REPO,
            "repo_type": "dataset",
            "file": TRANSCRIPT_REPO_FILE,
            "url": f"https://huggingface.co/datasets/{TRANSCRIPT_REPO}",
            "derived_from": [
                "Bose345/sp500_earnings_transcripts",
                "kurry/sp500_earnings_transcripts",
            ],
        },
        "file": {
            "path": str(path.relative_to(PROJECT_ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha,
            "rows": rows,
            "columns": columns,
        },
        "licence_position": LICENCE_POSITION,
        "committed": False,
    }
    PROVENANCE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log_saved(PROVENANCE_FILE)


# endregion

# region Main
def main() -> None:
    """Pull the corpus and record what arrived.

    Returns:
        None.
    """
    import pyarrow.parquet as pq

    banner("Transcript corpus")
    log_detail(f"{TRANSCRIPT_REPO} / {TRANSCRIPT_REPO_FILE}")
    log_detail("about 1.2 GB; resumes if interrupted")

    with logged_run("Downloading"):
        path = download()

    with logged_run("Verifying"):
        metadata = pq.ParquetFile(path).metadata
        sha = digest(path)

    banner("Writing")
    write_provenance(path, metadata.num_rows, metadata.num_columns, sha)

    log_detail(f"{metadata.num_rows:,} rows, {metadata.num_columns} columns, "
               f"{path.stat().st_size / 1e6:,.0f} MB")
    log_detail(f"sha256 {sha[:16]}...")

    banner("Licence")
    for line in LICENCE_POSITION:
        log_detail(line)

    if path != TRANSCRIPT_RAW_FILE:
        log_detail(f"note: landed at {path}, expected {TRANSCRIPT_RAW_FILE}")


if __name__ == "__main__":
    tee_to_logfile()
    main()
# endregion
