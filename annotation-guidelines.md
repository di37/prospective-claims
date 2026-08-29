# Annotation Guidelines — Prospective Claim Verification Pilot

**Status: frozen for the pilot.** Any change after the first claim is annotated requires a version bump, a line in the change log, and re-annotation of everything labelled under the previous version. Agreement scores are reported against the exact version used.

**Scope.** These guidelines cover the 250-claim pilot only. The study's decision gate runs on the numbers this pilot produces, so the guidelines are written to make those numbers mean what they claim to mean. Conventions that turn out to be unworkable are recorded as findings, not silently amended.

**Vocabulary.** Section 13 is a glossary of every term and label value used here, alphabetically. Consult it rather than guessing at a label name.

**Annotators.** Two, working independently. Do not discuss claims while annotating. Agreement is measured on independent judgments; discussion during annotation inflates it and destroys the number the pilot exists to produce. Disagreements are adjudicated after all 250 claims are complete.

---

## 1. Procedure

Four passes, in this order. The order is not a convenience — it is what keeps the two annotation axes independent.

```
Pass A   Identify claims        transcript passages, no cue list
Pass B   Falsifiability         claim text only, no evidence store
Pass C   Resolution + provenance claim text only, no evidence store
   *     Observation status     computed, not annotated
Pass D   Evidence availability  OBSERVABLE claims only, evidence store open
```

Two rules make the passes work:

**Falsifiability is judged before resolution.** Resolution involves supplying policy defaults for missing fields. Having just supplied a default baseline, you are primed to consider the claim checkable. Judging falsifiability first keeps it a judgment about the sentence rather than about what the manual let you fill in.

**Passes B and C happen with the evidence store closed.** Do not open XBRL data, do not look up what actually happened, do not check whether the company later filed the metric. If you already know the outcome for a company you follow, annotate it anyway and flag the record with `prior_knowledge: true` so the effect can be measured.

Complete each pass across all 250 claims before starting the next. Do not annotate one claim end-to-end.

---

## 2. Pass A — Identifying claims

### 2.1 Sampling

Passages are drawn before annotation begins:

1. Stratify earnings calls by sector and year across 2012–2024.
2. Randomly select **passages** — contiguous speaker turns, not whole calls — so that sector and year coverage survives.
3. Annotate every sampled passage exhaustively.

Do not use a cue list, keyword search, or detector output to find claims. The point of exhaustive passage annotation is an unbiased denominator; searching for `expect` reintroduces exactly the bias the design removes. Read the passage and mark what is there.

### 2.2 What counts as a forward-looking claim

A span qualifies when **all four** hold:

1. **Spoken by company management.** CEO, CFO, or another company executive. Analyst questions do not qualify even when they contain a forward-looking premise. The operator does not qualify.
2. **About the company's own future state or performance.** Not the industry in general, not a competitor, not the macroeconomy — unless the claim ties the outcome to the company.
3. **Assertive.** The speaker commits to an expectation. Questions, hypotheticals posed for illustration, and pure restatements of an analyst's framing do not qualify.
4. **Not boilerplate.** Safe-harbour language, forward-looking-statement disclaimers, and legal recitations are excluded.

### 2.3 Include / exclude

| Example | Decision |
|---|---|
| "We expect revenue between $2.1 and $2.3 billion next quarter." | **Include** — quantified guidance |
| "Margins should improve as the year progresses." | **Include** — directional, no number |
| "We remain confident in the long-term opportunity." | **Include** — annotate as UNFALSIFIABLE in Pass B |
| "If demand holds, we would expect inventory to normalise." | **Include** — conditional, flag `conditional: true` |
| "We are reaffirming the guidance we gave in February." | **Include** — restated guidance is a claim |
| "We aim to be the leader in this category." | **Include** — aspirational, UNFALSIFIABLE |
| "We have seen improvement over the last two quarters." | **Exclude** — past tense, not forward-looking |
| "Analysts are modelling roughly 12% growth." | **Exclude** — attributed to a third party |
| "How should we think about margins next year?" | **Exclude** — analyst question |
| "The industry is expected to grow at 8%." | **Exclude** — about the market, not the company |
| "Statements made today may constitute forward-looking statements..." | **Exclude** — boilerplate |
| "Let's say hypothetically demand fell 20% — we'd still be fine." | **Include** the second half only; the hypothetical premise is not the claim |

Uncertain cases are included and flagged `borderline: true`. Over-inclusion is recoverable at adjudication; under-inclusion silently corrupts the denominator.

### 2.4 Span boundaries and splitting

