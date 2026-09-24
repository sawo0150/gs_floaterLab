# exp96 — naive filter-prune isolation stopped on scheduler coupling

- Date: 2026-09-24
- Status: stopped during RPNG `table_01`; no quality result
- Runner: `benchmarks/online_gs/run_exp96_filter_prune_isolation.py`
- Partial output: `results/experiments/exp96_filter_prune_isolation/`
- Detailed record: [summary](benchmark_custom/exp96_filter_prune_isolation_20260924/summary.md)

Exp96 attempted to withhold ordinary regular opacity/size deletion while
keeping R4's other components fixed.  This is not a valid single-factor
ablation because R4's observation-driven phase controller consumes the actual
post-prune Gaussian count.  Without deletion the candidate produced only net
growth, did not obtain the controller's prune/recovery certificate, and opened
a third topology event at frame 657; Exp95 control has two.

The run was stopped before completion rather than reporting a confounded
PSNR.  The partial log proves physical filter deletion was zero and clone/split
remained active, but it contains no final PLY or held-out evaluation.  A fresh
root and source lock are required for a corrected shadow-count experiment.
