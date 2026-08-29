# reports

Everything the scripts produce. Nothing here is written by hand and nothing here is written by a notebook.

| Directory | Contents | Committed |
|---|---|---|
| `tables/` | Results tables, CSV | Yes |
| `figures/` | Report figures, PNG and PDF | Yes |
| `logs/` | One timestamped log per script run | No |
| `repro/` | Environment, seeds, artifact inventory | Yes |

Every artifact carries the prefix of the script that produced it:

```
tables/01a_example_sweep__sweep_results.csv
figures/06_make_report_figures__sweep_by_algorithm.png
```

The prefix is derived from the running script's filename rather than passed as an argument, so it cannot be forgotten or mistyped. `08_verify_invariants.py` fails on any artifact whose prefix matches no script in `scripts/`, which catches both an artifact written outside the harness and one left behind by a script that has since been renamed.
