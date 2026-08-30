# src/edgar

Everything in the study that talks to the SEC. One User-Agent, one rate limit, one retry policy, set here rather than at each call site, because the SEC identifies clients by that header and blocks on it.

| Module | Answers |
|---|---|
| `transport.py` | The shared HTTP layer. A 404 is a result, not a failure, so callers can tell a missing element from a timeout |
| `frames.py` | Does this element exist, and what did every filer report for it in one period |
| `submissions.py` | What has this filer filed, and when |
| `facts.py` | What did this one filer report for one concept, when the frame has no row for it |

The frames API is the cheap path: one request covers every filer. `facts.py` exists for the gaps, since a company whose year end sits away from a frame's instant has no row in it even though the fact exists. Reach for the per-filer endpoint only when the frame has already been tried.

Two rules the study depends on are enforced here rather than left to callers. Filing dates take the first filing covering a period, never an amendment, because a 10-Q/A published after the evidence cutoff does not make a claim observable while the original that arrived on time does. XBRL facts keep the as-first-reported value rather than the current value of a concept, because a restatement is information that did not exist when the claim was made.

Fiscal calendars are still to come, including non-standard year ends and 52- and 53-week retail years. That work is unglamorous and is a real source of label noise, which is why it belongs in its own module with its own tests rather than being inlined wherever a quarter needs resolving.

No key is needed for any of this. The full Company Facts client, which pulls every concept a filer has ever tagged, is separate work.