Mark the **minimal span that carries the full claim**, including its temporal qualifier.

One sentence may contain several claims. Split on distinct metrics:

> "We expect revenue to grow double digits and margins to expand modestly next quarter."

becomes two claims, each carrying the shared window:

```
C1  "revenue to grow double digits ... next quarter"
C2  "margins to expand modestly next quarter"
```

Do **not** split a single metric across a compound direction ("revenue will dip in Q1 and recover in Q2") — that is one claim with a structured window. Flag it `multi_segment_window: true`.

A claim spanning two sentences is one claim; record both offsets.

### 2.5 Recorded in Pass A

```json
{"claim_id": "", "call_id": "", "speaker_role": "CEO|CFO|OTHER_EXEC",
 "section": "PREPARED|QA", "char_start": 0, "char_end": 0, "text": "",
 "conditional": false, "borderline": false, "multi_segment_window": false,
 "prior_knowledge": false}
```

Also record, per passage: passage id, sector, fiscal year, total claims found, and annotation minutes. The claim count per passage is what produces the denominator.

---

## 3. Pass B — Falsifiability

One label per claim, from the claim text and its immediate context only.

### 3.1 The three values

**FALSIFIABLE** — Two competent analysts with complete future financial data would reach the same verdict without consulting this manual. The metric, the direction, and the period are determinate from what was said.

**UNDERSPECIFIED** — The claim names a real, reported quantity and a direction, but at least one field needed to settle it is missing from the claim and its context. It becomes checkable only once the policy registry supplies a default. Most directional guidance lands here, because management rarely states what it is comparing against.

**UNFALSIFIABLE** — No assignment of the missing fields makes it checkable. Either it names no measurable quantity, or the predicate is not the kind of thing an observation settles.

### 3.2 The test

Apply in order:

```
Q1. Does the claim refer to a quantity that varies over time
    and is reported somewhere in financial disclosure?
      no  -> UNFALSIFIABLE
      yes -> Q2

Q2. Are metric, direction, evaluation period, AND the thing
    being compared against all recoverable from the claim and
    its immediate context, WITHOUT consulting section 5?
      yes -> FALSIFIABLE
      no  -> Q3

Q3. Is there some assignment of the missing fields under which
    two analysts would agree on the verdict?
      yes -> UNDERSPECIFIED
      no  -> UNFALSIFIABLE
```

Q1 asks about *any* financial disclosure, not about XBRL. A claim about adjusted EBITDA is FALSIFIABLE even though XBRL will not carry it. Whether the evidence store holds it is Pass D's question, and mixing the two is the specific error this design exists to prevent.

Q2 asks only whether the comparison is recoverable from the text, not which default section 5 would supply. You do not need the registry to answer it, and you should not open it. THRESHOLD and RANGE claims need no comparison basis, so they pass Q2 on metric, direction, and period alone.

FALSIFIABLE therefore means self-contained: settleable without the manual. Expect it to be the smaller class, concentrated in threshold, range, and explicitly-benchmarked claims. That is the intended reading, and the FALSIFIABLE to UNDERSPECIFIED ratio is one of the pilot's reported numbers rather than something to engineer upward.

Both classes stay eligible for adjudication, and results are reported separately for each. UNFALSIFIABLE claims are excluded outright. Eligibility is not the same as inclusion: a FALSIFIABLE or UNDERSPECIFIED claim is still dropped from adjudication if its window is UNRESOLVED, if it is right-censored, or if it is conditional. Those exclusions are applied later, in sections 5.7 and 6, and they are not your concern in Pass B.

### 3.3 Calibration examples

| Claim | Label | Why |
|---|---|---|
| "Gross margin will exceed 71% in Q3." | FALSIFIABLE | metric, threshold, period all stated |
| "Adjusted EBITDA margin will be above 22% next quarter." | FALSIFIABLE | non-GAAP, but determinate — Pass D handles the store |
| "Revenue will grow next quarter." | UNDERSPECIFIED | metric, direction, period stated; comparison basis is not, and section 5 must supply it |
| "Revenue will grow year over year next quarter." | FALSIFIABLE | comparison basis stated, so nothing is left to the manual |
| "Margins should improve." | UNDERSPECIFIED | no window, no baseline |
| "Inventory should normalise over the next two quarters." | UNDERSPECIFIED | window stated; "normal" needs a definition |
| "We expect meaningful operating leverage over time." | UNDERSPECIFIED | real metric, no window at all |
| "We are well positioned for the year ahead." | UNFALSIFIABLE | no measurable quantity |
| "We remain excited about the long-term opportunity." | UNFALSIFIABLE | attitude, not quantity |
| "We aim to be the leader in this category." | UNFALSIFIABLE | "leader" is not a reported quantity |
| "We will continue to invest in R&D." | UNDERSPECIFIED | R&D expense is reported; "continue" implies direction |
| "Our team is executing exceptionally well." | UNFALSIFIABLE | evaluative |

