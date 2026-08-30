# Pilot and decision gate

What 250 annotated claims decide, and the rule written before the numbers arrive.

Two annotators, drawn from exhaustively annotated passages so the denominator is unbiased.

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

---

The measure the gate turns on depends on the sources in [data](data.md) and the labels in [annotation](annotation.md).
