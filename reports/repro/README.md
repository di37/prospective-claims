# reports/repro

The reproduction record. Written by `08_build_repro_artifacts.py` after every experiment script has run.

| File | Contents |
|---|---|
| `study_metadata.json` | Seeds, interpreter and platform, versions of the packages that affect results |
| `artifact_inventory.csv` | Every table and figure, with the script that produced it and its size |

The inventory reads the producing script from each artifact's filename prefix, which is why the writers enforce it. Together these answer the two questions a later reader has: can I rebuild this, and did this committed figure come from the current code.
