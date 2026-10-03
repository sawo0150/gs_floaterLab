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

## Amendment 1 (2026-10-03, after the smoke's first attempts; before any result)
Attempt 1 failed (drain before a control ran under the control's `torch.no_grad`; fixed with `enable_grad`). Attempt 2
ran correctly (final generation 1,775 renders = online) but failed the worker's `growth_capacity` check, which encodes
the online causal rule "one dense admission per κ = 16 steps"; the offline arm breaks it by design. The patch now
re-evaluates that check with only the final-generation preadmission exempt (all other admissions must satisfy it) and
adds `offline_preadmission_is_reference_set`. Both attempts are archived under `failed_attempts/`.

## Amendment 2 (2026-10-04, after stage 1; user asked to extend to the other scenes)
Stage 2: the 15 extra scenes of `ervs_vs_iid_scenes` (cvpr fixed_work_v1 setups, same preflight and legacy-IMU
launcher as their online runs), offline seed 0 only (15 runs). Reference set = each scene's online `ervs_k16_s0` final
dense/KF sets (verified identical across the 3 online arms × 3 seeds for all 15 scenes). Same gates as stage 1.
Analysis adds two descriptive views fixed before the runs: (a) cumulative training share by arrival order (Lorenz-style,
offline = diagonal) and its area to the diagonal; (b) the gap centred per scene, d(t) − mean d, with the mean absolute
deviation over the first 90% of the stream as the flatness measure (offline seed 0 vs the online seed mean for the 15
new scenes). Tested on 4 scenes beforehand and dropped: local count ratio vs gap (sign varies by scene, ρ −0.30…+0.46).