Two habits to avoid. Do not mark a claim UNFALSIFIABLE because you personally cannot find the data; that judgment belongs to Pass D. Do not mark a claim FALSIFIABLE because you can imagine a reasonable default; a claim that needs a default is UNDERSPECIFIED.

---

## 4. Pass C — Resolution and provenance

Resolve every claim, including UNFALSIFIABLE ones, as far as the text allows. Fields that cannot be resolved take `UNRESOLVED`.

### 4.1 Fields

```
m.concept     the financial quantity
m.scope       CONSOLIDATED | SEGMENT:<name> | GEOGRAPHY:<name> | PRODUCT:<name>
m.basis       GAAP | ADJUSTED_NON_GAAP | UNSPECIFIED
m.transform   NONE | MARGIN | GROWTH_RATE | PER_SHARE
              | SCALED_BY_REVENUE | CONSTANT_CURRENCY
b             the comparison baseline
w             evaluation window, fiscal quarters relative to the claim quarter
d             INCREASE | DECREASE | TOWARD_BASELINE | MAINTAIN | THRESHOLD | RANGE
tau           numeric threshold or range, or NONE
```

`m.concept` is written as a US-GAAP taxonomy element where one applies (`us-gaap:InventoryNet`, `us-gaap:GrossProfit`). Where none applies, write the plain-language concept and set `m.basis: ADJUSTED_NON_GAAP` — do not force a bad taxonomy match. Forcing matches is the failure mode that would make metric grounding look easier than it is.

`w` is a closed interval of fiscal quarters relative to the quarter of the call, `[t+1, t+2]`. Single quarters are `[t+1, t+1]`.

### 4.2 Provenance

Every field carries a provenance tag. The primary annotation is binary:

```
STATED     present in the claim or its immediate context
SUPPLIED   filled from the policy registry in section 5
```

Fields `b` and `w` additionally take the four-way refinement:

```
EXPLICIT           stated outright
CONTEXT_INFERRED   recoverable from surrounding turns in the same call
POLICY_DEFAULT     supplied by section 5
UNRESOLVED         no defensible value, even with policy
NOT_APPLICABLE     field not required for this claim type
                   (baseline on THRESHOLD and RANGE claims)
```

`CONTEXT_INFERRED` requires that you can point to the turn you inferred it from. Record the character offset in `b_context_ref` / `w_context_ref`. If you cannot point at it, it is `POLICY_DEFAULT`.

This distinction carries the paper's stratified results. Being generous with `CONTEXT_INFERRED` where you actually applied a default will make the model look like it understands language when it has learned the manual.

### 4.3 Worked example

> "We expect inventory levels to normalise over the next two quarters."

```json
{
  "m": {"concept": "us-gaap:InventoryNet", "scope": "CONSOLIDATED",
        "basis": "UNSPECIFIED", "transform": "SCALED_BY_REVENUE"},
  "b": "trailing 8-quarter median of InventoryNet/Revenues",
  "w": [1, 2],
  "d": "TOWARD_BASELINE",
  "tau": null,
  "provenance": {
    "m.concept": "STATED", "m.scope": "SUPPLIED", "m.basis": "SUPPLIED",
    "m.transform": "SUPPLIED", "d": "STATED",
    "b": "POLICY_DEFAULT", "w": "EXPLICIT"
  }
}
```

Management said "inventory," "normalise," and "next two quarters." Everything else — consolidated scope, unspecified basis, revenue scaling, the 8-quarter median — came from section 5. Basis is recorded as UNSPECIFIED rather than GAAP: per section 5.2 the mapping to GAAP happens at adjudication, so its cost stays visible in the provenance statistics. That is three SUPPLIED fields and one POLICY_DEFAULT out of seven, and the record now says so.

> "We expect adjusted operating margin in North America to exceed 18% on a constant-currency basis next quarter."

```json
{
  "m": {"concept": "operating_margin", "scope": "GEOGRAPHY:north_america",
        "basis": "ADJUSTED_NON_GAAP", "transform": "CONSTANT_CURRENCY"},
  "b": null,
  "w": [1, 1],
  "d": "THRESHOLD",
  "tau": {"op": ">", "value": 18.0, "unit": "percent"},
  "provenance": {
    "m.concept": "STATED", "m.scope": "STATED", "m.basis": "STATED",
    "m.transform": "STATED", "d": "STATED", "b": "NOT_APPLICABLE", "w": "EXPLICIT"
  }
}
```

