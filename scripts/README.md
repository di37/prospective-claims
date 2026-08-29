# scripts

Runnable entry points. Each produces results; none defines a method.

```
00_pull_transcripts.py            transcripts -> data/raw
01_build_reference_tables.py      EDGAR -> reference/
02_sample_passages.py             passage sample -> data/processed
03_compute_observation_status.py  OBSERVABLE / RIGHT_CENSORED per claim
06_make_report_figures.py         every figure
07_build_repro_artifacts.py       environment, seeds, artifact inventory
08_verify_invariants.py           PASS/FAIL protocol checks, non-zero on failure
```

Naming is `NN[a-z]_description.py`. Where a part both selects and tests, the `a` script touches validation only and the `b` script contacts the held-out set exactly once, which is what makes "the test set is read once" checkable rather than asserted.

Artifacts are written through the shared writers in `src/common.py`, which derive the output prefix from the running script's filename. Renaming a script renames its outputs on the next run.

A script that needs a loop the harness does not provide is a signal the loop belongs in `src/`, not that it should be written here.
