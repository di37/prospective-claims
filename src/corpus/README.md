# src/corpus

The earnings-call transcript corpus: what it covers, which filer each symbol is, and where a call divides.

| Module | Answers |
|---|---|
| `coverage.py` | Which quarters a symbol is covered for, and where the gaps are |
| `bridge.py` | Which study filer a corpus symbol is, and on what evidence |
| `segments.py` | Where prepared remarks end and the analyst Q&A begins |

Every other part of this project describes filings. This package describes the other side of the task, the calls the claims are made on, and its output decides what the pilot can sample: a filer with immaculate filing coverage and no transcript contributes nothing.

Nothing here writes transcript text to a file. The segmentation is a character offset into the source row, which rebuilds the segment exactly and carries no licensed text with it. That is the same rule the project applies to any released artifact, and it is enforced here rather than remembered later.

`bridge.py` is the part to read before trusting a number. Joining a ticker-keyed corpus to a CIK-keyed study set is not mechanical: a ticker moves when a company reorganises, is reassigned after a delisting, and is absent entirely for a company that went private. The module matches on tickers from each filer's own EDGAR submissions record, falls back to a short list of aliases checked one at a time, and reports everything else as unmatched with the reason. It does not guess, because a wrong match is worse than a missing filer: a missing filer is a smaller sample, a wrong match adjudicates one company's claims against another's filings.
