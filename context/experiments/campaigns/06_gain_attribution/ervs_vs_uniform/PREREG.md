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
