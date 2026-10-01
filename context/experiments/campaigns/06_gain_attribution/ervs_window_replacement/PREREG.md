# Preregistration — can ERVS replace the recency window? (2026-10-01, before any run)

## Question

In B, 3 of 12 slots go to the recent-keyframe window (uniform). The window guarantees service to newly arrived
keyframes — the same problem ERVS addresses (least-served first, immediate first service), whereas RR appends
newcomers to the current epoch. Hypothesis: **without the window, RR degrades and ERVS does not**, i.e. ERVS
subsumes the hand-designed recency window.

## Arms (official B worker/recipe/environment + overrides only; seed 0; 1 image = 1 Adam step)

| Arm | Quotas window:KF pool:dense | Sampler | Source |
|---|---|---|---|
| B | 3:3:6 | ERVS | reused from [b_ablation_v2](../b_ablation_v2/README.md) |
| B-RR | 3:3:6 | RR | reused from b_ablation_v2 |
| W0-ERVS | 0:6:6 | ERVS | new: `--batch-quotas 0 6 6` |
| W0-RR | 0:6:6 | RR | new: `--batch-quotas 0 6 6 --selector rr` |

The window's 3 slots move to the keyframe pool, so the keyframe share stays 6/12 and only the window changes.
Scenes aria1253, aria1253rot, RPNG table_06, UTMM square-1; budgets 15 and 25. 16 new runs.

## Metrics

1. Whole-cohort held-out PSNR (primary), SSIM, LPIPS.
2. Recent-third held-out PSNR (pilot definition).
3. Mechanism: first-service latency of newly available views, in completed services — dense views from their
   admission, keyframes from their first appearance in the mapper window; keyframe-pool and dense service CV.

## Noise references

B seed-0/1 spread (colin): aria1253 .021, rot .152, table_06 .048, square-1 .019 dB.

## Decision rules (fixed now)

Per scene and budget, with Δ above the noise reference counted as resolved:

- **R1 (RR needs the window):** W0-RR − B-RR < 0, resolved.
- **R2 (ERVS does not):** W0-ERVS − B ≥ −noise (not resolved-negative).
- **R3 (ERVS gains more without the window):** (W0-ERVS − W0-RR) > (B − B-RR) by more than the noise reference.

The replacement claim is supported at a budget if R1 and R2 both hold in ≥3/4 scenes; R3 is reported as supporting
evidence. Budgets 15 and 25 are read separately. Single seed: a supported claim is a candidate for multi-seed
confirmation. No quota/κ/τ changes after seeing results.

## Outputs

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_ervs_window_replacement.py`
- Raw: `results/campaigns/gain_attribution/ervs_window_replacement/v1/w0/<scene>/render<budget>/<arm>/`
- Card: this folder's `README.md`
