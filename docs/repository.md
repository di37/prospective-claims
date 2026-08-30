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
│   ├── annotation/
│   │   ├── annotation-guidelines.md  The frozen manual. Changes need a version bump.
│   │   ├── annotation.md         The four passes and why the order matters.
│   │   ├── four-passes.png       The passes as a diagram.
│   │   ├── walkthrough.md        One claim through all four passes, section by section.
│   │   ├── claim-1-passes.png    Claim 1 as a diagram: the resolvable case.
│   │   └── claim-2-passes.png    Claim 2 as a diagram: the unfalsifiable case.
│   ├── task/
│   │   ├── task.md               What the system does with a claim, and the falsifiability label.
│   │   ├── task-pipeline.png     Parked: missing the NOT_APPLICABLE branch.
│   │   └── falsifiability.png    The three-way label and how it is decided.
│   ├── worked-examples/
│   │   ├── worked-examples.md    Five claims end to end.
│   │   └── example-{1..5}.png    One illustration per example.
│   ├── pilot/
│   │   ├── pilot.md              The 250-claim pilot and the decision gate.
│   │   └── decision-gate.png     The gate and its three branches.
│   ├── data.md                   Sources, cost, and what constrains them.
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
│   ├── transcript_coverage.csv   Corpus symbol -> quarters covered. The sampling frame. Generated.
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
│   ├── reference/metrics/        The 49 metric definitions: models, constructors, data.
│   ├── reference/filers/         The selection rule: models, ranking, screening.
│   ├── reference/calendar/       Fiscal year shapes: models, shapes, derivation.
│   ├── corpus/README.md          The transcript corpus: coverage, identity, segmentation.
│   ├── corpus/bridge/            Ticker to CIK: models, matching. Why that join is fragile.
│   ├── corpus/segments/          Prepared remarks against the analyst Q&A.
│   ├── corpus/coverage.py        Quarter-by-quarter coverage per symbol.
│   ├── edgar/README.md           One transport, one rate limit, for every SEC call.
│   ├── edgar/transport.py        Shared HTTP layer. A 404 is a result, not a failure.
│   ├── edgar/frames/             Element existence, and every filer's value for one period.
│   ├── edgar/submissions/        Filing history per filer.
│   ├── edgar/facts.py            One filer, one concept, for the gaps the frames leave.
│   ├── resolution/README.md      Claim text to a structured proposition.
│   ├── resolution/windows/       Section 5.5 phrases onto a filer's fiscal quarters.
│   ├── adjudication/README.md    Observation status, evidence lookup, verdicts.
│   └── adjudication/observation/ Status from the filing calendar, never from evidence.
│
├── scripts/                      Numbered, runnable, produce results.
│   ├── README.md
│   ├── 00_pull_transcripts.py        Transcript corpus -> data/raw. About 1.2 GB.
│   ├── 01_build_metric_classes.py    Verifies elements against the SEC, writes the metric table.
│   ├── 02_select_filers.py           Ranks filers by revenue, writes the study set.
│   ├── 03_build_filing_dates.py      Filing history per filer, with a lag plausibility flag.
│   ├── 04_build_fiscal_calendar.py   Fiscal year shape and quarter ends per filer. Offline.
│   ├── 05_build_transcript_inventory.py  Corpus coverage and the sampling frame. Offline.
│   ├── 06_sample_passages.py
│   ├── 07_compute_observation_status.py
│   ├── 08_make_report_figures.py
│   ├── 09_build_repro_artifacts.py
│   └── 10_verify_invariants.py
│
├── tests/                        CPU only. No dataset, API key, or network.
│   ├── README.md
│   ├── test_windows.py           Window resolution across five calendar shapes.
│   └── test_observation.py       Observation status across every branch of section 6.
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
    ├── 04_fiscal_calendar.ipynb  The two calendar shapes, year-end changes, quarter labels.
    └── 05_transcripts.ipynb      Corpus coverage, the ticker join, and the Q&A split.
```

Every directory carries a README stating what lives there, what writes it, and whether it is committed. Many of the files listed above do not exist yet; the directories and their READMEs do, so the [annotation guidelines](annotation/annotation-guidelines.md) references resolve to a known place either way. Six reference tables are built and committed, each with a provenance record, and five of them have a notebook that reads it and says what it is fit for.

Artifacts in `reports/` carry the prefix of the script that produced them, so provenance is readable from a filename. `10_verify_invariants.py` will fail on any artifact whose prefix matches no script.

---

The rules behind this layout are in [reproducibility](reproducibility.md).
