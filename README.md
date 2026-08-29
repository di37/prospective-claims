<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.png">
    <img src="assets/banner-light.png" alt="Prospective Claim Verification. Pipeline: earnings calls to claim resolution, then a gap of one to eight quarters while evidence appears, then future filings, then adjudication." width="900">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/di37/prospective-claims/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/di37/prospective-claims/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="LICENSE"><img alt="Docs and data licence: CC BY 4.0" src="https://img.shields.io/badge/docs%20%26%20data-CC%20BY%204.0-1f6feb?style=flat-square"></a>
  <a href="LICENSE-MIT"><img alt="Code licence: MIT" src="https://img.shields.io/badge/code-MIT-2da44e?style=flat-square"></a>
  <a href="requirements.txt"><img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-3776ab?style=flat-square&logo=python&logoColor=white"></a>
  <a href="annotation-guidelines.md"><img alt="Annotation guidelines v1.6" src="https://img.shields.io/badge/guidelines-v1.6-8250df?style=flat-square"></a>
  <a href="#status"><img alt="Status: pilot not started" src="https://img.shields.io/badge/status-pilot%20not%20started-7d8590?style=flat-square"></a>
  <a href="https://github.com/di37/prospective-claims/issues"><img alt="Open issues" src="https://img.shields.io/github/issues/di37/prospective-claims?style=flat-square&color=bf8700"></a>
  <a href="CONTRIBUTING.md"><img alt="Contributions welcome" src="https://img.shields.io/badge/contributions-welcome-2da44e?style=flat-square"></a>
</p>

Resolving forward-looking claims from earnings calls into testable financial propositions, then checking them against financial facts published **after** the claim was made.

When a CFO says "we expect margins to improve next quarter", that is a prediction with a deadline. Three months later the company files a report containing the number that settles it. This project asks whether a model can turn the sentence into something checkable, wait for the filing, and decide whether the prediction held.

| | |
|---|---|
| **Status** | Design frozen. Pilot not yet run. |
| **Target** | ARR October 2026 cycle — submission 2026-10-12 |
| **Venue** | NAACL 2027 / COLING 2027 |
| **Study window** | 2012–2024, 120–150 large-cap filers |
| **Evidence store** | SEC Company Facts, the machine-readable financial data companies file with the regulator |

## Contents

