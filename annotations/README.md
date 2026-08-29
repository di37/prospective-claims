# annotations

Output of the annotation passes. One record per claim per annotator, so agreement can be computed on independent judgments.

| File | Contents |
|---|---|
| `passages.jsonl` | Sampled passages with sector, fiscal year, exhaustive claim count, and annotation minutes |
| `claims.jsonl` | One record per claim per annotator, accumulating across passes |
| `policy_gaps.md` | Cases the policy registry does not cover. A deliverable, not a scratchpad |

`passages.jsonl` carries the denominator. Claims are drawn from exhaustively annotated passages rather than found with a keyword search, so the coverage ratio describes the real population rather than whatever a regex happened to match.

Agreement is computed on the independent labels before any adjudication, and those are the numbers reported. Do not recompute them after disagreements are resolved.
