# Offline (deferred-training) reference vs online samplers — PREREG (2026-10-03)

**Question.** Relative to an offline 3DGS reference that trains every view equally after the stream, does online
uniform replay tilt per-view quality toward early views, and does ERVS reduce that tilt?

**Offline arm** (`offline_patch.py`, B mapper 6d200f0f, budget 25): same frozen tracker archive, same Gaussian births
(local birth off → births do not read the trained map), same render credit. No photometric step during the stream;
pending credit is spent before each mapper control (rescale/reset) on the current generation; right after the last
non-terminal arrival the final generation's dense pool is set to the online runs' final admitted set (identical across
uniform_iid / uniform_k16 / ERVS and seeds, verified on the 4 scenes) and the remaining credit is spent with epoch RR
over KF and dense pools at quotas (0, 6, 6) (same 50:50 KF/dense split as online). Protected opacity pruning every
300 renders inside the drain. Known differences, reported not corrected: offline trains with final poses; pruning
timing differs.

**Plan.** Smoke: utmm (square-1) seed 0 — gates: valid execution and all worker checks, final-generation renders equal
to the online run's final-generation services, final dense pool = reference set, KF pool = reference set, per-view
count spread within each pool ≤ 1 (RR), Gaussian count within ±30% of online. If the smoke passes, stage 1 runs
automatically: 4 scenes (aria1253, table_06, aria1253rot, square-1) × offline seeds 0, 1, 2 (11 more runs), paired
with the existing online seeds. Stage 2 (remaining 15 scenes, seed 0) needs a separate decision.

**Metric.** Per held-out view: d(v) = PSNR_online(v) − PSNR_offline(v), seed-paired; curve over stream time (10%
moving average), Spearman slope of d over the first 90% of the stream, five time bins, and per-view training counts.

**Prediction (pre-declared).** uniform_iid: d > 0 early and < 0 late (negative slope). ERVS: slope closer to 0 than
uniform_iid (and uniform_k16). Primary test: mean over scenes of |slope_ERVS| < |slope_uniform_iid| and the
late-bin (60–100%) d of ERVS above uniform_iid. With 4 scenes this is directional evidence only.
