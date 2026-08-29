# reference

Frozen companion tables the annotation manual depends on. Unlike `data/`, these **are** committed: they are small, they are version-locked to the manual, and changing one changes what an annotation means.

| File | Used by | Contents |
|---|---|---|
| `metric_classes.csv` | manual section 5.4 | metric -> FLOW or LEVEL, which selects the default baseline |
| `fiscal_calendar.csv` | manual section 5.5 | cik -> fiscal year end, 52/53-week flag |
| `filing_dates.csv` | manual section 6 | cik, fiscal_period, form_type, filed_date |
| `evidence_cutoff.txt` | manual section 6 | the single cutoff date T |

`filing_dates.csv` is what makes the evidence maturity date computable. The fiscal calendar maps "next quarter" onto a period; it cannot say when the report covering that period was filed. Take the first filing covering a period, not an amendment.

Changing any file here is a version bump on the annotation guidelines and requires a change-log entry.