| Section | What is in it |
|---|---|
| [Research question](#research-question) | The question and its three sub-questions |
| [Worked examples](#worked-examples) | Five inputs and what the system returns for each |
| [Task](#task) | Resolution, adjudication, and the pipeline |
| [Annotation](#annotation) | Four passes and why the order matters |
| [Falsifiability](#falsifiability) | The three-way linguistic label |
| [Data](#data) | Sources, what constrains them, and what is licensable |
| [Reproducibility](#reproducibility) | Environment, seeds, and the rules that keep results rebuildable |
| [Pilot and decision gate](#pilot-and-decision-gate) | What 250 claims decide |
| [Repository](#repository) | Files and what each is for |
| [Status](#status) | What is done and what blocks the next step |
| [Glossary](#glossary) | Finance and filing terms used above |
| [Contributing](#contributing) | Where to start, and what needs doing |
| [Citation](#citation) | How to cite this work |
| [References](#references) | Peer-reviewed anchors |

## Research question

> Can NLP systems resolve forward-looking statements in corporate earnings calls into testable financial propositions, and subsequently verify those propositions against financial evidence that becomes available only in later reporting periods?

| | Question |
|---|---|
| **RQ1** | How accurately can models recover the metric concept, scope, accounting basis, transformation, baseline, temporal window, direction, and threshold implied by a forward-looking claim? |
| **RQ2** | Can models distinguish objectively testable forecasts from underspecified or intrinsically unfalsifiable corporate language? |
| **RQ3** | Given evidence published after the claim, can a system determine whether it was supported or refuted, and recognise when sufficient evidence is unavailable in the designated store? |

Existing financial claim-verification benchmarks verify claims against evidence that already exists, usually inside the same document. This task verifies against evidence that does not exist when the claim is made, which means the evaluation window is not given and has to be inferred.

## Worked examples

Five representative claims and what the system returns. Between them they cover every outcome the task can produce. The sentences are illustrative rather than quotations from any particular company.

### 1. Clean verification

A threshold claim needs no baseline, and the metric maps directly onto a tagged GAAP concept.

```
INPUT    "We expect gross margin to exceed 71% in the third quarter."
         uttered 2023-05-24, fiscal Q2

RESOLVE  concept    GrossProfit / Revenues        STATED
         scope      consolidated                  SUPPLIED
         basis      UNSPECIFIED                   SUPPLIED
         window     [t+1, t+1]                    EXPLICIT
         direction  THRESHOLD                     STATED
         threshold  > 71%                         STATED
         falsifiability  FALSIFIABLE

CHECK    UNSPECIFIED maps to GAAP at adjudication, per section 5.2
         Q3 filed 2023-11-02, before cutoff  ->  OBSERVABLE
         GrossProfit / Revenues = 73.2%      ->  GAAP-XBRL

OUTPUT   SUPPORTED
```

### 2. Refuted, and mostly resolved by policy

"Normalise" carries no number, so the manual supplies the baseline. The provenance column is what stops the model getting credit for the manual's work.

```
INPUT    "We expect inventory levels to normalise over the next two quarters."

RESOLVE  concept    InventoryNet                  STATED
         scope      consolidated                  SUPPLIED
         basis      UNSPECIFIED                   SUPPLIED
         transform  scaled by revenue             SUPPLIED
         baseline   trailing 8-quarter median     POLICY_DEFAULT
         window     [t+1, t+2]                    EXPLICIT
         direction  TOWARD_BASELINE               STATED
         falsifiability  UNDERSPECIFIED

CHECK    both quarters filed  ->  OBSERVABLE
         gap to baseline: +38% at t, +41% at t+2

OUTPUT   REFUTED
         TOWARD_BASELINE is supported only if the gap shrinks. It widened,
         so the stated normalisation did not occur
```

### 3. Falsifiable, but not checkable from the evidence store

The most important failure case, and the one the pilot measures. Nothing is wrong with the sentence; the measure simply does not exist as structured data.

```
INPUT    "Adjusted EBITDA margin will be above 22% next quarter."

RESOLVE  concept    EBITDA margin                 STATED
         basis      ADJUSTED_NON_GAAP             STATED
         window     [t+1, t+1]                    EXPLICIT
         direction  THRESHOLD                     STATED
         threshold  > 22%                         STATED
         falsifiability  FALSIFIABLE

CHECK    filed and observable                ->  OBSERVABLE
         company-defined measure, not tagged ->  NON-GAAP-ONLY

OUTPUT   NOT_ENOUGH_EVIDENCE
         insufficient evidence in the designated store, which is not
         the same as the figure not existing: it is in the earnings
         release, just not in XBRL
```

### 4. Nothing to check

No observation settles this, so it never reaches adjudication. The rate at which management produces these is itself a signal.

```
INPUT    "We remain very excited about the long-term opportunity."

RESOLVE  concept    none
         falsifiability  UNFALSIFIABLE

OUTPUT   excluded from adjudication, counted in the vagueness rate
```

### 5. Correct, but not yet answerable

A long horizon is not a defect in the claim. Treating it as missing evidence would be a mistake, and would penalise the model for inferring the window correctly.

```
INPUT    "We expect margins to recover over the next two years."
         uttered 2024-12-10

RESOLVE  window     [t+1, t+8]                    EXPLICIT
         direction  INCREASE                      STATED
         falsifiability  UNDERSPECIFIED

CHECK    window ends 2026 Q4, filings not yet published
                                             ->  RIGHT_CENSORED

OUTPUT   excluded from adjudication, reported in the censoring rate
         annotated and counted, never scored
```

## Task

```mermaid
flowchart TD
    A["Forward-looking claim uttered at time t<br/>'inventory levels should normalise<br/>over the next two quarters'"]
    B["Resolve<br/>m = concept, scope, basis, transform<br/>b = baseline &nbsp; w = window<br/>d = direction &nbsp; τ = threshold"]
    C{"Falsifiable or<br/>underspecified?"}
    D["UNFALSIFIABLE<br/>excluded on the label alone"]
    K{"Conditional?"}
    L["Excluded from primary<br/>reported as its own stratum"]
    W{"Window resolved?"}
    X["NOT_APPLICABLE<br/>no window, so no observation status"]
    E{"Window closed AND<br/>filings published<br/>by cutoff T?"}
    F["RIGHT_CENSORED<br/>annotated, counted, not scored"]
    G{"Evidence available<br/>in store E?"}
    H["NOT_ENOUGH_EVIDENCE<br/>filing-text, non-GAAP, or absent"]
    I["Retrieve XBRL facts<br/>for w, as-first-reported"]
    J["SUPPORTED / REFUTED"]

    A --> B --> C
    C -- no --> D
    C -- yes --> K
    K -- yes --> L
    K -- no --> W
    W -- no --> X
    W -- yes --> E
    E -- no --> F
    E -- yes --> G
    G -- no --> H
    G -- yes --> I --> J
```

Two properties of this order carry the design.

**Observability is decided before evidence is inspected.** A claim is OBSERVABLE when its window has closed *and* the filings covering that window have been published by the cutoff `T`. That test uses the filer's reporting calendar, not the existence of any particular fact, so it does not depend on the thing it gates.

**Adjudication is scored twice.** Binary SUPPORTED / REFUTED on the slice with GAAP-XBRL evidence, isolating comparison and arithmetic. Three-way including NEI over the adjudication-eligible FALSIFIABLE and UNDERSPECIFIED claims, after the exclusions below, measuring whether a system knows when it cannot check something. A system emitting NEI where evidence does exist is a retrieval failure, reported separately and never credited as correct abstention.

## Annotation

Four passes, each completed across all claims before the next begins.

```mermaid
flowchart LR
    subgraph blind ["Evidence store closed"]
        direction TB
        PA["Pass A<br/>Identify claims<br/>exhaustive, no cue list"]
        PB["Pass B<br/>Falsifiability<br/>text only"]
        PC["Pass C<br/>Resolution + provenance<br/>text only"]
        PA --> PB --> PC
    end
    OS["Computed<br/>Observation status<br/>script, not annotator"]
    subgraph open ["Evidence store open"]
        PD["Pass D<br/>Evidence availability<br/>OBSERVABLE claims only"]
    end
    PC --> OS --> PD
```

Falsifiability is judged before resolution on purpose. Resolution means supplying policy defaults for missing fields, and an annotator who has just supplied a default baseline is primed to call the claim checkable. Judging falsifiability first keeps it a judgment about the sentence.

The two annotation axes are orthogonal and are annotated from different sources.

| Axis | Type | Annotated from | Values |
|---|---|---|---|
| Falsifiability | intrinsic | claim text only | falsifiable / underspecified / unfalsifiable |
| Evidence availability | extrinsic | the evidence store | GAAP-XBRL / filing-text / non-GAAP-only / absent |

Collapsing these into one label would teach a model where the SEC taxonomy has gaps rather than anything about language.

## Falsifiability

```mermaid
flowchart TD
    Q1{"Q1. Refers to a quantity that varies<br/>over time and is reported in<br/>any financial disclosure?"}
    Q2{"Q2. Metric, direction, period, AND<br/>comparison basis all recoverable<br/>from the text, without the registry?"}
    Q3{"Q3. Any assignment of the missing<br/>fields under which two analysts<br/>would agree on the verdict?"}
    F["FALSIFIABLE<br/>settleable without the manual"]
    U["UNDERSPECIFIED<br/>checkable once policy supplies a default"]
    N["UNFALSIFIABLE<br/>no observation settles it"]

    Q1 -- no --> N
    Q1 -- yes --> Q2
    Q2 -- yes --> F
    Q2 -- no --> Q3
    Q3 -- yes --> U
    Q3 -- no --> N
```

Q1 asks about *any* financial disclosure, not about the evidence store. A claim about adjusted EBITDA is falsifiable even though the structured data will not carry it, because EBITDA is a company-defined measure rather than a standard one; whether the store holds it is Pass D's question.

| Claim | Label |
|---|---|
| "Gross margin will exceed 71% in Q3." | FALSIFIABLE |
| "Adjusted EBITDA margin will be above 22% next quarter." | FALSIFIABLE |
| "Revenue will grow next quarter." | UNDERSPECIFIED |
| "Inventory should normalise over the next two quarters." | UNDERSPECIFIED |
| "We remain excited about the long-term opportunity." | UNFALSIFIABLE |

FALSIFIABLE means self-contained, so it is expected to be the smaller class, concentrated in threshold and range claims.

FALSIFIABLE and UNDERSPECIFIED claims are both *eligible* for adjudication, and results are stratified by the two. Eligible is not the same as included: a claim is still dropped if its evaluation window is UNRESOLVED, if it is right-censored, or if it is conditional. Only UNFALSIFIABLE is excluded on the strength of the label alone.

## Data

All real, all public. Nothing synthetic.

| Data | Source | Cost | Status |
|---|---|---|---|
| Earnings call transcripts | `RudrakshNanavaty/earnings-call-data` (HuggingFace) — 183k rows, 2005–2025, 685 tickers across 496 companies | Free | Verified, not yet pulled |
| Financial facts | SEC Company Facts, `data.sec.gov` | Free, no API key | Verified, not yet pulled |
| Filing dates | SEC EDGAR submissions API | Free, no API key | Verified, not yet pulled |
| Earnings-miss labels | Alpha Vantage `EARNINGS` endpoint — reported and estimated EPS, surprise, surprise percentage | Paid tier | Verified, needed only for the downstream task |

Study window 2012–2024, 120–150 large-cap filers.

Four properties of the data shape the design, and each one closed off an easier version of the project.

**Structured financial data does not reach back to 2005.** XBRL tagging was phased in for periods ending on or after June 2009 for the largest filers, June 2010 for other large accelerated filers, and June 2011 for everyone else. Transcripts run from 2005, but adjudication cannot start until roughly 2011, which is why the window begins in 2012.

**Non-GAAP measures are absent from the structured data.** A great deal of guidance is issued on adjusted EBITDA, non-GAAP margins, or constant-currency revenue, and companies routinely decline to reconcile forward-looking non-GAAP figures to GAAP. None of those exist as XBRL facts, so some of the most specific-sounding claims in the corpus are the least checkable. How much of the corpus this removes is exactly what the pilot measures.

**Filed values get revised.** Company Facts serves the current value of a concept, including restatements. The adjudicator uses as-first-reported values, because a restatement issued later would leak information that was not available when the claim was made.

**Fiscal calendars do not align.** Non-standard year ends, 52- and 53-week retail calendars, and "next year" meaning a fiscal year ending the following January. This is unglamorous work and a real source of label noise, so it gets its own module and its own tests.

Transcripts are owned by their providers, so a released dataset carries claim spans, character offsets, resolutions, and labels, plus a script that reconstructs the text from its source. That constraint is a design input, not something to resolve later.

## Reproducibility

Every number in this project should be rebuildable from a clean checkout by someone who is not us. That is a design constraint, not an aspiration, and several decisions elsewhere in this README exist only to serve it.

### Environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12.10. `requirements.txt` pins exact versions rather than ranges, because a range means two people can follow the same instructions and get different numbers. The pinned set is the versions of record: every committed result will be produced under them. Nothing has been run yet, so that is a commitment rather than a claim about existing results. Relaxing a pin means re-running whatever depended on it and updating the environment record.

### Seeds

Sampling, splitting, and any model seed will be fixed in `src/constants.py` and recorded in `reports/repro/study_metadata.json`. Neither file exists yet. They are part of the protocol rather than tuning knobs: once set, changing one invalidates every result committed under it.

### Data provenance

Nothing under `data/` is committed. Raw data is obtained by documented steps and everything downstream is rebuilt by script, so the repository stays small and the pipeline stays honest. If a value looks wrong, the fix goes in the script that produced it, never in the file.

XBRL facts are stored **as first reported**. Company Facts serves the current value of a concept including restatements, and a figure revised after a claim was made would leak information that did not exist at the time.

The evidence cutoff `T` is a single frozen date in `reference/evidence_cutoff.txt`. It determines which claims are observable, so a moving cutoff would silently change the censoring rate between runs.

### Protocol rules that keep results honest

| Rule | What it prevents |
|---|---|
| The test split is read by exactly one script per part | Selection decisions made with the test set in scope |
| Splits are frozen before annotation begins | Splits drawn to suit results already seen |
| Every table and figure carries the prefix of the script that produced it | Artifacts nobody can trace or regenerate |
| Figures are rendered from builders in `src`, never defined in a notebook | Committed figures that go stale silently |
| Annotation agreement is computed pre-adjudication and never recomputed | Agreement scores inflated by discussion |
| Conventions that could move a number are declared before annotation, then ablated | Choices tuned after seeing their effect |

`scripts/08_verify_invariants.py` will check these mechanically and exit non-zero on failure, so a violation blocks a commit rather than surviving into a paper. It is not written yet; CI already has the step, which skips until the file appears. What CI does run today is `.github/scripts/check_docs.py`, which catches the documentation equivalents: links pointing at renamed files, anchors pointing at reworded headings, a guidelines version that drifted between the change log and the record schema, and hard-wrapped prose. Each rule is invisible in the results when broken, which is exactly why it is checked by machine rather than by review.

### Reproduction record

`scripts/07_build_repro_artifacts.py`, once written, will produce `reports/repro/` after every experiment script has run: interpreter and platform, versions of the packages that affect results, seeds, and an inventory of every artifact with the script that produced it. Together these answer the two questions a later reader has, which are whether they can rebuild this and whether a committed figure came from the current code.

## Pilot and decision gate

250 claims, two annotators, drawn from exhaustively annotated passages so the denominator is unbiased.

```mermaid
flowchart TD
    P["250 claims<br/>two independent annotators"]
    M["StructuredCoverage =<br/>GAAP-XBRL adjudicable ÷ OBSERVABLE"]
    A["≥ 40%<br/>Full scope<br/>resolution + adjudication<br/>+ downstream application"]
    B["20–40%<br/>Adjudication secondary<br/>spine is resolution<br/>+ falsifiability"]
    C["&lt; 20%<br/>Drop adjudication<br/>taxonomy + falsifiability<br/>+ resolution task"]

    P --> M
    M --> A
    M --> B
    M --> C
```

The rule is written before the numbers arrive. A gate whose every outcome can be described as an interesting finding is not a test. All three branches are real papers; the third is the calmer six weeks.

Reported alongside it: per-field Cohen's kappa, censoring rate split by reason, the numerical/qualitative proportion, and median annotation minutes per claim.

## Repository

```text
.
├── README.md                     This file. Task, annotation scheme, data, and the decision gate.
├── annotation-guidelines.md      Annotation manual. Frozen; changes need a version bump and a change-log entry.
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
├── data/                         Not committed. Obtained by the documented steps.
│   ├── README.md
│   ├── raw/README.md             Transcripts and XBRL facts exactly as pulled. Never edited.
│   ├── interim/README.md         Intermediate, regenerable.
│   └── processed/README.md       The splits every experiment reads. Temporal, frozen before annotation.
│
├── reference/                    Committed. Version-locked to the annotation manual.
│   ├── README.md
│   ├── metric_classes.csv        metric -> FLOW or LEVEL, selects the default baseline. Generated.
│   ├── metric_classes.provenance.json  What produced the table, and when it was last proved.
│   ├── fiscal_calendar.csv       cik -> fiscal year end, 52/53-week flag.
│   ├── filing_dates.csv          cik, fiscal_period, form_type, filed_date.
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
│   ├── reference/metrics.py      Authored metric definitions, validated at import.
│   ├── edgar/frames.py           SEC frames client, used to verify taxonomy elements.
│   ├── resolution/README.md      Claim text to a structured proposition.
│   └── adjudication/README.md    Observation status, evidence lookup, verdicts.
│
├── scripts/                      Numbered, runnable, produce results.
│   ├── README.md
│   ├── 00_pull_transcripts.py
│   ├── 01_build_reference_tables.py   Verifies elements against the SEC, writes reference tables.
│   ├── 02_sample_passages.py
│   ├── 03_compute_observation_status.py
│   ├── 06_make_report_figures.py
│   ├── 07_build_repro_artifacts.py
│   └── 08_verify_invariants.py
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
    └── 01_metric_classes.ipynb   Coverage, the evidence-store gap, and the arguable classes.
```

Every directory carries a README stating what lives there, what writes it, and whether it is committed. Most of the code and data files listed above do not exist yet; the directories and their READMEs do, so the manual's references to `metric_classes.csv`, `fiscal_calendar.csv` and `filing_dates.csv` resolve to a known place.

Artifacts in `reports/` carry the prefix of the script that produced them, so provenance is readable from a filename. `08_verify_invariants.py` will fail on any artifact whose prefix matches no script.

## Status

Nothing has been pulled and nothing has been annotated.

The data comes before the pilot, not after. An earlier reading of the plan had the pilot as the first gate, but 250 annotated claims cannot exist without transcripts, and `StructuredCoverage` cannot be computed without filing dates and XBRL facts. Acquisition is the first task.

Three companion tables block the pilot, and two of the three are pure data-engineering with no annotation involved.

| File | Needed by | Contents |
|---|---|---|
| `metric_classes.csv` | Pass C | metric → FLOW or LEVEL, for the baseline defaults |
| `fiscal_calendar.csv` | Pass C | cik → fiscal year end, 52/53-week flag |
| `filing_dates.csv` | observation status | cik, fiscal_period, form_type, filed_date |

`filing_dates.csv` is what makes the evidence maturity date computable. The fiscal calendar maps "next quarter" onto a period; it cannot say when the report covering that period was filed.

The next thing that can change this project is the pilot. Further conceptual review has reached diminishing returns.

## Glossary

Terms used above, for readers coming from outside finance.

| Term | What it means |
|---|---|
| **8-K** | A filing for events between scheduled reports. The earnings press release is usually an attachment to one. |
| **10-Q / 10-K** | The quarterly and annual reports a US public company must file. |
| **Adjudication** | Deciding whether a claim turned out to be supported or refuted, once the evidence exists. Borrowed from law, where it means settling a disputed matter; here the dispute is between what management predicted and what the filings later showed. It is the second half of the pipeline: resolution turns the sentence into something checkable, adjudication does the checking. |
| **ARR** | ACL Rolling Review, the shared reviewing system for the main natural language processing conferences. |
| **As-first-reported** | The value as originally filed, before any later restatement. Using restated values would leak information that was not available at the time. |
| **CIK** | The SEC's unique identifier for a filer. |
| **Cohen's kappa** | A measure of agreement between two annotators that corrects for agreement by chance. |
| **Company Facts** | The SEC endpoint serving those tagged values for a given company. |
| **Consensus estimate** | The average of analysts' forecasts for a figure. Beating or missing it is what "earnings surprise" refers to. |
| **Earnings call** | A quarterly conference call where a company's executives discuss results and answer analyst questions. Split into prepared remarks and a Q&A session. |
| **Earnings miss** | Reported results below the consensus estimate. |
| **EBITDA** | Earnings before interest, taxes, depreciation and amortisation. A widely used non-GAAP profitability measure. |
| **EDGAR** | The SEC's public database of those filings. Free, no key required. |
| **EPS** | Earnings per share. Net profit divided by shares outstanding. |
| **Filing date** | When a report actually reached the SEC. Distinct from the period it covers, and often weeks later. |
| **Fiscal quarter** | A company's own accounting quarter. Not necessarily aligned to the calendar; some retailers use 52- or 53-week years. |
| **GAAP** | Generally Accepted Accounting Principles, the standard US rules for how a figure must be calculated. What XBRL tags. |
| **Guidance** | A forward-looking statement by management about expected future performance. |
| **NEI** | Not Enough Information. The standard third label in fact-verification work, alongside supported and refuted. |
| **Non-GAAP** | A company-defined adjustment to a GAAP figure, such as excluding one-off costs. Common in guidance, and not present in XBRL, which is the central constraint on this project. |
| **Resolution** | Turning a claim sentence into a checkable proposition: which metric, measured against what, over which period, moving which way. Happens before any evidence is consulted, and produces nothing but structure. Not to be confused with adjudication, which comes after and produces a verdict. |
| **SEC** | The US Securities and Exchange Commission, the regulator public companies file with. |
| **XBRL** | A tagging standard that makes filed financial statements machine-readable, so "revenue" can be looked up as a labelled field rather than parsed out of a PDF. |

## References

Peer-reviewed anchors for the task, the annotation axes, and the accounting literature the design builds on.

| Work | Venue | Relevance |
|---|---|---|
| Zhao et al., FinDVer | EMNLP 2024 | Closest NLP benchmark; verifies against contemporaneous evidence |
| Shah et al., NumClaim | FEVER @ ACL 2024 | Numerical claim detection; baseline for the numerical subset |
| Lin et al., Argument-Based Sentiment on Forward-Looking Statements | Findings of ACL 2024 | Forward-looking language, equity research reports |
| Pardawala et al., SubjECTive-QA | NeurIPS 2024 D&B | Earnings-call QA subjectivity; adjacent to falsifiability |
| Aly et al., FEVEROUS | NeurIPS 2021 D&B | SUPPORTED / REFUTED / NEI over structured evidence |
| Rogers & Stocken, Credibility of Management Forecasts | The Accounting Review 2005 | Management forecast credibility |
| Huang, Teoh & Zhang, Tone Management | The Accounting Review 2014 | Abnormal tone; why NRD is not a novelty claim |
| Gow, Larcker & Zakolyukina, Non-Answers During Conference Calls | JAR 2021 | Non-answers as a disclosure choice |

## Contributing

Contributions are welcome from anyone interested in claim verification, financial NLP, or careful annotation. The project is early, which means most of the groundwork is still open and a contribution now shapes what gets built rather than patching what exists.

Good places to start, none of which need a dataset, an API key, or a GPU:

- [Compile the metric class reference table](https://github.com/di37/prospective-claims/issues/1) — beginner. Classify financial metrics as flow or level, which decides each claim's default baseline.
- [Add a worked annotation walkthrough](https://github.com/di37/prospective-claims/issues/2) — beginner. Take one claim through all four passes so a new annotator sees the manual applied.
- [Add unit tests for fiscal calendar alignment](https://github.com/di37/prospective-claims/issues/3) — beginner to intermediate. Small synthetic fixtures, no downloads.

Larger pieces, roughly in the order the project needs them:

| Issue | What it unblocks |
|---|---|
| [Build the EDGAR filing dates table](https://github.com/di37/prospective-claims/issues/4) | Observation status, and therefore the censoring rate |
| [Build the fiscal calendar table](https://github.com/di37/prospective-claims/issues/5) | Temporal resolution for filers whose year does not match the calendar |
| [Pull and inventory the transcript corpus](https://github.com/di37/prospective-claims/issues/6) | Which filers the pilot can sample from |
| [Implement the observation status calculator](https://github.com/di37/prospective-claims/issues/7) | The OBSERVABLE and RIGHT_CENSORED split |
| [Implement the Company Facts client](https://github.com/di37/prospective-claims/issues/8) | Adjudication against as-first-reported values |
| [Annotate a batch of pilot claims](https://github.com/di37/prospective-claims/issues/9) | The pilot itself; needs at least two people annotating independently |
| [Per-field agreement reporting](https://github.com/di37/prospective-claims/issues/10) | The decision gate |
| [Output prefixes and invariant checks](https://github.com/di37/prospective-claims/issues/11) | Provenance and the protocol rules |

[All open issues](https://github.com/di37/prospective-claims/issues).

Comment on an issue before starting so work can be coordinated and nobody duplicates effort. Keep pull requests focused and document any new dependencies.

Two things to know before contributing. `annotation-guidelines.md` is frozen: changing it requires a version bump and a change-log entry, because a rule change alters what every existing annotation means. And the annotation task deliberately gives more weight to careful reading than to code, so a contributor with a finance or accounting background and no Python is genuinely useful here.

Contributors are acknowledged in the repository and in release notes. Where a contribution is substantial and intellectual rather than mechanical, authorship on any resulting paper follows the normal conventions for that.

## Citation

If you use this repository, its annotation guidelines, or any derived annotations, cite it. Commercial use is fine and no permission is needed, but under CC BY 4.0 attribution is a condition of use rather than a courtesy: using the material without credit falls outside the licence.

```bibtex
@misc{hasan2026prospective,
  author = {Hasan, Doula Isham Rashik},
  title  = {Prospective Claim Verification: Checking Forward-Looking Corporate
            Statements Against Evidence That Does Not Exist Yet},
  year   = {2026},
  note   = {Version 0.1.0},
  url    = {https://github.com/di37/prospective-claims}
}
```

`CITATION.cff` carries the same metadata in machine-readable form, which is what produces the "Cite this repository" button on GitHub.

If a paper comes out of this work, cite that instead and this repository in addition where the annotation scheme or the released annotations are used directly.

## License

Open source and commercially usable. You may use, copy, modify, redistribute, and build products on this work, including for profit, without asking permission and without paying anything.

**The one condition is attribution.** Cite it. That is the whole trade.

Dual-licensed, because the two kinds of material have different needs. The full texts are in [LICENSE](LICENSE) (CC BY 4.0) and [LICENSE-MIT](LICENSE-MIT).

| Material | Licence | You may | You must |
|---|---|---|---|
| Annotation guidelines, README, released annotations and reference tables | CC BY 4.0 | Use commercially, adapt, redistribute | Credit the author, link the licence, note any changes |
| Source code in `src/` and `scripts/` | MIT | Use commercially, adapt, redistribute, sublicense | Preserve the copyright notice |

Documentation and data are CC BY 4.0 rather than MIT specifically so that attribution is enforceable. MIT permits use with no credit beyond the copyright notice, which would not oblige anyone to cite this work. CC BY 4.0 keeps commercial use fully open while making the citation a term of the licence rather than a request.

Neither licence extends to earnings-call transcripts, which remain the property of their providers, or to SEC filing content. Released datasets carry claim spans, character offsets, resolutions, and labels, plus a script that reconstructs the text from its source.

`LICENSE` holds the unmodified CC BY 4.0 legal text so GitHub's detector recognises it, which is why the split above is described here rather than inside that file.
