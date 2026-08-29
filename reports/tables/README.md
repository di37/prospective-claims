# reports/tables

Results tables, one CSV per output, written only through `common.write_table`.

The writer adds the calling script's prefix and refuses a filename that already contains one, so a double-prefixed file cannot be produced by accident.

Notebooks read these and write none. A table written from a notebook has no producing script, so it cannot be regenerated and it fails the prefix check.
