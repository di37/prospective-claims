# reference

Frozen companion tables the [annotation guidelines](../docs/annotation-guidelines.md) depend on. Unlike `data/`, these **are** committed: they are small, they are version-locked to the manual, and changing one changes what an annotation means.

| File | Used by | Contents |
|---|---|---|
| `metric_classes.csv` | [section 5.4](../docs/annotation-guidelines.md#54-baseline) | metric -> FLOW or LEVEL, which selects the default baseline. **Present**, 49 rows. |
| `filers.csv` | every table below | the 150 study filers and the CIKs everything joins on. **Present**, 150 rows. |
| `filing_dates.csv` | [section 6](../docs/annotation-guidelines.md#6-observation-status-computed-not-annotated) | cik, fiscal_period, form_type, filed_date. **Present**, 7,118 rows. |
| `fiscal_calendar.csv` | [section 5.5](../docs/annotation-guidelines.md#55-window) | cik -> fiscal year end, 52/53-week flag. **Present**, 150 rows. |
| `fiscal_quarters.csv` | [section 5.5](../docs/annotation-guidelines.md#55-window) | cik, fiscal year, quarter -> period end. **Present**, 7,030 rows. |
| `transcript_coverage.csv` | the sampling frame | corpus symbol -> quarters covered, and which study filer it is. **Present**, 685 rows. |
| `evidence_cutoff.txt` | [section 6](../docs/annotation-guidelines.md#6-observation-status-computed-not-annotated) | the single cutoff date T |

`filing_dates.csv` is what makes the evidence maturity date computable. The fiscal calendar maps "next quarter" onto a period; it cannot say when the report covering that period was filed. Take the first filing covering a period, not an amendment.

Rebuild in order, because 03 and 04 join on the CIKs that 02 writes:

```bash
python scripts/01_build_metric_classes.py
python scripts/02_select_filers.py
python scripts/03_build_filing_dates.py
python scripts/04_build_fiscal_calendar.py
python scripts/00_pull_transcripts.py        # about 1.2 GB, run once
python scripts/05_build_transcript_inventory.py
```

Only 04 and 05 are offline. It derives the calendars from the filing dates 03 already pulled, so it changes only when they do.

Every table has a `.provenance.json` beside it recording the commit it was built from, when, and the rules that were in force. Every table has a notebook in `notebooks/` that reads it and says what it is fit for.

## metric_classes.csv

Authored source is `src/reference/metrics.py`. The script verifies every taxonomy element against the SEC frames API at three points across the study window, 2012, 2018 and 2024, and exits non-zero if one exists in no period. `metric_classes.provenance.json` records the commit it ran from, when it was last proved, and filer counts per element per period.

Probing more than one period is what surfaces the ASC 606 transition. `ContractWithCustomerLiabilityCurrent` does not exist in 2012 and `DeferredRevenueCurrent` is being retired, so neither spans the window and the two together do. A single-period check would report whichever one it sampled as universally available.

Columns: `metric`, `class`, `taxonomy_element`, `in_evidence_store`, `window_coverage`, `ambiguous`, `note`.

`window_coverage` is `full` when the metric can be retrieved across 2012 to 2024, `partial` when it cannot, and `n/a` when the metric is outside the evidence store. Where `taxonomy_element` separates names with `|` they are alternatives to try in turn, not components to combine, and coverage is their union.

`class` is FLOW or LEVEL and nothing else, because [section 5.4](../docs/annotation-guidelines.md#54-baseline) dispatches on exactly those two. Flows are measured over a period and default to the same quarter a year earlier; levels are measured at a point in time and default to the immediately prior quarter.

The 8 rows with `in_evidence_store: no` still carry a class, because the baseline default applies whether or not XBRL holds the metric. Falsifiability and evidence availability are separate axes, and this table speaks only to the first.

10 rows are marked `ambiguous: yes`, each with a justification rather than a silent decision. Three are worth knowing before annotating:

- **Margins** are ratios of two flows, classed FLOW and compared year over year. Sequential comparison is defensible for a non-seasonal filer. Year over year is correct for seasonal filers and merely conservative for the rest, which is why it wins.
- **Days sales outstanding and inventory turns** put a level over a flow. Both are classed LEVEL because management discusses working-capital efficiency sequentially, but the flow denominator makes the other reading arguable.
- **Shares** are two rows on purpose. `shares_outstanding` is a count at a point in time and is LEVEL; `weighted_average_shares` is averaged over a period and is FLOW. A claim about buyback impact usually means the second.

One metric is `partial`: `remaining_performance_obligation`. ASC 606 created the concept and there is no pre-606 equivalent, so claims about it before roughly 2018 cannot be settled however good retrieval is.

Sparse elements are a separate problem from absent ones. `us-gaap:DebtCurrent` is tagged by a few hundred filers, so `short_term_debt` will often find nothing even inside its covered window. Expect the gap rather than treating it as an error.

A metric absent from this file makes the baseline field `UNRESOLVED` and goes in `annotations/policy_gaps.md`. Do not add a row mid-pilot to make a claim resolvable; log the gap and let the next version decide.

## filers.csv

Columns: `cik`, `name`, `location`, `revenue`, `assets`, `revenue_to_assets`, `rank`, `source_element`.

Filers are ranked by annual revenue from the SEC frames API at CY2023, restricted to US locations, largest 150. A filer reporting under both revenue elements is counted once at the larger figure, because the two overlap during the ASC 606 transition and adding them would double-count. Authored source is `src/reference/filers.py`.

Candidates are screened on revenue over total assets before the ranking is taken, because the frames API serves whatever a filer tagged. A candidate above 25 times its assets is excluded rather than flagged: an implausible revenue figure does not make a filer suspect, it makes its rank fabricated, and the rule is the largest filers by revenue. One candidate fails, Tigo Energy, which tagged CY2023 revenue as 145,233,000,000 against total assets of 127,777,000 and would have ranked 25th on it. Every exclusion is named in the provenance record with the figures that caused it.

The threshold comes from the data. Across the top 300 candidates the median ratio is 0.70 and the largest genuine reading is 6.5, for a fuel distributor; the next value up is Tigo at 1,137, with nothing between. 25 is four times the largest real observation and still low enough that a thousand-fold error on an asset-heavy filer, whose true ratio is near 0.05, would trip it.

Two selected filers have no assets figure to screen against and are kept, because absence of a balance sheet to check is not evidence of an error. Their CIKs are in the provenance.

Two limitations remain, both visible in `notebooks/02_filers.ipynb` and neither fixed.

Twelve slots go to six corporate families: Charter with CCO Holdings, Plains All American with Plains GP, PBF Energy with PBF Holding, Paramount Global with Paramount Skydance, MetLife with Metropolitan Life, Berkshire Hathaway with Berkshire Hathaway Energy. The dedupe is per CIK and cannot see one business filing under two. Most are debt-issuing subsidiaries that hold no earnings call, so the transcript intersection removes them; Paramount needs a decision, because a successor entity can inherit the call series.

Goldman Sachs, Morgan Stanley, Wells Fargo and Truist tag neither revenue element, so no cutoff admits them. Financial-sector coverage here is set by tagging practice rather than by size.

Join on `cik` and never on `name`. U.S. Bancorp files as `US BANCORP \DE\`.

## filing_dates.csv

Columns: `cik`, `fiscal_period`, `form_type`, `filed_date`, `lag_days`, `suspect`, `accession`.

One row per 10-K or 10-Q covering a period that ends between 2012 and 2024. Amendments are excluded at extraction rather than filtered later, and where a period was filed more than once the earliest filing wins.

`lag_days` is filing date minus period end, and it is the reason the table exists: the median 10-Q arrives 32 days after its period closes and the median 10-K 50 days, so a window can close weeks before the report covering it exists. Computing observability from period end would mark claims answerable before the evidence was published.

`suspect` is empty for good rows and names the problem otherwise. 10 of 7,118 rows are flagged: 6 `lag_implausibly_short` and 4 `lag_long`. EDGAR's `reportDate` is wrong for a small share of filings, and since `fiscal_period` is what adjudication joins on, a wrong period matches a claim to the wrong filing. These are flagged rather than dropped, because a long lag may be genuine delinquency, which the study treats as its own case.

The short threshold is 5 days, set from the observed distribution rather than assumed. Lags of 0 to 3 days are impossible; nothing appears again until 9 days, after which Delta and Oracle form a coherent cluster at 10 to 14 days because they genuinely file that fast. A threshold of 15 would have flagged 51 rows, 40 of them from those two filers alone.

119 of 150 filers span the full window and two have no filings in it at all. Drop those two before sampling.

## fiscal_calendar.csv and fiscal_quarters.csv

`fiscal_calendar.csv` columns: `cik`, `name`, `calendar_type`, `declared_year_end`, `year_end_month`, `year_end_day`, `year_end_weekday`, `year_end_changed`, `changed_at`, `earlier_calendar_type`, `annual_anchors`, `fiscal_years`, `suspect_anchors`, `missing_fiscal_years`. One row per filer.

`fiscal_quarters.csv` columns: `cik`, `fiscal_year`, `quarter`, `period_end`, `form_type`, `days_from_year_start`. One row per observed fiscal period. Quarter 4 is the annual period end, since the 10-K covers it rather than a fourth 10-Q.

Both are derived from `filing_dates.csv` rather than fetched. Every 10-K period end is an annual anchor and the 10-Q period ends between consecutive anchors are that year's quarters. Authored source is `src/reference/calendar.py`.

EDGAR's `fiscalYearEnd` is not enough on its own, which is why the calendar is derived. It holds one value per filer, so for a 52/53-week filer it names whichever date the most recent year happened to land on, and for a filer that changed its year end it names only where it ended up. Every one of the 27 week-based filers takes seven distinct year-end dates across the window.

Two shapes account for all but five filers. A fixed-date year end lands on the same calendar date, so consecutive years are 365 or 366 days apart: 118 filers. A 52/53-week year ends on the same weekday and inserts a 53rd week roughly every six years, so consecutive years are 364 or 371 days apart: 27 filers. The gap sets do not overlap, which is what makes the classification decidable. Five filers have fewer than three annual anchors and are `insufficient_data` rather than guessed at.

Three filers changed year end inside the window and are listed with the date and both regimes. Deere ran a fixed 31 October year end through fiscal 2016 then moved to the Sunday nearest the end of October; Archer-Daniels-Midland moved from June to December in 2012; Best Buy from March to the Saturday nearest 31 January in 2013. The shape reported is the one in force after the change, with the earlier one beside it.

The derivation is also a second filter on bad period ends. Publix files every year end on a Saturday except 31 December 2013, and Paramount files every year end on 31 December except 21 December 2012. Both lags are plausible, so `filing_dates.csv` could not flag them; both disagree with their neighbours here. They are recorded in `suspect_anchors` rather than dropped. Two filers are missing an annual anchor outright: General Electric for fiscal 2014, whose 10-K was excluded upstream as suspect, and Best Buy for fiscal 2013, which was an eleven-month transition period.

`fiscal_year` is the calendar year the fiscal year ends in. That is a convention, not the filer's own name for the year: Walmart calls the year ending January 2024 fiscal 2024 while Target calls the year ending January 2023 fiscal 2022, so no single rule matches both. **Join on `period_end`, never on `fiscal_year`.**

74 quarters carry no label because they sit after their filer's last annual report and belong to a fiscal year the window never closes. Four more sit in the gaps left by the two missing anchors.

## transcript_coverage.csv

Columns: `symbol`, `company_name`, `cik`, `filer_name`, `match_method`, `first_period`, `last_period`, `quarters_present`, `quarters_expected`, `gaps`, `continuous`, `calls_split`, `calls_unsplit`, `calls_low_confidence`. One row per symbol in the transcript corpus, 685 of them, with `cik` filled for the 121 that are study filers.

This is the sampling frame. A filer with immaculate filing coverage and no transcript contributes no claims, so this table and not `filers.csv` decides what the pilot can draw from.

The join it records is the fragile part. The corpus is keyed by ticker and the study by CIK, and a ticker is not stable over thirteen years. Exxon Mobil is the case that proves it: the study holds CIK 34088 from a 2023 revenue frame, the SEC's current ticker file maps XOM to a later holding entity, and 34088 carries no ticker at all, so joining on the public ticker file would have dropped the seventh largest filer in the study. Matching therefore runs on tickers from each filer's own submissions record, with three aliases checked one at a time against the corpus's company names. Nothing is fuzzy matched: an earlier attempt mapped Metropolitan Life onto 3M and Flex onto F5 Networks.

29 study filers have no transcript. Five are not listed and hold no public call, which the filer notebook predicted. 24 are listed and simply absent from a corpus that carries 685 tickers rather than a full index history.

86 of the 121 cover every quarter of 2012 to 2024, against a design that assumes 120 to 150. 106 have no interior gap, so most of the shortfall is companies that listed after 2012 or were acquired before 2024 rather than ragged coverage. Relaxing to at most four missing quarters gives 100 filers, as does shortening the window to 2016, but not the same 100. The table carries quarters and gaps per filer so the threshold stays a study decision rather than being baked in here.

`calls_split`, `calls_unsplit` and `calls_low_confidence` count how the prepared-remarks and Q&A boundary went for that symbol. The offsets themselves are in `data/interim/transcript_segments.parquet`, which is not committed. Offsets rather than text, because the transcripts are third-party content this project does not redistribute.

Changing any file here is a version bump on the annotation guidelines and requires a change-log entry.
