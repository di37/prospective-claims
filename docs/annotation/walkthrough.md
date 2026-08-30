# A claim through all four passes

The [annotation guidelines](annotation-guidelines.md) state the rules well and never show one claim moving from a raw sentence to a finished record. This page does that, twice, and cites the section governing every decision so you can check the reasoning against the manual rather than take it on trust.

Read it before your first passage, not instead of the manual. It shows the shape of the work; the manual is what you actually apply.

Each claim leads with a diagram of all four passes. The prose under it is the reference: it says which section governs each decision and why the rule reads the way it does.

The sentences are written for this page. No real company is quoted.

---

## The rule that makes the ordering matter

Passes A, B and C happen with the evidence store shut. You do not look up a single figure until Pass D, and Pass D only runs on claims a script has already marked OBSERVABLE.

That is not procedural fussiness. Section 3.2 spells out the failure it prevents: an annotator who has just looked up a number knows whether the claim is checkable, and will label falsifiability accordingly. Falsifiability is meant to be a judgment about language. Once you have seen the evidence you cannot make it again.

So the record below grows in one direction only. Nothing a later pass learns is allowed back into an earlier field.

---

## Claim 1: "R&D spend should come down over the next two quarters."

Spoken by the CFO in the prepared remarks of a fiscal Q2 call.

![Claim 1 through all four passes. Pass A admits the sentence on the four tests in section 2.2. Pass B runs the falsifiability ladder and lands on UNDERSPECIFIED because the baseline is missing. Pass C resolves seven fields, four of them from the manual rather than the speaker. Observation status is computed as OBSERVABLE. Pass D opens the evidence store, finds the concept in XBRL Company Facts on the first of three sources, and records GAAP-XBRL.](claim-1-passes.png)

### Pass A — is this a claim at all?

Section 2.2 asks four questions, and all four must hold.

| Test | This claim |
|---|---|
| Spoken by company management | Yes, the CFO. An analyst asking the same thing would not qualify |
| About the company's own future | Yes. Not the industry, not a competitor |
| Assertive | Yes. "Should come down" commits to an expectation |
| Not boilerplate | Yes. Not safe-harbour language |

One sentence, one metric, so section 2.4 gives one claim rather than a split. The span is the minimal one carrying the full claim **including its temporal qualifier**, so "over the next two quarters" is inside the span and not trimmed off as context.

Nothing here is a judgment call, which is the point: Pass A is meant to be mechanical and exhaustive. Section 2.3 says to include uncertain cases and flag `borderline: true`, because over-inclusion is recoverable at adjudication and under-inclusion silently corrupts the denominator that every rate in the paper is divided by.

```json
{"claim_id": "2019Q2_EXMPL_0007", "call_id": "2019Q2_EXMPL",
 "speaker_role": "CFO", "section": "PREPARED",
 "char_start": 4193, "char_end": 4248,
 "text": "R&D spend should come down over the next two quarters",
 "conditional": false, "borderline": false,
 "multi_segment_window": false, "prior_knowledge": false}
```

### Pass B — falsifiability, from the text alone

Section 3.2 is a three-question ladder, applied in order. Do not open section 5 while answering it.

**Q1. Does the claim refer to a quantity that varies over time and is reported somewhere in financial disclosure?** Yes. Research and development expense is a line item. Note the question says *any* financial disclosure, not XBRL: whether the store holds it is Pass D's problem, and section 3.2 names mixing the two as the specific error this design exists to prevent.

**Q2. Are metric, direction, evaluation period, and the thing being compared against all recoverable without the registry?** No. The first three are there — R&D expense, downward, the next two quarters — but "come down" from *what*? Management did not say. Down against last quarter and down against the same quarter last year are different claims and can disagree.

**Q3. Is there some assignment of the missing fields under which two analysts would agree on the verdict?** Yes. Fix the baseline and the verdict follows.

So **UNDERSPECIFIED**. Section 3.1 expects most directional guidance to land here, because management rarely states its comparison. Resist the pull toward FALSIFIABLE: section 3.3 closes by warning that a claim needing a default is UNDERSPECIFIED, however reasonable the default seems.

```json
{"falsifiability": "UNDERSPECIFIED"}
```

### Pass C — resolution and provenance

Now section 5 opens. The evidence store does not.

Seven fields, each with a provenance tag recording whether the speaker supplied it or the manual did. Section 4.2 warns that being generous with STATED is how a model ends up looking like it understands language when it has learned the registry.

| Field | Value | Provenance | Governed by |
|---|---|---|---|
| `m.concept` | `us-gaap:ResearchAndDevelopmentExpense` | STATED | management said "R&D spend" |
| `m.scope` | `CONSOLIDATED` | SUPPLIED | section 5.1; no segment or geography named |
| `m.basis` | `UNSPECIFIED` | SUPPLIED | section 5.2 |
| `m.transform` | `NONE` | SUPPLIED | section 5.3; no margin, growth rate or scaling implied |
| `d` | `DECREASE` | STATED | section 5.6 maps "come down" to DECREASE |
| `w` | `[1, 2]` | EXPLICIT | section 5.5; "the next two quarters" is stated outright |
| `b` | same quarter prior year | POLICY_DEFAULT | section 5.4; R&D expense is a flow, and `metric_classes.csv` says so |
| `tau` | `null` | — | directional claim, no threshold |

Two of these are worth pausing on.

**`m.basis` is recorded as `UNSPECIFIED`, not `GAAP`.** Section 5.2 does map unspecified to GAAP, but that mapping happens at adjudication. Writing GAAP here would hide the fact that management never said it, and the provenance statistics exist precisely to show what the defaults cost.

