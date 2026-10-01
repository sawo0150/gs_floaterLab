# Preregistration — B ablation chain pilot (written 2026-10-01, before any run)

## Question

Starting from the adopted condition B (VIGS-SLAM-custom main `6d200f0f`), which parts of the
paper's photometric claims (view-set growth, pacing, ERVS) produce a measurable held-out gain?
This is a **fast single-seed pilot** to find signals; it does not establish final paper claims.

## Fixed setup

- Mapper: `scripts/selected_mapping/run_selected_worker.py` with the official B recipe arguments
  (`configs/selected_mapping_fixed40.json`) and the B environment (`selected_recipe.recipe_environment`).
  Each arm appends only the override arguments listed below (argparse: last value wins).
- Inputs: the B source lock's frozen tracker archives and setups (preflight PASS on this machine).
  Setups copied byte-identical from colin (sha matches lock). Machine profile
  `results/local_machine_profiles/rtx5070ti_b_ablation.json`.
- Scenes: `aria1253rot` (rot) and RPNG `table_06` (rpng). Mapper seed 0 only.
- Budgets: 15 and 40 training renders/KF. Zero tail. Fixed-work replay, not a live-time test.
- GPU: local RTX 5070 Ti, one run at a time, GPU idle check before each run.

## Arms

Chain (both scenes × both budgets):

| Arm | Meaning | Overrides on top of B |
|---|---|---|
| R1 | KF window only | `--batch-quotas 12 0 0` |
| R2 | + KF pool (ERVS); dense slots filled by keyframes | `--auxiliary-mode kf_native` |
| R3 | + dense pool, immediate admission (no pacing) | `--membership immediate` |
| R4 | + growth pacing κ=16 = **B** | none |
| R4rr | B with RR instead of ERVS | `--selector rr` |

ERVS-favourable regime (both scenes, budget 15 only; larger pool relative to budget):

| Arm | Overrides |
|---|---|
| K4_ervs | `--kappa 4` |
| K4_rr | `--kappa 4 --selector rr` |

(κ=16 at budget 15 is shared with chain R4 / R4rr.)

## Metrics

- Primary: fixed held-out PSNR (saved map, evaluated twice; must pass consistency).
- Secondary: SSIM, LPIPS, Gaussian count.
- Recent-third PSNR: mean PSNR over held-out views whose frame index is in the last third of the
  sequence (post-hoc grouping of the same per-view results; definition fixed here).
- Service balance (mechanism check for ERVS/RR): from per-view completed service counts in the run
  record — coefficient of variation, minimum count, and admitted dense pool size.
- Mapping seconds: descriptive only.
- Checkpoint convergence curves are **not** part of this pilot (no snapshots); they are follow-up
  work for arms that show a signal.

## Noise reference (single seed)

From the colin four-scene dense-depth experiment (same B recipe, seeds 0/1), max over arms A and B:
rot **0.152 dB**, rpng **0.048 dB**. A difference smaller than this is reported as "unresolved".

## Predictions and reading rules (fixed now)

- **C1 dense growth:** R4 − R2 > noise in both scenes at both budgets (prior: +0.24 … +0.60 dB at 40).
- **C1 pacing:** R4 − R3 > noise in both scenes, expected to be larger at budget 15 than at 40.
  If R3 ≈ R4 (unresolved) at both budgets, the paper should not claim that pacing beats naive
  admission; it should claim dense RGB supervision only.
- **ERVS:** first check the mechanism — ERVS must lower the service-count CV vs RR. Only then read
  quality: ERVS − RR in full PSNR and recent-third PSNR, expected larger at κ=4/budget 15 than at
  κ=16/budget 40. If the mechanism does not change, quality differences are treated as noise.
- A "signal" requires the same sign in both scenes and |Δ| above that scene's noise reference.
  Signals are candidates for a multi-seed confirmation, not final claims.
- No κ/γ/quota tuning after seeing these results. All arms and scenes are reported.

## Outputs

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_b_ablation_chain.py`
- Raw: `results/campaigns/gain_attribution/b_ablation_chain/v1/<phase>/<scene>/render<budget>/<arm>/`
- Summary: `results/campaigns/gain_attribution/b_ablation_chain/v1/summary.csv`, `SUMMARY.md`
- Card: `context/experiments/campaigns/06_gain_attribution/b_ablation_chain/README.md`
