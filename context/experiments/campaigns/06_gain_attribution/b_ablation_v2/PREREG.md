# Preregistration — ERVS vs RR at scarce and live-representative budgets (2026-10-01, before any run)

Scope reduced from [PLAN.md](PLAN.md) by user decision: **ERVS only (Part A), seed 0 only, budgets 15 and 25,
no snapshots.** Parts B/C and checkpoint curves are not run here.

## Setup

- Mapper: official B worker, recipe and environment (VIGS-SLAM-custom main `6d200f0f`); arms append overrides only.
  Same runner pattern and audits as the [b_ablation_chain pilot](../b_ablation_chain/README.md).
- Scenes: aria1253, aria1253rot, RPNG table_06, UTMM square-1 (the four B-pinned scenes; preflight PASS).
- Budgets: 15 and 25 training renders/KF. Budget 25 is the live-representative point (live FIFO runs realised about
  20–30 renders/KF at 1× on an RTX 5090); 15 is the scarce point.
- Arms: `ervs` (B) and `rr` (`--selector rr`). Seed 0. 1 image = 1 Adam step. Zero tail.
- Reuse: the pilot's seed-0 budget-15 R4 (ervs) and R4rr (rr) runs for aria1253rot and table_06 are identical
  configurations and are reused, not rerun. 12 new runs.

## Metrics

1. Mechanism: keyframe-pool and dense service-count CV (all_rgb counts, final generation), never-served dense views.
2. Recent-third held-out PSNR (held-out views in the last third of the sequence; pilot definition).
3. Whole-cohort held-out PSNR / SSIM / LPIPS (always reported).

## Noise references (single seed)

B seed-0/1 spread from colin's four-scene dense-depth experiment: aria1253 0.021, aria1253rot 0.152,
table_06 0.048, square-1 0.019 dB (whole-cohort PSNR). No reference exists for recent-third PSNR; it is
reported descriptively.

## Reading rules (fixed now)

- **Mechanism first:** ERVS must lower the keyframe-pool CV relative to RR in the same cell.
- **Signal for C2:** at a given budget, ERVS−RR whole-cohort PSNR is positive and above that scene's noise
  reference in ≥3/4 scenes, or recent-third ERVS−RR is positive in ≥3/4 scenes (descriptive, flagged as such).
- Budget 15 and 25 are read separately and both reported. Pilot budget-40 results stay in the record.
- Single seed: any signal is a candidate for multi-seed confirmation, not a final claim. No κ/τ tuning afterwards.

## Outputs

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_b_ablation_v2.py`
- Raw: `results/campaigns/gain_attribution/b_ablation_v2/v1/ervs/<scene>/render<budget>/<arm>/`
- Card: `context/experiments/campaigns/06_gain_attribution/b_ablation_v2/README.md`
