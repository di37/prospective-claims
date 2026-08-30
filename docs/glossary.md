# Glossary

Finance and filing terms used across this project, for readers coming from outside finance.

| Term | What it means |
|---|---|
| **8-K** | A filing for events between scheduled reports. The earnings press release is usually an attachment to one. |
| **10-Q / 10-K** | The quarterly and annual reports a US public company must file. |
| **Adjudication** | Deciding whether a claim turned out to be supported or refuted, once the evidence exists. Borrowed from law, where it means settling a disputed matter; here the dispute is between what management predicted and what the filings later showed. It is the second half of the pipeline: resolution turns the sentence into something checkable, adjudication does the checking. |
| **ARR** | ACL Rolling Review, the shared reviewing system for the main natural language processing conferences. |
| **As-first-reported** | The value as originally filed, before any later restatement. Using restated values would leak information that was not available at the time. |
| **CIK** | The SEC's unique identifier for a filer. |
| **Cohen's kappa** | A measure of agreement between two annotators that corrects for agreement by chance. |
| **Company Facts** | The SEC endpoint serving those tagged values for a given company. |
| **Consensus estimate** | The average of analysts' forecasts for a figure. Beating or missing it is what "earnings surprise" refers to. |
| **Earnings call** | A quarterly conference call where a company's executives discuss results and answer analyst questions. Split into prepared remarks and a Q&A session. |
| **Earnings miss** | Reported results below the consensus estimate. |
| **EBITDA** | Earnings before interest, taxes, depreciation and amortisation. A widely used non-GAAP profitability measure. |
| **EDGAR** | The SEC's public database of those filings. Free, no key required. |
| **EPS** | Earnings per share. Net profit divided by shares outstanding. |
| **Filing date** | When a report actually reached the SEC. Distinct from the period it covers, and often weeks later. |
| **Fiscal quarter** | A company's own accounting quarter. Not necessarily aligned to the calendar; some retailers use 52- or 53-week years. |
| **GAAP** | Generally Accepted Accounting Principles, the standard US rules for how a figure must be calculated. What XBRL tags. |
| **Guidance** | A forward-looking statement by management about expected future performance. |
| **NEI** | Not Enough Information. The standard third label in fact-verification work, alongside supported and refuted. |
| **Non-GAAP** | A company-defined adjustment to a GAAP figure, such as excluding one-off costs. Common in guidance, and not present in XBRL, which is the central constraint on this project. |
| **Resolution** | Turning a claim sentence into a checkable proposition: which metric, measured against what, over which period, moving which way. Happens before any evidence is consulted, and produces nothing but structure. Not to be confused with adjudication, which comes after and produces a verdict. |
| **SEC** | The US Securities and Exchange Commission, the regulator public companies file with. |
| **XBRL** | A tagging standard that makes filed financial statements machine-readable, so "revenue" can be looked up as a labelled field rather than parsed out of a PDF. |

---

Terms specific to the annotation scheme have their own glossary in [`annotation-guidelines.md`](annotation-guidelines.md).