**`b` comes from `metric_classes.csv`, not from judgment.** Section 5.4 dispatches on whether the metric is a flow or a level. R&D expense is a flow, so the default baseline is the same quarter a year earlier. Had it been a level — inventory, cash, headcount — the default would be the immediately prior quarter. A metric absent from that file makes the field UNRESOLVED and goes in `policy_gaps.md`; you do not invent a class for it.

```json
{
  "m": {"concept": "us-gaap:ResearchAndDevelopmentExpense",
        "scope": "CONSOLIDATED", "basis": "UNSPECIFIED", "transform": "NONE"},
  "b": "same quarter prior year", "b_context_ref": null,
  "w": [1, 2], "w_context_ref": null,
  "d": "DECREASE", "tau": null,
  "provenance": {
    "m.concept": "STATED", "m.scope": "SUPPLIED",
    "m.basis": "SUPPLIED", "m.transform": "SUPPLIED", "d": "STATED",
    "b": "POLICY_DEFAULT", "w": "EXPLICIT"
  }
}
```

Four fields of seven came from the manual rather than the speaker, and the record now says so.

### Computed — observation status

**You do not annotate this.** Section 6 assigns it by script after Pass C, and the reason is circularity.

The window is `[t+1, t+2]`, so it spans two fiscal quarters after the call. The script asks which periodic reports cover them and when those reports were actually filed with the SEC. The later of those two filing dates is the claim's evidence maturity date. If both the window has closed and those filings exist by the cutoff `T`, the claim is OBSERVABLE.

Note what that test does **not** consult: whether the R&D figure exists. Section 6 explains why defining observability on the adjudicating fact would be circular — a claim whose evidence turns out to be ABSENT has no such fact to date at all. Observability cannot be decided by first locating the evidence whose existence it gates.

Filing dates are real EDGAR dates from `filing_dates.csv`, not statutory deadlines. Both quarters here filed well before the cutoff.

```json
{"observation_status": "OBSERVABLE", "delinquent_filer": false}
```

### Pass D — evidence availability

Only now does the store open, and only for claims marked OBSERVABLE.

Section 7 says to resolve the unspecified basis first: search for the GAAP measure. The Pass C record keeps `UNSPECIFIED`, so the provenance statistics still show what the default cost; only this search treats it as GAAP.

Then the bounded search, in order, stopping at the first hit:

1. **XBRL Company Facts for that filer and period.** `us-gaap:ResearchAndDevelopmentExpense` is there for both quarters of the window. Stop.

```json
{"evidence_availability": "GAAP-XBRL",
 "evidence_sources_checked": ["xbrl_company_facts"],
 "evidence_note": null}
```

Had it not been in XBRL, the search would have continued to the 10-Q text and then the earnings release, and stopped at `ABSENT` only after all three. Section 7 forbids going further — no investor decks, no company website, no third-party sources — because an unbounded search cannot be replicated by another annotator, and reproducibility of the label matters more than finding the number.

The one error section 7 singles out is substituting a near neighbour. If this claim had resolved to *adjusted* R&D for one segment and the store held only consolidated GAAP R&D, the answer would be `NON-GAAP-ONLY`, not `GAAP-XBRL`. Judge availability against what was resolved. Inflating coverage here corrupts the number the whole decision gate runs on.

---

## Claim 2: "We think we are building something durable here."

Same call, CEO, in the Q&A.

![Claim 2 through all four passes. Pass A admits it, because aspirational statements are filtered by Pass B rather than dropped. Q1 of the falsifiability ladder fails, since durability is not a reported quantity, so the label is UNFALSIFIABLE and Q2 and Q3 are never reached. Nothing resolves in Pass C, observation status is NOT_APPLICABLE, and the evidence store is never opened. The claim still counts in the denominator.](claim-2-passes.png)

**Pass A: include it.** Section 2.3 is explicit that aspirational statements are included and labelled in Pass B. Excluding it at Pass A would quietly shrink the denominator and inflate every rate computed from it.

**Pass B: Q1 fails.** "Durable" is not a quantity that varies over time and is reported in financial disclosure. No further questions. **UNFALSIFIABLE**.

**Pass C: nothing to resolve.** No metric, no direction, no window.

**Computed: not reached.** Unfalsifiable claims are excluded on the label alone.

**Pass D: not reached.** The store is never opened for it.

```json
{"claim_id": "2019Q2_EXMPL_0011", "speaker_role": "CEO", "section": "QA",
 "text": "we think we are building something durable here",
 "falsifiability": "UNFALSIFIABLE",
 "observation_status": "NOT_APPLICABLE",
 "evidence_availability": "N/A"}
```

This claim costs a minute and produces no label beyond the first. It is not wasted work: the rate at which management produces unfalsifiable statements is one of the things the pilot reports, and that rate has no meaning unless these are counted.

---

## What to carry into your first passage

**The order is the method.** If you find yourself wanting to check a number during Pass B, that is the design working. Write the label from the text and move on.

**Provenance is not bookkeeping.** Four of Claim 1's seven fields came from the registry. The paper reports results split by provenance, so a field tagged STATED when the manual supplied it moves a number in the results.

**Count everything you find.** Both claims above go in the record. The denominator is as much a deliverable as any label, and section 10 says getting it right matters as much as any other decision here.

**When the manual does not cover it, say so.** Mark the field UNRESOLVED and log it in `annotations/policy_gaps.md`. The gap log is a pilot output, not an admission of failure: it is what tells the next version of the guidelines what to fix.

---

The rules are in [`annotation-guidelines.md`](annotation-guidelines.md). The passes and why they are ordered this way are in [annotation](annotation.md). Five claims shown as input and output rather than pass by pass are in [worked examples](../worked-examples/worked-examples.md).