Threshold and range claims need no baseline; `b` is `null` with provenance `NOT_APPLICABLE`. Do not use `STATED`, since management stated no baseline, and do not use `UNRESOLVED`, which means a needed value could not be found. `NOT_APPLICABLE` keeps these claims out of the baseline provenance statistics entirely. Note this claim is fully STATED and still will not be adjudicable — non-GAAP, geographic scope, constant currency. Falsifiability and evidence availability are different questions.

---

## 5. Policy registry

These are the manual's defaults. Applying any of them sets provenance `SUPPLIED` or `POLICY_DEFAULT`. Do not invent defaults outside this list; if a claim needs one that is not here, mark the field `UNRESOLVED` and log it in `policy_gaps.md`. The gap log is a pilot output.

### 5.1 Scope

Default `CONSOLIDATED` unless a segment, geography, or product is named.

### 5.2 Basis

Default `UNSPECIFIED` at annotation. `UNSPECIFIED` maps to `GAAP` at adjudication, as a POLICY_DEFAULT. Annotate what was said; the mapping happens downstream so its cost stays measurable.

### 5.3 Transform

| Metric type | Default transform |
|---|---|
| Margin language ("margins", "margin rate") | `MARGIN` |
| Balance-sheet level in a normalisation claim | `SCALED_BY_REVENUE` |
| "grow", "growth", "up/down X%" | `GROWTH_RATE` |
| EPS language | `PER_SHARE` |
| Everything else | `NONE` |

### 5.4 Baseline

Applied only when `d` is INCREASE, DECREASE, or MAINTAIN and no baseline is stated.

| Metric class | Default baseline | Rationale |
|---|---|---|
| Flow metrics — revenue, income, expense, margin | **same quarter prior year** | how management overwhelmingly speaks about flows |
| Level metrics — inventory, cash, debt, receivables, headcount | **immediately prior quarter** | levels are compared sequentially |
| TOWARD_BASELINE ("normalise", "return to normal") | **trailing 8-quarter median** of the metric under its default transform | "normal" needs a definition and this one is stable and public |

Metric class comes from `metric_classes.csv`, frozen with this document. A metric absent from that file makes the field `UNRESOLVED` and goes in the gap log.

### 5.5 Window

| Phrasing | Window |
|---|---|
| "next quarter", "Q3" (next by fiscal calendar) | `[1, 1]` |
| "the next two quarters", "first half" | `[1, 2]` |
| "this year", "fiscal 2026" (the current fiscal year) | remaining quarters of that fiscal year |
| "next year" | `[n+1 .. n+4]`, the four quarters of the next fiscal year |
| "second half" | the two quarters composing H2 of the named fiscal year |
| "over time", "longer term", "in the coming years", "eventually" | **UNRESOLVED** |
| No temporal expression at all | **UNRESOLVED** |

**Do not default an unstated window to next quarter.** It is tempting and it is wrong: window inference is a headline contribution, and defaulting it manufactures easy labels for the exact capability under test. An unstated window makes the claim UNDERSPECIFIED in Pass B and `UNRESOLVED` here.

Fiscal, not calendar. "Next quarter" means the next fiscal quarter for that filer. Companies with January or June year-ends and 52/53-week retail calendars are handled by `fiscal_calendar.csv`, frozen with this document.

### 5.6 Direction and materiality

| Language | `d` |
|---|---|
| "grow", "improve", "expand", "increase", "up" | INCREASE |
| "decline", "contract", "decrease", "down", "ease" | DECREASE |
| "normalise", "return to normal", "come back in line" | TOWARD_BASELINE |
| "hold", "remain stable", "flat", "sustain" | MAINTAIN |
| "exceed", "above", "at least", "below", "under" | THRESHOLD |
| "between X and Y", "in the range of" | RANGE |

Materiality band, applied at adjudication and recorded here so annotators know what the labels will mean:

```
default band = 0            directional claims are judged on sign alone
sensitivity  = 1%, 2% relative, reported as an ablation
```

For INCREASE / DECREASE: SUPPORTED if the realised change is in the stated direction; REFUTED otherwise. A flat outcome REFUTES a claim of improvement — management said it would improve and it did not.

For TOWARD_BASELINE: SUPPORTED if the absolute gap to baseline is smaller at window end than at claim date, by more than the band.

