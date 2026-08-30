# reports/figures

Report figures, written only through `common.save_figure`, which saves a raster copy for the README and a vector copy for the paper. Needing the vector version after the fact otherwise means re-running the script.

Figure builders live in one module under `src`. Both the figure script and the notebooks call the same builders, so a figure a notebook saves is the same file the script renders and is reproducible either way.

What is not allowed is a notebook cell that constructs a figure inline and saves it. That artifact exists only as a side effect of executing the notebook, no script regenerates it, and it goes stale silently when the results behind it change. `10_verify_invariants.py` checks for exactly that.
