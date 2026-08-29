# src/adjudication

Decides whether a resolved claim was supported, refuted, or cannot be checked.

Order matters and is fixed. Observability is determined before any evidence is inspected:

```
M(c) = max{ filing dates of the reports covering the claim's window }

OBSERVABLE      window closed AND M(c) <= cutoff T
RIGHT_CENSORED  otherwise
```

`M(c)` depends on the filer's reporting calendar, never on whether a particular fact exists. Deciding observability by first locating the adjudicating fact would be circular, since a claim whose evidence turns out to be absent has no such fact to date.

Only then is evidence availability checked, and only for OBSERVABLE claims. Anything outside the evidence store is NOT_ENOUGH_EVIDENCE, which means insufficient evidence in the designated store rather than evidence that does not exist.
