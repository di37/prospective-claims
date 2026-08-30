# The task

What the system is asked to do with a forward-looking claim, and the label that decides whether it is worth asking.

<!-- task-pipeline.png is parked, not linked: it routes "Window resolved? -> No" into
     UNFALSIFIABLE and has no NOT_APPLICABLE node, which reverses the fix made in 5d7ac24.
     Swap the Mermaid below for the image once that branch is added. -->
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

## Falsifiability

![The falsifiability decision tree. Q1 asks whether the claim refers to a quantity reported in any financial disclosure, Q2 whether metric, direction, period and comparison basis are all recoverable from the text, and Q3 whether any assignment of the missing fields would let two analysts agree. The answers give FALSIFIABLE, UNDERSPECIFIED or UNFALSIFIABLE, with five labelled example statements.](falsifiability.png)

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

---

Next: [how humans annotate this](../annotation/annotation.md), or [five claims worked end to end](../worked-examples/worked-examples.md).
