# scripts

Runnable entry points. Each produces results; none defines a method.

```
00_pull_transcripts.py            transcripts -> data/raw
01_build_metric_classes.py        metric -> FLOW or LEVEL, elements verified against EDGAR
02_select_filers.py               the 150 study filers, ranked by revenue
03_build_filing_dates.py          cik, fiscal_period, form_type, filed_date, per filer
04_build_fiscal_calendar.py       cik -> fiscal year end, 52/53-week flag
05_sample_passages.py             passage sample -> data/processed
06_compute_observation_status.py  OBSERVABLE / RIGHT_CENSORED per claim
07_make_report_figures.py         every figure
08_build_repro_artifacts.py       environment, seeds, artifact inventory
09_verify_invariants.py           PASS/FAIL protocol checks, non-zero on failure
```

01 to 04 build `reference/`, in that order: 02 decides who is in the study and 03 and 04 join on the CIKs it writes. Running 03 against a stale `filers.csv` produces a table that looks fine and covers the wrong companies.

Naming is `NN[a-z]_description.py`. Where a part both selects and tests, the `a` script touches validation only and the `b` script contacts the held-out set exactly once, which is what makes "the test set is read once" checkable rather than asserted.

Artifacts are written through the shared writers in `src/common.py`, which derive the output prefix from the running script's filename. Renaming a script renames its outputs on the next run.

A script that needs a loop the harness does not provide is a signal the loop belongs in `src/`, not that it should be written here.
