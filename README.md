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
  <a href="docs/annotation-guidelines.md"><img alt="Annotation guidelines v1.6" src="https://img.shields.io/badge/guidelines-v1.6-8250df?style=flat-square"></a>
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

## Documentation

Each page answers one question and can be read on its own.

| Document | Answers |
|---|---|
| [The task](docs/task.md) | What the system does with a claim, and the label that decides whether it is worth asking |
| [Worked examples](docs/worked-examples.md) | Five claims end to end, covering every outcome the task can produce |
| [Annotation](docs/annotation.md) | The four passes, and why the order is part of the design |
| [Annotation guidelines](docs/annotation-guidelines.md) | The frozen manual annotators work from. Versioned, with a change log |
| [Data](docs/data.md) | Where the data comes from, and the four properties of it that shaped the design |
| [Pilot and decision gate](docs/pilot.md) | What 250 annotated claims decide, under a rule written before the numbers arrive |
| [Reproducibility](docs/reproducibility.md) | Environment, seeds, and the protocol rules that keep results rebuildable |
| [Repository layout](docs/repository.md) | Where everything lives, what writes it, and whether it is committed |
| [Glossary](docs/glossary.md) | Finance and filing terms, for readers coming from outside finance |
| [References](docs/references.md) | The peer-reviewed work the design builds on |

## Research question

> Can NLP systems resolve forward-looking statements in corporate earnings calls into testable financial propositions, and subsequently verify those propositions against financial evidence that becomes available only in later reporting periods?

| | Question |
|---|---|
| **RQ1** | How accurately can models recover the metric concept, scope, accounting basis, transformation, baseline, temporal window, direction, and threshold implied by a forward-looking claim? |
| **RQ2** | Can models distinguish objectively testable forecasts from underspecified or intrinsically unfalsifiable corporate language? |
| **RQ3** | Given evidence published after the claim, can a system determine whether it was supported or refuted, and recognise when sufficient evidence is unavailable in the designated store? |

Existing financial claim-verification benchmarks verify claims against evidence that already exists, usually inside the same document. This task verifies against evidence that does not exist when the claim is made, which means the evaluation window is not given and has to be inferred.

## What it looks like

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

Four more, covering a refuted claim, one that is falsifiable but unanswerable from the evidence store, one that nothing can settle, and one whose window has not closed yet: [worked examples](docs/worked-examples.md).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12.10, pinned exactly rather than by range, because a range means two people follow the same instructions and get different numbers.

The reference tables are committed, so nothing needs running to read them. To rebuild them from the SEC:

```bash
python scripts/01_build_metric_classes.py
python scripts/02_select_filers.py
python scripts/03_build_filing_dates.py
python scripts/04_build_fiscal_calendar.py
```

In that order: 02 decides who is in the study, 03 joins on the CIKs it writes, and 04 derives the calendars from what 03 pulled. Only 04 is offline. No API key is needed for any of it; the SEC asks for a descriptive User-Agent, which `src/constants.py` sets.

The notebooks in `notebooks/` read each table and say what it is fit for. They generate nothing, so they can be read without being run.

Full detail in [reproducibility](docs/reproducibility.md).

## Status

No transcripts have been pulled and nothing has been annotated. Every companion table the pilot depends on is built.

The data comes before the pilot, not after. An earlier reading of the plan had the pilot as the first gate, but 250 annotated claims cannot exist without transcripts, and `StructuredCoverage` cannot be computed without filing dates and XBRL facts. Acquisition is the first task.

| File | Needed by | Contents | State |
|---|---|---|---|
| `metric_classes.csv` | [Pass C](docs/annotation.md) | metric → FLOW or LEVEL, for the baseline defaults | Built, 49 rows |
| `filers.csv` | every table below | the 150 study filers | Built, 150 rows |
| `filing_dates.csv` | [observation status](docs/task.md) | cik, fiscal_period, form_type, filed_date | Built, 7,118 rows |
| `fiscal_calendar.csv` | [Pass C](docs/annotation.md) | cik → fiscal year end, 52/53-week flag | Built, 150 rows |
| `fiscal_quarters.csv` | [Pass C](docs/annotation.md) | cik, fiscal year, quarter → period end | Built, 7,030 rows |

`filing_dates.csv` is what makes the evidence maturity date computable. The fiscal calendar maps "next quarter" onto a period; it cannot say when the report covering that period was filed.

Each table carries a provenance record and a notebook that reads it and states what it is fit for. Filer selection screens candidates on revenue over total assets, which removes one company that tagged its revenue a thousand-fold too high and would otherwise have ranked 25th. One known limitation is recorded rather than fixed: six corporate families hold twelve of the 150 slots, because the dedupe is per CIK and cannot see one business filing under two. See [`reference/README.md`](reference/README.md).

The next thing that can change this project is the pilot. Further conceptual review has reached diminishing returns.

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

Two things to know before contributing. [`docs/annotation-guidelines.md`](docs/annotation-guidelines.md) is frozen: changing it requires a version bump and a change-log entry, because a rule change alters what every existing annotation means. And the annotation task deliberately gives more weight to careful reading than to code, so a contributor with a finance or accounting background and no Python is genuinely useful here.

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
