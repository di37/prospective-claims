# scripts

Runnable entry points. Each produces results; none defines a method.

```
00_pull_transcripts.py            transcript corpus -> data/raw. About 1.2 GB, run once
01_build_metric_classes.py        metric -> FLOW or LEVEL, elements verified against EDGAR
02_select_filers.py               the 150 study filers, ranked by revenue
03_build_filing_dates.py          cik, fiscal_period, form_type, filed_date, per filer
04_build_fiscal_calendar.py       cik -> fiscal year end, 52/53-week flag
05_build_transcript_inventory.py  corpus coverage, and which filers the pilot can sample
06_sample_passages.py             passage sample -> data/processed
07_compute_observation_status.py  OBSERVABLE / RIGHT_CENSORED per claim
08_make_report_figures.py         every figure
09_build_repro_artifacts.py       environment, seeds, artifact inventory
10_verify_invariants.py           PASS/FAIL protocol checks, non-zero on failure
```

01 to 05 build `reference/`, in that order: 02 decides who is in the study, 03 joins on the CIKs it writes, 04 derives the calendars from what 03 pulled, and 05 intersects all of it with the transcript corpus to give the set the pilot actually samples from. Running 03 against a stale `filers.csv` produces a table that looks fine and covers the wrong companies. Only 04 and 05 are offline.

00 stands apart. It downloads about 1.2 GB and depends on nothing, so it is run once and then left alone; 05 re-reads what it landed and is cheap to re-run whenever the study set changes.

Naming is `NN[a-z]_description.py`. Where a part both selects and tests, the `a` script touches validation only and the `b` script contacts the held-out set exactly once, which is what makes "the test set is read once" checkable rather than asserted.

Artifacts are written through the shared writers in `src/common.py`, which derive the output prefix from the running script's filename. Renaming a script renames its outputs on the next run.

A script that needs a loop the harness does not provide is a signal the loop belongs in `src/`, not that it should be written here.
