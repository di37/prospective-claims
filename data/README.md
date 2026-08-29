# data

Three stages, none of them committed.

| Stage | What it holds | Written by |
|---|---|---|
| `raw/` | Transcripts and XBRL facts exactly as pulled | `scripts/00_pull_transcripts.py`, `scripts/01_build_reference_tables.py` |
| `interim/` | Intermediate products, all regenerable | Various scripts |
| `processed/` | The splits every experiment reads | `scripts/02_sample_passages.py` |

Nothing here is edited by hand. If a value looks wrong, fix the script that produced it and re-run, so the fix survives the next regeneration.

Transcripts are owned by their providers and are not redistributed. A released dataset carries claim spans, character offsets, resolutions, and labels, plus a script that reconstructs the text from its source.
