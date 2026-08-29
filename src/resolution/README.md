# src/resolution

Turns a forward-looking claim into a structured proposition.

```
resolve(claim, t) -> (m, b, w, d, tau)
```

where `m` is itself four fields: concept, scope, accounting basis, and transform. A single metric label cannot express "adjusted operating margin in North America on a constant-currency basis", and the accounting basis is what predicts whether the claim is checkable at all.

Every resolved field carries a provenance tag recording whether it came from the speaker or from the annotation policy. Results are reported stratified by provenance, because a model that scores well only where the policy supplied the answer has learned the manual rather than the language.

An unstated evaluation window resolves to UNRESOLVED. It is never defaulted to next quarter: window inference is one of the study's contributions, and defaulting it would manufacture easy labels for the exact capability under test.
