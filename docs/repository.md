# Repository layout

Where everything lives, what writes it, and whether it is committed.

```text
.
├── README.md                     Pitch, research question, quick start, status. Links into docs/.
├── requirements.txt              Pinned dependencies. Versions of record.
├── assets/                       README banner, light and dark variants.
├── .github/
│   ├── workflows/ci.yml          Documentation, environment, and code checks.
│   └── scripts/check_docs.py     Link, citation, version, and prose checks. Runnable locally.
├── .python-version               3.12.10
├── LICENSE                       CC BY 4.0. Covers documentation and data.
├── LICENSE-MIT                   MIT. Covers source code.
├── CITATION.cff                  Machine-readable citation metadata.
│
├── docs/                         Prose a reader follows rather than runs.
│   ├── README.md
│   ├── annotation-guidelines.md  The frozen manual. Changes need a version bump and a change-log entry.
│   ├── task.md                   What the system does with a claim, and the falsifiability label.
│   ├── worked-examples.md        Five claims end to end.
│   ├── annotation.md             The four passes and why the order matters.
│   ├── data.md                   Sources, cost, and what constrains them.
│   ├── pilot.md                  The 250-claim pilot and the decision gate.
│   ├── reproducibility.md        Environment, seeds, and the protocol rules.
│   ├── repository.md             This page.
│   ├── glossary.md               Finance and filing terms.
│   └── references.md             Peer-reviewed anchors.
│
├── data/                         Not committed. Obtained by the documented steps.
│   ├── README.md
│   ├── raw/README.md             Transcripts and XBRL facts exactly as pulled. Never edited.
│   ├── interim/README.md         Intermediate, regenerable.
│   └── processed/README.md       The splits every experiment reads. Temporal, frozen before annotation.
│
├── reference/                    Committed. Version-locked to the annotation manual.
│   ├── README.md
│   ├── metric_classes.csv        metric -> FLOW or LEVEL, selects the default baseline. Generated.
│   ├── filers.csv                The 150 study filers. The CIK every other table joins on. Generated.
│   ├── filing_dates.csv          cik, fiscal_period, form_type, filed_date, lag. Generated.
│   ├── fiscal_calendar.csv       cik -> fiscal year end, 52/53-week flag. Generated.
│   ├── fiscal_quarters.csv       cik, fiscal year, quarter -> period end. Generated.
│   ├── *.provenance.json         Per table: what produced it, when, and the rules in force.
│   └── evidence_cutoff.txt       The single cutoff date T.
│
├── annotations/
│   ├── README.md
│   ├── passages.jsonl            Sampled passages with exhaustive claim counts. Carries the denominator.
│   ├── claims.jsonl              One record per claim per annotator.
│   └── policy_gaps.md            Cases the policy registry does not cover.
│
├── src/                          Importable code, no side effects.
│   ├── README.md
│   ├── constants.py              Paths, seeds, SEC settings. Standard library only.
│   ├── run_logging.py            Console output and log files.
│   ├── reference/README.md       What is authored here against what is derived.
│   ├── reference/metrics.py      Authored metric definitions, validated at import.
│   ├── reference/filers.py       The filer selection rule, and what it costs.
│   ├── reference/calendar.py     Fiscal year shapes, derived from filed period ends.
│   ├── edgar/README.md           One transport, one rate limit, for every SEC call.
│   ├── edgar/transport.py        Shared HTTP layer. A 404 is a result, not a failure.
│   ├── edgar/frames.py           Element existence, and every filer's value for one period.
│   ├── edgar/submissions.py      Filing history per filer.
│   ├── edgar/facts.py            One filer, one concept, for the gaps the frames leave.
│   ├── resolution/README.md      Claim text to a structured proposition.
│   └── adjudication/README.md    Observation status, evidence lookup, verdicts.
│
├── scripts/                      Numbered, runnable, produce results.
│   ├── README.md
│   ├── 00_pull_transcripts.py
│   ├── 01_build_metric_classes.py    Verifies elements against the SEC, writes the metric table.
│   ├── 02_select_filers.py           Ranks filers by revenue, writes the study set.
│   ├── 03_build_filing_dates.py      Filing history per filer, with a lag plausibility flag.
│   ├── 04_build_fiscal_calendar.py   Fiscal year shape and quarter ends per filer. Offline.
│   ├── 05_sample_passages.py
│   ├── 06_compute_observation_status.py
│   ├── 07_make_report_figures.py
│   ├── 08_build_repro_artifacts.py
│   └── 09_verify_invariants.py
│
├── reports/
│   ├── README.md
│   ├── tables/README.md          Written only through the shared writer.
│   ├── figures/README.md         Rendered from builders in src, never defined in a notebook.
│   ├── logs/README.md            One timestamped log per run. Not committed.
│   └── repro/README.md           Environment, seeds, artifact inventory.
│
└── notebooks/
    ├── README.md                 Read results and interpret them. Generate nothing.
    ├── 01_metric_classes.ipynb   Coverage, the evidence-store gap, and the arguable classes.
    ├── 02_filers.ipynb           What the selection rule admits, and the three things it gets wrong.
    ├── 03_filing_dates.ipynb     Filing lag, the rows the table does not trust, window coverage.
    └── 04_fiscal_calendar.ipynb  The two calendar shapes, year-end changes, quarter labels.
```

Every directory carries a README stating what lives there, what writes it, and whether it is committed. Many of the files listed above do not exist yet; the directories and their READMEs do, so the [annotation guidelines](annotation-guidelines.md) references resolve to a known place either way. Three reference tables are built and committed, each with a provenance record and a notebook that reads it.

Artifacts in `reports/` carry the prefix of the script that produced them, so provenance is readable from a filename. `09_verify_invariants.py` will fail on any artifact whose prefix matches no script.

---

The rules behind this layout are in [reproducibility](reproducibility.md).
