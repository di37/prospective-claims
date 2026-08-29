# data/processed

The splits every experiment reads. Written once, by the preparation script, and not re-split anywhere else.

The primary split is temporal, which is also the deployment setting: a system reads a claim today and adjudicates it later.

```
train  2012-2020
dev    2021-2022
test   2023-2024
```

A firm-disjoint split is reported alongside as a robustness check. Splits are frozen before annotation begins, and the construction script is committed so they can be rebuilt exactly.
