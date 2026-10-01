# Can ERVS replace the recency window? (2026-10-01)

Status: **EVIDENCE — complete, 16 new runs + 16 reused cells**, seed 0. Not a final claim.

[PREREG](PREREG.md) (committed `d2b0529` before any run). Runner
`benchmarks/online_gs/campaigns/gain_attribution/run_ervs_window_replacement.py`; window-free arms use
`--batch-quotas 0 6 6` (window slots moved to the keyframe pool, keyframe share unchanged). B and B-RR are reused
from [b_ablation_v2](../b_ablation_v2/README.md) (and through it from the pilot for rot/rpng at budget 15).
Raw: `results/campaigns/gain_attribution/ervs_window_replacement/v1/`. One failed launch (reference-path bug, no GPU
work) is kept in raw `failed_attempts/`.

## Results (whole-cohort held-out PSNR, dB)

| Scene | Budget | B (win, ERVS) | B-RR (win, RR) | W0-ERVS | W0-RR | R1 W0RR−BRR | R2 W0E−B | R3 gap on → off | Recent-third W0E−W0R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| aria1253rot | 15 | 23.81 | 23.68 | 23.68 | 23.77 | +0.08 ✗ | −0.14 ✓ | +0.13 → −0.09 ✗ | +0.21 |
| aria1253rot | 25 | 24.53 | 24.60 | 24.69 | 24.58 | −0.02 ✗ | +0.15 ✓ | −0.06 → +0.11 ✓ | +0.32 |
| table_06 | 15 | 23.79 | 23.34 | 23.80 | 23.63 | +0.29 ✗ | +0.01 ✓ | +0.44 → +0.16 ✗ | +0.52 |
| table_06 | 25 | 24.43 | 24.16 | 24.39 | 24.17 | +0.01 ✗ | −0.03 ✓ | +0.27 → +0.22 ✗ | −0.12 |
| aria1253 | 15 | 23.45 | 23.31 | 23.95 | 24.23 | +0.92 ✗ | +0.50 ✓ | +0.14 → −0.29 ✗ | +0.21 |
| aria1253 | 25 | 24.52 | 24.93 | 24.96 | 25.30 | +0.37 ✗ | +0.44 ✓ | −0.41 → −0.34 ✓ | +0.33 |
| square-1 | 15 | 20.77 | 20.98 | 20.85 | 20.71 | −0.27 ✓ | +0.08 ✓ | −0.21 → +0.14 ✓ | +0.33 |
| square-1 | 25 | 21.37 | 21.42 | 21.38 | 21.34 | −0.08 ✓ | +0.01 ✓ | −0.05 → +0.04 ✓ | +0.06 |

Scene means: budget 15 — B 22.96, B-RR 22.83, W0-ERVS 23.07, W0-RR 23.09; budget 25 — 23.71, 23.78, 23.86, 23.85.

## Reading against the PREREG

- **R1 (RR needs the window): 2/8** (square-1 only). In aria1253 and table_06 at 15, RR *improves* without the window.
- **R2 (ERVS does not need it): 8/8.**
- **R3 (ERVS gains more without the window): 4/8** (budget 15: 1/4, budget 25: 3/4).
- **Replacement claim not supported** (requires R1 and R2 in ≥3/4 scenes at a budget).

## Mechanism

First-service latency (median, completed services; dense from admission, keyframes from first appearance in the
mapper window) does **not** favour ERVS: dense latency is equal or shorter under RR in every cell, and after removing
the window keyframe latency rises from ≈13–17 to ≈17–78 for both samplers, without a consistent ERVS advantage.
The premise that RR makes newcomers wait while ERVS serves them first is not borne out by these records.

## Exploratory observations (not preregistered)

- **The window slot itself is not useful on average.** Removing it never resolved-hurt ERVS (R2 8/8) and raised the
  4-scene mean by about +0.1 dB for both samplers; aria1253 gains +0.4 … +0.9 dB. Changing the adopted recipe would
  need its own preregistered confirmation (more scenes, seeds).
- **Recent-third PSNR favours ERVS without the window in 7/8 cells** (+0.06 … +0.52; one −0.12), versus 5/8 with the
  window in b_ablation_v2. No noise reference exists for this subset; descriptive only.
- Whole-cohort ERVS−RR averages ≈0 with or without the window.

## Implications

- ERVS cannot currently be presented as a replacement for the recency window, nor as a whole-cohort quality gain.
- Two leads that would each need their own preregistered test: (1) drop the window from the recipe;
  (2) ERVS's effect on recently observed regions without the window (recent-third, new-region convergence), with a
  multi-seed noise reference for that subset.
