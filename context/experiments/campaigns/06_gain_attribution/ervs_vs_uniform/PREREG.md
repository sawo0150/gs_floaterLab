# Preregistration — ERVS vs uniform sampling on B (2026-10-02, before any uniform run)

## Why

All previous B comparisons used the code's `rr` selector, which is **epoch-based random reshuffling** (each pool is
shuffled and consumed once per epoch; newcomers join the current epoch). Epoch RR already equalizes service counts by
construction. The paper's baseline is different: "Round-robin ... changing only the Gibbs energy to zero", i.e.
**uniform sampling** over the same pools. This experiment compares ERVS against that baseline.

## Arms (official B worker/recipe/environment; fixed-work frozen-tracker replay; seed 0)

| Arm | Overrides | Meaning |
|---|---|---|
| ERVS (B) | — | reused: b_ablation_v2 (15/25), ervs_low_budget (5/10), pilot for rot/rpng at 15 |
| Uniform | `--tau 1e12` | Gibbs weights exp(−Δn / (τ/N·(Σn+1))) → 1: uniform sampling within each pool; same window, quotas, batch-level no-duplicate rule, commit semantics |

`tau` is used only by the ERVS weights (`unified_view_training.py` lines 68–69); no other component reads it.
Scenes aria1253, aria1253rot, RPNG table_06, UTMM square-1; budgets 5, 10, 15, 25 renders/KF. 16 new runs.

## Metrics (fixed now; per-view held-out PSNR from the fixed manifest, time order by frame index)

Primary: whole-cohort held-out PSNR, SSIM, LPIPS.
Mechanism: keyframe-pool and dense-pool service-count CV (all_rgb counts, final generation); never-served views;
mean service count per admission-time quintile.
Secondary:
- worst-Q1 PSNR = mean of the arm's own lowest ⌈n/4⌉ views;
- late PSNR = mean over the last 20% of held-out views in time order;
- bin range = max − min of the five time-bin (20%) mean PSNRs.

## Noise references

B seed-0/1 spread (colin, budget 40): aria1253 .021, rot .152, table_06 .048, square-1 .019 dB. Low-budget spread may be
larger (single seed).

## Reading rules

- Mechanism first: ERVS must have lower service-count CV than Uniform in the cell; otherwise quality differences are
  not attributed to balancing.
- ERVS−Uniform is a **signal** at a budget if positive in ≥3/4 scenes and above the noise reference in those scenes
  (primary PSNR); secondary metrics are counted the same way (positive = better for ERVS; for bin range, lower).
- All budgets and scenes reported; the epoch-RR results stay in the record as a separate, stronger baseline.
  No τ/κ/quota changes after seeing results.

## Outputs

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_ervs_vs_uniform.py`
- Raw: `results/campaigns/gain_attribution/ervs_vs_uniform/v1/uniform/<scene>/render<budget>/uniform/`
- Card: this folder's `README.md`

## Amendment 1 — before any completed run (2026-10-02)

The revised method (colin `paper/latex/sec/4_method.tex`, 2026-10-02 21:53) defines the baseline as uniform sampling
and ERVS as two parts: count-dependent Gibbs weights (β > 0) and K-group sampling without replacement (K > 1). The
earlier queued uniform run was stopped by the user before completing any cell (kept in `failed_attempts/`).

Arms (all B, fixed-work, seed 0, 4 scenes, budgets 5/10/15/25):

| Arm | β | K | Implementation |
|---|---|---|---|
| uniform_iid | 0 | 1 (with replacement) | `--tau 1e12` + `sampling_mode_patch.py` (`B_WITH_REPLACEMENT=1`): keyframe/dense draws no longer exclude views already chosen in the batch; window unchanged |
| uniform_group | 0 | role quota (without replacement) | `--tau 1e12` |
| ERVS (B) | > 0 | role quota | reused |

Gates: recorded policy tau ≥ 1e11 for both uniform arms; uniform_iid must log repeated in-batch draws > 0 in the
keyframe or dense pool.

Metrics, in addition to the list above:
- **min-bin PSNR** = lowest of the five time-bin (20%) mean held-out PSNRs — **co-primary with worst-Q1** for the
  balancing claim;
- mean PSNR / SSIM / LPIPS are always reported next to them, whatever their sign.

Reading: ERVS vs each uniform arm separately (β effect = ERVS − uniform_group; K effect = uniform_group − uniform_iid).
A signal requires ≥3/4 scenes in the same direction above the scene noise reference (dB metrics).
