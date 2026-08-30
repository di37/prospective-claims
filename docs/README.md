# docs

Documents a reader follows rather than runs. Everything here is prose, versioned like code, and cited by the rest of the repository.

The root [README](../README.md) is the entry point: what the project is, the research question, a quick start, and current status. These pages hold the detail it links to, and each one answers a single question so it can be read on its own.

| Document | Answers |
|---|---|
| [`task.md`](task.md) | What the system does with a forward-looking claim, and the label that decides whether it is worth asking |
| [`worked-examples.md`](worked-examples.md) | Five claims taken end to end, covering every outcome the task can produce |
| [`annotation.md`](annotation.md) | The four annotation passes, and why the order is part of the design |
| [`annotation-guidelines.md`](annotation-guidelines.md) | The manual annotators work from. The rules themselves, versioned |
| [`data.md`](data.md) | Where the data comes from, what it costs, and the four properties of it that shaped the design |
| [`pilot.md`](pilot.md) | What 250 annotated claims decide, under a rule written before the numbers arrive |
| [`reproducibility.md`](reproducibility.md) | Environment, seeds, and the protocol rules that keep results rebuildable |
| [`repository.md`](repository.md) | Where everything lives, what writes it, and whether it is committed |
| [`glossary.md`](glossary.md) | Finance and filing terms, for readers coming from outside finance |
| [`references.md`](references.md) | The peer-reviewed work the design builds on |

## The one frozen document

[`annotation-guidelines.md`](annotation-guidelines.md) is frozen; the rest of these pages are not. Changing a rule in it changes what every existing annotation means, so a change requires a version bump, an entry in the change log at the bottom of the file, and re-annotation of anything labelled under the previous version. Nothing has been annotated yet, so no re-annotation is outstanding.

The version is checked by machine. [`check_docs.py`](../.github/scripts/check_docs.py) fails when the version in the record schema and the version in the change log disagree, because a rule that changed without a bump is worse than no versioning at all: every annotation made under it looks valid and means something different.

The reference tables in [`reference/`](../reference/README.md) are frozen with that document and named by it. Section 5.4 dispatches on `metric_classes.csv`, section 5.5 on `fiscal_calendar.csv` and `fiscal_quarters.csv`, section 6 on `filing_dates.csv`. Changing a table is therefore a change to the manual and takes the same version bump.

## What stays at the root

`README.md`, `CONTRIBUTING.md`, `CITATION.cff` and the licences stay where GitHub looks for them. Moving any of them would break the rendered landing page, the "Cite this repository" button, or licence detection.
