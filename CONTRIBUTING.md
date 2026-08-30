# Contributing

Thank you for your interest in this project.

It studies whether NLP systems can resolve forward-looking claims from earnings calls into testable propositions and then verify them against financial evidence published afterwards. The work is early: most of the groundwork is still open, so a contribution now shapes what gets built rather than patching what exists.

## Ways to contribute

Not all of this is code. The annotation work weights careful reading over programming, so a contributor with a finance or accounting background and no Python is genuinely useful here.

- Annotating pilot claims under the manual
- Building the reference tables the manual depends on
- Implementing the EDGAR and XBRL data clients
- Writing tests, particularly around fiscal calendar and date logic
- Improving documentation, worked examples, and the glossary
- Reporting anything in the annotation manual that is ambiguous, contradictory, or unworkable in practice
- Reporting broken links, wrong section references, or errors in the worked examples

That sixth item is worth taking seriously. The manual has been through several rounds of internal review, and every round found a real internal inconsistency. Finding another is a contribution, not a nuisance.

## Before you start

Comment on the issue you intend to work on. This coordinates effort and avoids two people building the same table.

If no issue covers what you have in mind, open one first and describe it. That is cheaper for both of us than a pull request that turns out to be out of scope.

The open issues are listed in the [Contributing section of the README](README.md#contributing), grouped by entry-level and larger pieces.

## Getting started

```bash
git clone https://github.com/di37/prospective-claims.git
cd prospective-claims
```

There is no build step yet, because there is no code yet. Data acquisition comes first: 250 annotated claims cannot exist without transcripts, and the coverage figure that gates the project cannot be computed without filing dates and XBRL facts.

No paid API key is needed for any currently open issue. The SEC endpoints are free and require no key, only a descriptive User-Agent and respect for the published rate limits.

## The annotation manual is frozen

[`docs/annotation-guidelines.md`](docs/annotation-guidelines.md) is a frozen document. Changing a rule changes what every existing annotation means, so any change requires a version bump, an entry in the change log at the bottom of the file, and re-annotation of anything labelled under the previous version.

This is not a barrier to reporting problems with it. If a rule is ambiguous or contradicts another, say so in an issue. Several such reports have already improved it.

## Decisions that should not be quietly reversed

Each of these looks like an obvious simplification and each one reintroduces a defect that was found and fixed. If you think one is wrong, open an issue and argue it rather than changing it in a pull request.

**An unstated evaluation window resolves to UNRESOLVED.** It is never defaulted to next quarter. Window inference is one of the contributions under study, and defaulting it manufactures easy labels for the exact capability being measured.

**Observability is decided from the filing calendar, not from whether a fact exists.** A claim whose evidence turns out to be absent has no fact whose publication date could be inspected, so deciding observability by first locating the evidence is circular.

**Provenance never routes into the NOT_ENOUGH_EVIDENCE label.** NEI is a property of the evidence store; whether a resolution rests on a policy default is a property of the resolution. Merging them collapses two axes that are deliberately independent.

**The decision gate uses StructuredCoverage over OBSERVABLE claims**, not a single coverage ratio over everything. A single ratio lets right-censoring depress the figure and makes the project's direction depend on when the data happened to be collected.

**Falsifiability is judged from the claim text alone, before the evidence store is opened.** An annotator who has just supplied a default baseline is primed to call the claim checkable.

## If you are contributing code

Conventions, in short. Configuration objects are pydantic models, frozen, with unknown fields forbidden, so a mistyped keyword is an error rather than an ignored setting. Docstrings are Google style on every public callable. Modules are organised with `# region` blocks. Code in `src/` is importable with no side effects; anything that produces results is a numbered script in `scripts/`.

Artifacts are written through the shared writers, which derive an output prefix from the running script's filename, so every table and figure names the script that produced it.

Notebooks read results and interpret them. They do not write tables, and they do not define figures inline; they render builders that live in `src`, so every committed figure is reproducible by running a script.

## If you are annotating

Read [`docs/annotation-guidelines.md`](docs/annotation-guidelines.md) end to end before starting. The four-pass order matters, and so does the rule that falsifiability is judged before resolution.

Complete each pass across your whole batch before starting the next. Do not take one claim end to end.

Keep the evidence store closed during Passes B and C. If you already know an outcome for a company you follow, annotate anyway and set the `prior_knowledge` flag so the effect can be measured.

Do not discuss claims with another annotator while working. Agreement is measured on independent judgments, and discussion inflates it.

Log anything the policy registry does not cover in `annotations/policy_gaps.md` rather than inventing a default. That log is a deliverable.

## Before you submit

- Your code runs without errors, and any new dependency is documented
- Tests pass, and new logic has tests that would fail without it
- Nothing under `data/` is committed
- Transcript text is not committed; it belongs to its providers
- `docs/annotation-guidelines.md` is unchanged, or the version and change log were updated together
- Links and section references in any documentation you touched still resolve

## Pull requests

Keep them focused. One issue per pull request where possible.

Explain what you did and why in the description. If you made a judgment call the issue did not specify, say so explicitly rather than leaving it to be discovered in review.

## Acknowledgement and licensing

Contributors are acknowledged in the repository and in release notes. Where a contribution is substantial and intellectual rather than mechanical, authorship on any resulting paper follows the normal conventions for that.

By contributing you agree that your contributions are licensed under the same terms as the project: CC BY 4.0 for documentation and data, MIT for source code. See [LICENSE](LICENSE) and [LICENSE-MIT](LICENSE-MIT).