For MAINTAIN: SUPPORTED if the absolute change is within the band. This is the one direction where the band cannot be zero; MAINTAIN uses the 2% relative band by default.

### 5.7 Conditional claims

Annotate the consequent as the claim, and record the antecedent in `condition_text`. Do not attempt to verify the antecedent in the pilot.

Conditionals are excluded from primary adjudication. If the antecedent fails, so demand does not hold, then the consequent failing does not refute anything management said, and scoring it REFUTED would be a logic error. Verifying antecedents is out of scope for six weeks, so conditionals are annotated in full for resolution and falsifiability, reported as their own stratum with counts, and left out of the headline SUPPORTED / REFUTED / NEI figures. This matches the treatment of right-censored claims: annotated, counted, not scored.

---

## 6. Observation status — computed, not annotated

Assigned by script after Pass C, not by hand. Given evidence cutoff `T`:

```
M(c)  = max{ filing dates of the periodic reports required to cover w(c) }

OBSERVABLE       end(w(c)) <= T   AND   M(c) <= T
RIGHT_CENSORED   window incomplete   OR   M(c) > T
```

`M(c)` is the claim's **evidence maturity date**. It depends only on the resolved window, the filer's reporting calendar, and which periodic reports cover those periods. It does not depend on any particular fact existing.

Defining observability on the adjudicating fact instead would be circular. A claim whose evidence turns out to be ABSENT has no such fact to date, and NON-GAAP-ONLY and FILING-TEXT claims have no XBRL fact whose publication date can be inspected. Observability cannot be decided by first locating the evidence whose existence it gates.

The causal order is therefore fixed:

```
claim
  -> resolve window w(c)
  -> identify the reporting periods w(c) spans
  -> have the filings covering those periods been published by T?
       no  -> RIGHT_CENSORED          (stop; no evidence inspection)
       yes -> OBSERVABLE
                -> inspect evidence
                -> GAAP-XBRL | FILING-TEXT | NON-GAAP-ONLY | ABSENT
```

Filing dates are **actual EDGAR filing dates**, not statutory deadlines. Large accelerated filers have 40 days after period end for a 10-Q and 60 for a 10-K, so window-end plus roughly 75 days is the practical floor for `M(c)` — but filers vary and the real dates are available, so use them.

Where a required periodic report has not been filed by `T` and its deadline has passed, the filer is delinquent: `M(c)` is undefined, the claim is RIGHT_CENSORED, and it is flagged `delinquent_filer: true`. That is a different situation from an immature window and is reported separately.

A claim whose `w` is `UNRESOLVED` cannot be assigned a status; it is `NOT_APPLICABLE` and is excluded from adjudication along with the right-censored.

---

## 7. Pass D — Evidence availability

**OBSERVABLE claims only.** The evidence store is open for this pass and only this pass.

```
Evidence store E = SEC Company Facts (XBRL, as-first-reported)
                 + XBRL calculation linkbases
```

| Value | Meaning |
|---|---|
| `GAAP-XBRL` | the metric, at the stated scope and basis, is retrievable from E for the window |
| `FILING-TEXT` | a GAAP measure, not in E, but present in the 10-Q/10-K text or tables, or in the earnings release |
| `NON-GAAP-ONLY` | the resolved metric is non-GAAP, wherever it appears |
| `ABSENT` | not found in the bounded search below |
| `N/A` | claim is RIGHT_CENSORED or NOT_APPLICABLE |

Resolve `UNSPECIFIED` basis first. Pass C records `m.basis` as `UNSPECIFIED` whenever management did not say which basis they meant, and section 5.2 maps `UNSPECIFIED` to `GAAP`. Apply that mapping here, before testing availability: search XBRL for the GAAP measure. Do not treat `UNSPECIFIED` as an unresolved basis and do not go looking for a non-GAAP variant. The Pass C record stays `UNSPECIFIED`; only this pass's search treats it as GAAP, so the provenance statistics still show what the default cost.

Precedence: check basis before location. These two labels would otherwise overlap. Adjusted EBITDA printed in an earnings release is both non-GAAP and present in a document, so two annotators following the manual could pick different labels. Basis decides first. If the resolved `m.basis` is `ADJUSTED_NON_GAAP`, the label is `NON-GAAP-ONLY` wherever the figure appears. `FILING-TEXT` is reserved for GAAP measures that exist in a document but are not tagged in XBRL, such as untagged segment detail.

Bounded search before `ABSENT`. Check exactly these three, in order, and stop at the first hit:

