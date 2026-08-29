# reports/logs

One timestamped log per script run, written by `run_logging.tee_to_logfile`, which mirrors stdout and stderr to a file.

Not committed. The timestamp is the only nondeterministic value a script produces, which is why it lives in a filename here rather than anywhere in a results table.

Called before `main()`, so a run that fails halfway still leaves a record of how far it got.
