# src/reference

The authored source behind the generated tables in `reference/`. Nothing here reads a file or hits the network; the scripts do that and call in.

| Module | Owns |
|---|---|
| `metrics.py` | The 49 metric definitions, their FLOW or LEVEL class, and the taxonomy elements each resolves to |
| `filers.py` | The rule that decides who is in the study, and the plausibility screen that keeps a tagging error out of it |
| `calendar.py` | Fiscal year shapes, derived from the period ends filers actually filed |

The split between this package and `reference/` is the point of both. What is authored or decided lives here, in code, validated at import and reviewable in a diff. What is derived lives in the CSVs, regenerable and never edited by hand. A row that appears in a table but in no module here is a row someone typed, which is the failure this arrangement exists to prevent.

Each module carries its own limitations in its docstring rather than in a comment at the call site, because the limitation belongs to the rule and travels with it.