```
1. XBRL Company Facts for that filer and period      -> GAAP-XBRL
2. The 10-Q or 10-K covering the period, text and tables
3. The earnings release for the period (8-K exhibit 99.1)
```

Not found in all three means `ABSENT`. Do not search investor presentations, the company website, the call transcript itself, or any third-party source, because an unbounded search cannot be replicated by a second annotator. Record which of the three were checked in `evidence_sources_checked`.

Judge availability against **what was resolved**, not against a close relative. If the claim resolves to adjusted operating margin for North America and E holds only consolidated GAAP operating income, that is `NON-GAAP-ONLY`, not `GAAP-XBRL`. Substituting a nearby metric here is the single most damaging error available in this pass: it inflates coverage, which is what the decision gate runs on.

Use as-first-reported values. If a fact appears only in a later restatement, it was not available and does not count.

`ABSENT` should be rare. Most apparent absences are `NON-GAAP-ONLY` or `FILING-TEXT`.

---

## 8. Timing

Record wall-clock minutes per claim per pass. This decides whether the scheme scales to 2,000 claims: if the median total exceeds **four minutes per claim**, the four-way provenance refinement on `b` and `w` is dropped and STATED/SUPPLIED is used throughout. That decision is made on the timing data, not by argument.

Log interruptions rather than including them. Do not annotate for more than 90 minutes without a break; agreement degrades and the pilot is measuring the scheme, not stamina.

---

## 9. Disagreement handling

Do not resolve disagreements while annotating. After all 250 claims are complete in all passes:

1. Compute per-field agreement on the independent labels. **These are the numbers reported in the paper.** They are computed once and never recomputed after adjudication.
2. Adjudicate disagreements jointly. The adjudicated set becomes gold.
3. Any disagreement traced to an ambiguity in this document is logged in `policy_gaps.md`, whether or not it is resolved. The gap log is a deliverable — it is what tells v2 of these guidelines what to fix.

Fields scoring below **kappa 0.5** are demoted out of the headline task and reported as a negative finding with the default that will be applied instead. `b` is the field most at risk; that is expected and reporting it honestly is more valuable than engineering around it.

---

## 10. Record schema

One JSONL record per claim, accumulating across passes.

```json
{
  "claim_id": "2019Q2_XXXX_0007",
  "annotator": "A|B",
  "guidelines_version": "1.5",

  "call_id": "", "sector": "", "fiscal_year": 0, "fiscal_quarter": 0,
  "speaker_role": "CFO", "section": "PREPARED|QA",
  "char_start": 0, "char_end": 0, "text": "",
  "conditional": false, "condition_text": null,
  "evidence_sources_checked": [],
  "borderline": false, "multi_segment_window": false,
  "prior_knowledge": false,

  "falsifiability": "FALSIFIABLE|UNDERSPECIFIED|UNFALSIFIABLE",

  "m": {"concept": "", "scope": "", "basis": "", "transform": ""},
  "b": null, "b_context_ref": null,
  "w": [1, 1], "w_context_ref": null,
  "d": "", "tau": null,

  "provenance": {
    "m.concept": "STATED|SUPPLIED", "m.scope": "STATED|SUPPLIED",
    "m.basis": "STATED|SUPPLIED", "m.transform": "STATED|SUPPLIED",
    "d": "STATED|SUPPLIED",
    "b": "EXPLICIT|CONTEXT_INFERRED|POLICY_DEFAULT|UNRESOLVED|NOT_APPLICABLE",
    "w": "EXPLICIT|CONTEXT_INFERRED|POLICY_DEFAULT|UNRESOLVED"
  },

  "observation_status": "OBSERVABLE|RIGHT_CENSORED|NOT_APPLICABLE",
  "delinquent_filer": false,
  "evidence_availability": "GAAP-XBRL|FILING-TEXT|NON-GAAP-ONLY|ABSENT|N/A",
  "evidence_note": null,

  "minutes": {"pass_b": 0.0, "pass_c": 0.0, "pass_d": 0.0}
}
```

Per-passage records go in a separate file:

```json
{"passage_id": "", "call_id": "", "sector": "", "fiscal_year": 0,
 "char_start": 0, "char_end": 0, "claims_found": 0, "minutes": 0.0}
```

`claims_found` summed across passages is the denominator for `CensoringRate`. Getting it right matters as much as any label in this document.

---

## 11. Frozen companion files

Versioned with these guidelines; changing any of them is a version bump.

