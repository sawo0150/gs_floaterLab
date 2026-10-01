# B ablation chain pilot (2026-10-01)

Status: **EVIDENCE — pilot complete, 24/24 runs**, single seed. Not a final paper claim.

Question: on the adopted B mapper (VIGS-SLAM-custom main `6d200f0f`), which photometric claims of the paper
(dense view growth, admission pacing, ERVS) give a measurable held-out gain?

- [PREREG](PREREG.md) (sha `c720483a`, committed `fa26366` before any run).
- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_b_ablation_chain.py` — official B worker, recipe and
  environment; each arm only appends override arguments.
- Scenes aria1253rot (rot) and RPNG table_06 (rpng); budgets 15/40 training renders/KF; seed 0; RTX 5070 Ti;
  frozen-tracker fixed-work replay, zero tail. Noise references (colin B seeds 0/1): rot 0.152 dB, rpng 0.048 dB.
- Raw: `results/campaigns/gain_attribution/b_ablation_chain/v1/` (`SUMMARY.md`, `summary.csv`, `summary.json`).

## Results (held-out PSNR, dB)

| Arm | rot 15 | rot 40 | rpng 15 | rpng 40 |
|---|---:|---:|---:|---:|
| R1 KF window only | 20.572 | 20.875 | 21.067 | 21.044 |
| R2 + KF pool (ERVS) | 23.308 | 24.445 | 23.598 | 24.778 |
| R3 + dense, immediate admission | 23.695 | 24.799 | 23.788 | 24.988 |
| R4 + growth pacing κ=16 (= B) | 23.812 | 24.992 | 23.787 | 25.028 |
| R4rr (B with RR) | 23.685 | 25.270 | 23.342 | 24.808 |

| Step | rot 15 | rot 40 | rpng 15 | rpng 40 | Reading |
|---|---:|---:|---:|---:|---|
| R1→R2 KF pool | +2.736 | +3.570 | +2.531 | +3.734 | signal (prior practice, not our contribution) |
| R2→R3 dense RGB | +0.387 | +0.355 | +0.190 | +0.210 | **signal 4/4** |
| R3→R4 pacing | +0.117 | +0.193 | −0.001 | +0.040 | no signal (1/4 above noise) |
| ERVS − RR | +0.127 | −0.278 | +0.445 | +0.220 | inconsistent sign |

ERVS-favourable regime (κ=4, budget 15): ERVS − RR = rot +0.142, rpng −0.049. The predicted amplification did not occur.

B reproduces colin's seed-0 B (rot40 24.992 vs 24.999; rpng40 25.028 vs 25.024).

## Interpretation

- **Dense RGB supervision (C1) is the robust gain**: +0.19 … +0.55 dB over keyframe-only service in all four cells.
- **Pacing is not separable from naive admission** in this pilot. Immediate admission takes 1,042/1,810 dense views
  (26–53% never served) versus 131–465 with pacing, at similar PSNR. A paper claim for pacing would have to be
  efficiency (same quality, far fewer admitted views), which needs its own measurement.
- **ERVS does not give a consistent whole-cohort gain.** Its measurable mechanism is keyframe-pool balancing: ERVS
  lowers the keyframe service-count CV in 6/6 paired cells (counting window services, its `all_rgb` scope). It does not
  balance the dense pool better than RR (worse at κ=4). Recent-third PSNR favours ERVS in 5/6 cells
  (+0.16 … +0.49, one −0.03), which matches the intro's "older keyframes accumulate more updates" argument; this subset
  has no noise reference yet.
- Next candidates: multi-seed confirmation of the recent-third ERVS effect and of R2→R4 on more scenes; reframe or drop
  the pacing claim; checkpoint curves for R3 vs R4 if pacing is kept as an efficiency claim.

## Execution notes

Two B-validated setups were copied from colin (hash-matched to the B source lock). The rot/rpng archives are read from
the external volume through local symlinks; `droid.pth` for the rpng setup maps to an identical local copy
(sha `46476ef6…`). Two failed path-setup attempts are preserved in raw `failed_attempts/`; no completed run was
rerun or overwritten. Local disk had 23 GB free, so archives were not copied to the SSD as originally planned.
