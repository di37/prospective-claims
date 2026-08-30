# Annotation

Four passes over the claims, each completed across all of them before the next begins. The order is part of the design rather than a workflow convenience.

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

---

The rules themselves are in [`annotation-guidelines.md`](annotation-guidelines.md), which is frozen and versioned. This page is the shape; that document is the manual.
