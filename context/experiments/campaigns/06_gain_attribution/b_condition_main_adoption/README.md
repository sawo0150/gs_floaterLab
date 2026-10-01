# Adopt B in main — 2026-10-01

User explicitly selected B (KF RGB + metric depth, dense RGB only) as the latest
recipe and requested merging the tested branch into main and committing it.

- Main before merge: `50286727`.
- Tested branch tip merged: `37fb915242b55249c26bb4707a0d800d8789a1d5`.
- KF metric depth L1 weight 0.25, normals off; dense depth off, full dense
  gradients, 40 single-view Adam updates/KF; warp backward on.
- Preserve main's FIFO changes and evaluation consistency checks.
- Official entry point: `scripts/selected_mapping/run.py`.
- Original 24-run evidence: [dense-depth comparison](../dense_depth_four_scene/README.md).

Fresh integration gate: run the official main entry point on all four scenes,
seed 0, twice-evaluated held-out PSNR within 0.05dB of the corresponding tested B
map. Require identical per-prefix budgets, supervision traces, trajectories,
evaluation cohorts, loss configuration/counters and rasterizer hash.

Status: **ADOPTED — main merge commit `6d200f0f4b70c2e25685c2e53e5890fb5e165d6b`**, integration 4/4 passed. This is fixed-work replay, not a new
live-budget performance claim. No remote push was requested.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/validate_b_condition_main_adoption.py`.
Raw: `results/campaigns/gain_attribution/b_condition_main_adoption/v1/`.

## Integration results

| Scene | Main B PSNR | Prior B seed0 | Difference dB |
|---|---:|---:|---:|
| aria1253 | 25.774661 | 25.780230 | -0.005569 |
| table_06 | 25.022165 | 25.023729 | -0.001563 |
| square-1 | 21.861912 | 21.858617 | +0.003295 |
| aria1253rot | 24.984968 | 24.999312 | -0.014344 |

CPU: 14 selected-mapping tests + 8 geometry integration tests passed. All four runs matched loss/raster, per-prefix budget, exact supervision trace, trajectories and held-out cohorts. No source hashes changed during validation. Named PLY links are under raw `ply/`.

## Commit

Local main: `6d200f0f4b70c2e25685c2e53e5890fb5e165d6b`. Merge parents: `50286727` and `37fb9152`. VIGS-SLAM-custom worktree is clean. Post-commit source/input/raster preflight passed. No remote push was performed.

2026-10-01 update: `6d200f0f` was pushed to GitHub `sawo0150/VIGS-SLAM-custom` main (fast-forward from `50286727`) at the user's request.
