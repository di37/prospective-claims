# Data

Where the data comes from, what it costs, and the four properties of it that shaped the design.

All real, all public. Nothing synthetic.

| Data | Source | Cost | Status |
|---|---|---|---|
| Earnings call transcripts | `RudrakshNanavaty/earnings-call-data` (HuggingFace) — 33,362 calls, 2005–2025, 685 tickers across 496 companies | Free | Pulled, inventoried |
| Financial facts | SEC Company Facts, `data.sec.gov` | Free, no API key | Verified, not yet pulled |
| Filing dates | SEC EDGAR submissions API | Free, no API key | Verified, not yet pulled |
| Earnings-miss labels | Alpha Vantage `EARNINGS` endpoint — reported and estimated EPS, surprise, surprise percentage | Paid tier | Verified, needed only for the downstream task |

Study window 2012–2024, 120–150 large-cap filers.

Four properties of the data shape the design, and each one closed off an easier version of the project.

**Structured financial data does not reach back to 2005.** XBRL tagging was phased in for periods ending on or after June 2009 for the largest filers, June 2010 for other large accelerated filers, and June 2011 for everyone else. Transcripts run from 2005, but adjudication cannot start until roughly 2011, which is why the window begins in 2012.

**Non-GAAP measures are absent from the structured data.** A great deal of guidance is issued on adjusted EBITDA, non-GAAP margins, or constant-currency revenue, and companies routinely decline to reconcile forward-looking non-GAAP figures to GAAP. None of those exist as XBRL facts, so some of the most specific-sounding claims in the corpus are the least checkable. How much of the corpus this removes is exactly what the pilot measures.

**Filed values get revised.** Company Facts serves the current value of a concept, including restatements. The adjudicator uses as-first-reported values, because a restatement issued later would leak information that was not available when the claim was made.

**Fiscal calendars do not align.** Non-standard year ends, 52- and 53-week retail calendars, and "next year" meaning a fiscal year ending the following January. This is unglamorous work and a real source of label noise, so it gets its own module and its own tests.

**The corpus is narrower than the study set.** 121 of the 150 filers have transcripts in it. Five hold no public earnings call at all, being employee-owned, debt-issuing subsidiaries, or subsidiaries of a listed parent. The other 24 are listed companies the corpus does not carry, four of them S&P 500 members, so this is a 685-ticker subset rather than a complete index history. 86 of the 121 cover every quarter of the window, against a design that assumes 120 to 150. See [`notebooks/05_transcripts.ipynb`](../notebooks/05_transcripts.ipynb).

Transcripts are owned by their providers, so a released dataset carries claim spans, character offsets, resolutions, and labels, plus a script that reconstructs the text from its source. That constraint is a design input, not something to resolve later.

The licence chain supports that caution rather than relieving it. The release is tagged MIT, so are the two HuggingFace datasets beneath it, and none of the three names the vendor the transcripts originally came from; some transcripts still carry a `TRANSCRIPT SPONSOR` line, and one card tags MIT while also saying "for research and educational use only", which MIT does not say. A tag applied by an uploader does not grant rights the uploader does not hold, so the text is pulled, never committed, and never redistributed.

---

What the data can and cannot settle is measured by [the pilot](pilot/pilot.md). The tables built from it are described in [`reference/README.md`](../reference/README.md).
