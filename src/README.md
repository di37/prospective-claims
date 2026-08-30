# src

Importable code with no side effects. Importing anything here must not read a file, write a file, or hit the network.

| Module | Owns |
|---|---|
| `constants.py` | Paths, seeds, the evidence cutoff. Standard library only, so it is cheap to import anywhere |
| `config.py` | Pydantic models for claims and experiment conditions, with validation at construction |
| `common.py` | Loading, seeding, table and figure I/O |
| `run_logging.py` | Console output, log files, and the output-prefix rule |
| `edgar/` | Everything that talks to the SEC: one transport, the frames API, submissions, single concepts |
| `reference/` | Authored definitions behind the generated tables in `reference/` |
| `resolution/` | Claim text to a structured, checkable proposition |
| `adjudication/` | Observation status, evidence lookup, verdicts |

Scripts import from here. Nothing here imports from `scripts/`.

Configs are pydantic models rather than dicts or dataclasses, frozen and with unknown fields forbidden, so a mistyped keyword is an error rather than a silently ignored setting. A condition that has been run is a record of what was run.

Where a module carries both the shapes of a domain and the rules that operate on them, it is a package rather than a file: `models.py` holds what the domain is, and the behaviour sits beside it in modules named for what they do. The split is by responsibility rather than by type, so the shapes stay next to the code that uses them rather than migrating into one shared bag of models. A module with a single class stays a single file, because splitting it would cost cohesion and buy nothing.