```
metric_classes.csv    metric -> FLOW | LEVEL, for the baseline defaults        (sec 5.4)
fiscal_calendar.csv   cik -> fiscal year end, 52/53-week flag                 (sec 5.5)
filing_dates.csv      cik, fiscal_period, form_type, filed_date               (sec 6)
evidence_cutoff.txt   the single date T                                       (sec 6)
policy_gaps.md        running log of cases the registry does not cover        (sec 5)
```

`filing_dates.csv` is what makes `M(c)` computable. `fiscal_calendar.csv` maps "next quarter" onto a fiscal period; it cannot say when the report covering that period was actually filed, and `M(c)` is defined on filing dates rather than period ends precisely so that observability never depends on a fact existing. Source it from the EDGAR submissions API (`data.sec.gov/submissions/CIK##########.json`), which gives `form`, `period`, and `filingDate` per filer. Take the **first** filing covering a period, not an amendment: a 10-Q/A published after `T` does not make a claim observable, and the original 10-Q that arrived on time does.

A filer present in the pilot sample but missing from `filing_dates.csv` blocks status assignment; treat that as a data error to fix, never as RIGHT_CENSORED.

---

## 12. What the pilot outputs

```
per-field kappa            all resolution fields, both axes, provenance
CensoringRate              # RIGHT_CENSORED / # all forward-looking
  ..immature window         window has not closed by T
  ..awaiting filing         window closed, M(c) > T
  ..delinquent filer        deadline passed, report not filed
StructuredCoverage         # GAAP-XBRL / # OBSERVABLE forward-looking   <- the gate
FalsifiableCoverage        # GAAP-XBRL / # (OBSERVABLE and FALSIFIABLE)
numerical vs qualitative   proportion, from exhaustive passage annotation
prepared vs Q&A            proportion
median annotation minutes  per claim, per pass
policy_gaps.md             cases the registry could not cover
```

`StructuredCoverage` drives the study's decision gate. Nothing about the project's shape is settled until it exists.

---

## 13. Glossary

Terms used in this manual, alphabetically. Label values are given in the case they are recorded in.

| Term | What it means |
|---|---|
| **8-K** | An SEC filing for events between scheduled reports. The quarterly earnings press release is normally exhibit 99.1 of one. |
| **10-Q / 10-K** | The quarterly and annual reports a US public company must file. The 10-K covers the full year and replaces the fourth 10-Q. |
| **ABSENT** | Evidence availability. The resolved metric was not found by the bounded three-source search in section 7. |
| **ADJUSTED_NON_GAAP** | Accounting basis. A company-defined measure rather than a standard one. Never present in the evidence store. |
| **As-first-reported** | The value as originally filed, before any later restatement. Restated values would leak information that was not available at the time of the claim. |
| **Baseline (`b`)** | What a directional claim is measured against. Often unstated, which is why section 5.4 supplies defaults by metric class. |
| **CIK** | The SEC's unique numeric identifier for a filer. The join key in `fiscal_calendar.csv` and `filing_dates.csv`. |
| **Cohen's kappa** | Agreement between two annotators, corrected for agreement by chance. Reported per field; below 0.5 a field is demoted. |
| **Company Facts** | The SEC endpoint serving XBRL-tagged values for one company across its filings. The evidence store for this study. |
| **CONTEXT_INFERRED** | Provenance. Recoverable from surrounding turns in the same call. Requires a character offset you can point at. |
| **Direction (`d`)** | Which way the claim says the metric will move: INCREASE, DECREASE, TOWARD_BASELINE, MAINTAIN, THRESHOLD, or RANGE. |
| **EBITDA** | Earnings before interest, taxes, depreciation and amortisation. A common non-GAAP profitability measure. |
| **EDGAR** | The SEC's public filing database. Source of the filing dates used to compute observation status. |
| **EPS** | Earnings per share. Net profit divided by shares outstanding. |
| **Evidence maturity date (`M(c)`)** | The latest filing date among the reports covering a claim's evaluation window. Computed from the filing calendar, never from whether a particular fact exists. |
| **Evidence store (`E`)** | SEC Company Facts as-first-reported, plus XBRL calculation linkbases. Anything outside it is NEI. |
| **EXPLICIT** | Provenance. Stated outright in the claim. |
| **FALSIFIABLE** | Falsifiability. Settleable without the policy registry: metric, direction, period and comparison basis are all in the text. |
| **FILING-TEXT** | Evidence availability. A GAAP measure present in a filing's text or tables but not tagged in XBRL. |
| **Fiscal quarter** | A company's own accounting quarter, which need not align to the calendar. Some retailers use 52- or 53-week years. |
| **GAAP** | Generally Accepted Accounting Principles. The standard US rules governing how a reported figure is calculated. What XBRL tags. |
| **GAAP-XBRL** | Evidence availability. The resolved metric is retrievable from the evidence store for the window. The only value that reaches binary adjudication. |
| **Guidance** | A forward-looking statement by management about expected future performance. |
| **Metric (`m`)** | The four-part quantity a claim is about: concept, scope, accounting basis, and transform. |
| **NEI** | Not Enough Information. Insufficient evidence *in the designated store*, which is not the same as the evidence not existing. |
| **NON-GAAP-ONLY** | Evidence availability. The resolved metric is non-GAAP, wherever it appears. Takes precedence over FILING-TEXT. |
| **NOT_APPLICABLE** | Provenance. The field is not required for this claim type, as with a baseline on a THRESHOLD claim. |
| **OBSERVABLE** | Observation status. The evaluation window has closed and the filings covering it were published before the cutoff. |
| **POLICY_DEFAULT** | Provenance. Supplied by the registry in section 5 rather than by the speaker. |
| **Prepared remarks** | The scripted opening portion of an earnings call, before analyst questions. |
| **Provenance** | Whether a resolved field came from the speaker or from this manual. The distinction that keeps annotation policy from passing as language understanding. |
| **Q&A** | The analyst question-and-answer portion of an earnings call. |
| **RIGHT_CENSORED** | Observation status. The window has not closed, or the filings covering it are not yet published. Annotated and counted, never scored. |
| **SEC** | The US Securities and Exchange Commission, the regulator public companies file with. |
| **STATED** | Provenance. Present in the claim or its immediate context. |
| **SUPPLIED** | Provenance. Filled from the policy registry in section 5. |
| **THRESHOLD** | Direction. The claim names a level to be exceeded or undercut, so no baseline is needed. |
| **TOWARD_BASELINE** | Direction. "Normalise" or "return to normal": the gap to a historical norm should shrink. |
| **UNDERSPECIFIED** | Falsifiability. A real reported quantity and a direction, but a field needed to settle it is missing and the registry must supply it. |
| **UNFALSIFIABLE** | Falsifiability. No assignment of the missing fields makes the claim checkable. |
| **UNRESOLVED** | Provenance. No defensible value, even with the registry. An unstated evaluation window resolves here rather than defaulting. |
| **Window (`w`)** | The evaluation period, as a closed interval of fiscal quarters relative to the call. Inferring it is one of the study's contributions, which is why it is never defaulted. |
| **XBRL** | The tagging standard that makes filed financial statements machine-readable, so a figure can be looked up as a labelled field. |

## Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-08-29 | Initial freeze for the pilot. |
| 1.5 | 2026-08-29 | Adds section 13, an alphabetical glossary of finance, filing, and label vocabulary, with a pointer from the top. No rule changed. No claims annotated under 1.4; no re-annotation required. |
| 1.4 | 2026-08-29 | Section 7: states that Pass D applies the section 5.2 mapping UNSPECIFIED to GAAP before testing availability, and that the Pass C record is unchanged. Without this an annotator could treat UNSPECIFIED as an unresolved basis and search differently. No claims annotated under 1.3; no re-annotation required. |
| 1.3 | 2026-08-29 | Two consistency fixes. Section 4.3: threshold worked example records `b` provenance as NOT_APPLICABLE, matching the prose below it. Section 3.2: adjudication eligibility restated, since window-UNRESOLVED, right-censored, and conditional claims are also excluded, not only UNFALSIFIABLE. No claims annotated under 1.2; no re-annotation required. |
| 1.2 | 2026-08-29 | Five internal inconsistencies fixed before annotation began. Section 3.2: Q2 now includes the comparison basis, so "Revenue will grow next quarter" is UNDERSPECIFIED rather than FALSIFIABLE, and FALSIFIABLE means settleable without the registry. Section 4.3: inventory example records basis UNSPECIFIED, matching section 5.2. Section 7: NON-GAAP-ONLY takes precedence over FILING-TEXT, and ABSENT requires a bounded three-source search. Section 5.7: conditionals excluded from primary adjudication. Baseline provenance gains NOT_APPLICABLE for threshold and range claims. No claims annotated under 1.1; no re-annotation required. |
| 1.1 | 2026-08-29 | Section 6, observation status: replaced `publication_date(e_c) <= T` with the evidence maturity date `M(c)`, removing a circularity in which observability depended on locating the very fact whose existence observability gates. Added `delinquent_filer` flag. Section 11 adds `filing_dates.csv`, without which `M(c)` is not computable. Section 12 splits CensoringRate by reason. No claims annotated under 1.0; no re-annotation required. |
