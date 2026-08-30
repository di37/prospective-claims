# src/resolution

Turns a forward-looking claim into a structured proposition.

```
resolve(claim, t) -> (m, b, w, d, tau)
```

where `m` is itself four fields: concept, scope, accounting basis, and transform. A single metric label cannot express "adjusted operating margin in North America on a constant-currency basis", and the accounting basis is what predicts whether the claim is checkable at all.

Every resolved field carries a provenance tag recording whether it came from the speaker or from the annotation policy. Results are reported stratified by provenance, because a model that scores well only where the policy supplied the answer has learned the manual rather than the language.

An unstated evaluation window resolves to UNRESOLVED. It is never defaulted to next quarter: window inference is one of the study's contributions, and defaulting it would manufacture easy labels for the exact capability under test.

`windows.py` is the only part written so far. It maps a phrase the manual already names onto a window of the filer's own fiscal quarters and then onto concrete period ends. Recognising an arbitrary paraphrase as one of those phrases is the model's job and is RQ1; nothing in this module reads text.

Where `t` sits is a parameter rather than a decision taken there. Section 4.1 calls the window relative to "the claim quarter" in one line and "the quarter of the call" in the next, and for any real earnings call those differ by exactly one, because a call reporting the third quarter is held during the fourth. Both readings are implemented as `Anchor.REPORTED_QUARTER` and `Anchor.CALL_QUARTER`, both are tested, and choosing between them is a change to the manual rather than to this code.
