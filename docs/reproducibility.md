# Reproducibility

Every number in this project should be rebuildable from a clean checkout by someone who is not us. That is a design constraint, not an aspiration, and several decisions elsewhere in these documents exist only to serve it.

## Environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12.10. `requirements.txt` pins exact versions rather than ranges, because a range means two people can follow the same instructions and get different numbers. The pinned set is the versions of record: every committed result will be produced under them. Nothing has been run yet, so that is a commitment rather than a claim about existing results. Relaxing a pin means re-running whatever depended on it and updating the environment record.

## Seeds

Sampling, splitting, and any model seed will be fixed in `src/constants.py` and recorded in `reports/repro/study_metadata.json`. Neither file exists yet. They are part of the protocol rather than tuning knobs: once set, changing one invalidates every result committed under it.

## Data provenance

Nothing under `data/` is committed. Raw data is obtained by documented steps and everything downstream is rebuilt by script, so the repository stays small and the pipeline stays honest. If a value looks wrong, the fix goes in the script that produced it, never in the file.

XBRL facts are stored **as first reported**. Company Facts serves the current value of a concept including restatements, and a figure revised after a claim was made would leak information that did not exist at the time.

The evidence cutoff `T` is a single frozen date in `reference/evidence_cutoff.txt`. It determines which claims are observable, so a moving cutoff would silently change the censoring rate between runs.

## Protocol rules that keep results honest

| Rule | What it prevents |
|---|---|
| The test split is read by exactly one script per part | Selection decisions made with the test set in scope |
| Splits are frozen before annotation begins | Splits drawn to suit results already seen |
| Every table and figure carries the prefix of the script that produced it | Artifacts nobody can trace or regenerate |
| Figures are rendered from builders in `src`, never defined in a notebook | Committed figures that go stale silently |
| Annotation agreement is computed pre-adjudication and never recomputed | Agreement scores inflated by discussion |
| Conventions that could move a number are declared before annotation, then ablated | Choices tuned after seeing their effect |

`scripts/10_verify_invariants.py` will check these mechanically and exit non-zero on failure, so a violation blocks a commit rather than surviving into a paper. It is not written yet; CI already has the step, which skips until the file appears. What CI does run today is `.github/scripts/check_docs.py`, which catches the documentation equivalents: links pointing at renamed files, anchors pointing at reworded headings, a guidelines version that drifted between the change log and the record schema, and hard-wrapped prose. Each rule is invisible in the results when broken, which is exactly why it is checked by machine rather than by review.

## Reproduction record

`scripts/09_build_repro_artifacts.py`, once written, will produce `reports/repro/` after every experiment script has run: interpreter and platform, versions of the packages that affect results, seeds, and an inventory of every artifact with the script that produced it. Together these answer the two questions a later reader has, which are whether they can rebuild this and whether a committed figure came from the current code.

---

The layout these rules assume is described in [repository](repository.md).
