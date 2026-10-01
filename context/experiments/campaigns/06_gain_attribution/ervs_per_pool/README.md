# ERVS per pool: keyframe pool vs dense pool (2026-10-02)

Status: **EVIDENCE — complete, 16 new runs + 16 reused cells**, seed 0. Not a final claim.

[PREREG](PREREG.md) (committed `c800b28` before any run). Runtime patch
`benchmarks/online_gs/campaigns/gain_attribution/per_pool_selector.py` (sha-checked copy of the locked
`UnifiedTrainingSet.reserve`, RR limited to `B_RR_ROLES`); launcher path fix `c33ef0d`. Every new run passed the
draw gate: only the intended method was drawn in each pool (e.g. rot/15/ER: ERVS-keyframe 632, RR-dense 1,027).
EE/RR reused from [b_ablation_v2](../b_ablation_v2/README.md). Raw: `results/campaigns/gain_attribution/ervs_per_pool/v1/`.
One failed launch (module shadowing, no mapping) is kept in raw `failed_attempts/`.

## Results (whole-cohort held-out PSNR, dB; `*` above that scene's noise reference)

EE = ERVS/ERVS (B), ER = keyframe ERVS + dense RR, RE = keyframe RR + dense ERVS, RR = RR/RR.

| Scene | Budget | EE | ER | RE | RR | Keyframe-pool effect | Dense-pool effect | Interaction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| aria1253rot | 15 | 23.81 | 23.72 | 23.62 | 23.68 | +0.111 | +0.016 | +0.155 |
| table_06 | 15 | 23.79 | 23.63 | 23.70 | 23.34 | **+0.185*** | **+0.259*** | −0.201 |
| aria1253 | 15 | 23.45 | 22.75 | 23.61 | 23.31 | **−0.359*** | **+0.499*** | +0.406 |
| square-1 | 15 | 20.77 | 20.70 | 20.89 | 20.98 | **−0.203*** | −0.012 | +0.148 |
| aria1253rot | 25 | 24.53 | 24.56 | 24.45 | 24.60 | +0.024 | −0.088 | +0.120 |
| table_06 | 25 | 24.43 | 24.37 | 24.48 | 24.16 | **+0.079*** | **+0.188*** | −0.274 |
| aria1253 | 25 | 24.52 | 24.91 | 24.83 | 24.93 | **−0.166*** | **−0.247*** | −0.287 |
| square-1 | 25 | 21.37 | 21.41 | 21.42 | 21.42 | −0.028* | −0.020* | −0.044 |

Pool effect = mean of the two paired differences with the other pool held fixed; interaction =
(EE − ER) − (RE − RR). Four-scene means — budget 15: EE 22.95, ER 22.70, RE 22.96, RR 22.83;
budget 25: EE 23.71, ER 23.81, RE 23.79, RR 23.78.

## Reading against the PREREG

- **Keyframe-pool effect:** no signal at either budget (signs split 2/2).
- **Dense-pool effect:** no signal (budget 15: positive in 3/4 but above noise in 2/4; budget 25: mixed).
- **Cancellation hypothesis not supported:** opposite-sign pool effects occur only in aria1253 at budget 15.
- Interactions are as large as the main effects (−0.29 … +0.41), so the pool effects are not additive.
- Mechanism: the keyframe-pool CV follows the keyframe-pool sampler (ERVS ≈0.58–0.67 vs RR ≈0.66–0.74, all scenes);
  the dense CV changes little with the dense sampler. Balancing is achieved where ERVS is applied, but quality does
  not follow it consistently.

## Conclusion across the ERVS experiments

Pilot chain, b_ablation_v2, window replacement and this per-pool factorial (single seed, four scenes, budgets
15/25/40) all show ERVS balancing service counts as designed, while its held-out effect depends on scene, pool and
budget with large interactions and four-scene means within ≈0.25 dB of RR. On the B system the sampler is a
second-order factor. Recommended: stop sampler variants; centre the photometric claim on dense RGB supervision and
test role separation (keyframe share) directly.
