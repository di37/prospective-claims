# reference

Frozen companion tables the annotation manual depends on. Unlike `data/`, these **are** committed: they are small, they are version-locked to the manual, and changing one changes what an annotation means.

| File | Used by | Contents |
|---|---|---|
| `metric_classes.csv` | manual section 5.4 | metric -> FLOW or LEVEL, which selects the default baseline. **Present**, 49 rows. |
| `fiscal_calendar.csv` | manual section 5.5 | cik -> fiscal year end, 52/53-week flag |
| `filing_dates.csv` | manual section 6 | cik, fiscal_period, form_type, filed_date |
| `evidence_cutoff.txt` | manual section 6 | the single cutoff date T |

`filing_dates.csv` is what makes the evidence maturity date computable. The fiscal calendar maps "next quarter" onto a period; it cannot say when the report covering that period was filed. Take the first filing covering a period, not an amendment.

Rebuild with:

```bash
python scripts/01_build_reference_tables.py
```

Authored source is `src/reference/metrics.py`. The script verifies every taxonomy element against the SEC frames API at three points across the study window, 2012, 2018 and 2024, and exits non-zero if one exists in no period. `metric_classes.provenance.json` records the commit it ran from, when it was last proved, and filer counts per element per period.

Probing more than one period is what surfaces the ASC 606 transition. `ContractWithCustomerLiabilityCurrent` does not exist in 2012 and `DeferredRevenueCurrent` is being retired, so neither spans the window and the two together do. A single-period check would report whichever one it sampled as universally available.

## metric_classes.csv

Columns: `metric`, `class`, `taxonomy_element`, `in_evidence_store`, `window_coverage`, `ambiguous`, `note`.

`window_coverage` is `full` when the metric can be retrieved across 2012 to 2024, `partial` when it cannot, and `n/a` when the metric is outside the evidence store. Where `taxonomy_element` separates names with `|` they are alternatives to try in turn, not components to combine, and coverage is their union.

`class` is FLOW or LEVEL and nothing else, because section 5.4 dispatches on exactly those two. Flows are measured over a period and default to the same quarter a year earlier; levels are measured at a point in time and default to the immediately prior quarter.

The 8 rows with `in_evidence_store: no` still carry a class, because the baseline default applies whether or not XBRL holds the metric. Falsifiability and evidence availability are separate axes, and this table speaks only to the first.

10 rows are marked `ambiguous: yes`, each with a justification rather than a silent decision. Three are worth knowing before annotating:

- **Margins** are ratios of two flows, classed FLOW and compared year over year. Sequential comparison is defensible for a non-seasonal filer. Year over year is correct for seasonal filers and merely conservative for the rest, which is why it wins.
- **Days sales outstanding and inventory turns** put a level over a flow. Both are classed LEVEL because management discusses working-capital efficiency sequentially, but the flow denominator makes the other reading arguable.
- **Shares** are two rows on purpose. `shares_outstanding` is a count at a point in time and is LEVEL; `weighted_average_shares` is averaged over a period and is FLOW. A claim about buyback impact usually means the second.

One metric is `partial`: `remaining_performance_obligation`. ASC 606 created the concept and there is no pre-606 equivalent, so claims about it before roughly 2018 cannot be settled however good retrieval is.

Sparse elements are a separate problem from absent ones. `us-gaap:DebtCurrent` is tagged by a few hundred filers, so `short_term_debt` will often find nothing even inside its covered window. Expect the gap rather than treating it as an error.

A metric absent from this file makes the baseline field `UNRESOLVED` and goes in `annotations/policy_gaps.md`. Do not add a row mid-pilot to make a claim resolvable; log the gap and let the next version decide.

Changing any file here is a version bump on the annotation guidelines and requires a change-log entry.
