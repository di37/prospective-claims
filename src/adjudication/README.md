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

| Module | Owns |
|---|---|
| `observation/models.py` | The vocabulary and the records that carry it |
| `observation/covering.py` | Which filing covers a period, and whether a missing one is overdue |
| `observation/status.py` | The rule from section 6 |
| `observation/reporting.py` | The censoring rate, split by reason |

`observe()` takes no evidence argument at all. That is the design rather than an omission: a claim whose figure turns out to be absent has no fact whose publication date could be inspected, so a status that consulted the evidence could not be assigned to the claims that need it most.

Censoring is reported by reason rather than as one number, because the three reasons say different things. An immature window is a property of the study's cutoff and would resolve itself given time. A filing that has not arrived is a property of this filer's promptness. A delinquent filer is a property the study treats as its own case, since the report may never arrive at all.

The window arrives as concrete period ends rather than as offsets from the claim quarter, which keeps the unsettled question of what `t` denotes in `src/resolution` where it belongs.

Checked against the reference tables as well as against synthetic ones: 6,735 two-quarter windows placed across every real fiscal calendar in `fiscal_quarters.csv`, adjudicated against the real filing dates. Observable counts rise monotonically with the cutoff, from 1,380 at mid-2015 to 6,735 by 2026, and the 104 censored at a 2024 year-end cutoff all carry a maturity date rather than a missing filing, the latest being a fourth-quarter annual report filed in March 2025.
