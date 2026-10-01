# ERVS vs RR at very low budgets (5 and 10 renders/KF) (2026-10-02)

Status: **EVIDENCE — complete, 16 runs**, seed 0, paper system B (depth on). Not a final claim.

[PREREG](PREREG.md) (committed `053a97b` before any run). Runner
`benchmarks/online_gs/campaigns/gain_attribution/run_ervs_low_budget.py`. Raw:
`results/campaigns/gain_attribution/ervs_low_budget/v1/`. All runs passed the execution audit and twice-run evaluation.

## Results (whole-cohort held-out PSNR, dB; `*` above the scene's budget-40 noise reference)

| Scene | Budget | ERVS | RR | ERVS−RR | Recent-third Δ | KF-pool CV ERVS/RR | Dense CV ERVS/RR |
|---|---:|---:|---:|---:|---:|---:|---:|
| aria1253rot | 5 | 21.918 | 21.617 | **+0.301*** | +0.61 | 0.97/0.80 | 0.79/0.80 |
| aria1253rot | 10 | 23.067 | 23.062 | +0.005 | −0.36 | 0.65/0.72 | 0.87/0.85 |
| table_06 | 5 | 21.936 | 21.848 | **+0.088*** | +0.01 | 0.96/0.80 | 0.82/0.84 |
| table_06 | 10 | 22.942 | 23.199 | **−0.257*** | −0.14 | 0.66/0.69 | 0.86/0.87 |
| aria1253 | 5 | 21.213 | 20.577 | **+0.636*** | −0.70 | 0.99/0.74 | 0.75/0.77 |
| aria1253 | 10 | 22.961 | 22.555 | **+0.406*** | −0.16 | 0.67/0.72 | 0.86/0.82 |
| square-1 | 5 | 19.428 | 19.358 | **+0.070*** | +0.52 | 0.95/0.88 | 0.76/0.79 |
| square-1 | 10 | 20.281 | 20.359 | **−0.078*** | +0.47 | 0.72/0.76 | 0.84/0.81 |

## Budget curve of ERVS−RR (dB; 15/25 from b_ablation_v2, 40 from the pilot)

| Scene | 5 | 10 | 15 | 25 | 40 |
|---|---:|---:|---:|---:|---:|
| aria1253rot | +0.30 | +0.00 | +0.13 | −0.06 | −0.28 |
| table_06 | +0.09 | −0.26 | +0.45 | +0.27 | +0.22 |
| aria1253 | +0.64 | +0.41 | +0.14 | −0.41 | — |
| square-1 | +0.07 | −0.08 | −0.21 | −0.05 | — |

## Reading against the PREREG

- **Budget 5: positive signal** (4/4 scenes positive and above the noise reference) — the first ERVS signal on B.
- **Budget 10: no signal** (2/4 positive above noise).
- Per the PREREG, "ERVS helps under scarce budgets" is supported at budget 5 as a **candidate** requiring multi-seed
  confirmation.

## Caveats (not overriding the rule)

- **Mechanism reversed at budget 5.** ERVS's keyframe-pool service CV is *higher* than RR's (0.95–0.99 vs 0.74–0.88);
  at budgets ≥10 it is lower, as designed. The budget-5 gain therefore cannot be attributed to ERVS's balancing. A
  plausible cause is that with very few completed services the Gibbs weights are nearly uniform, so ERVS behaves like
  near-random sampling while RR enforces epochs; this is not tested here.
- **Non-monotonic curves.** table_06 flips at 10 (−0.26) between positive neighbours; rot is 0 at 10. The noise
  references were measured at budget 40; single-seed spread at budgets 5–10 is unknown and may be larger.
- **Operating point.** Live runs realise ≈20–30 renders/KF; budget 5 is far below it (PSNR 19–22 dB).
- Recent-third Δ at budget 5 is mixed (+0.61, +0.01, −0.70, +0.52).

## Next step if pursued

Multi-seed confirmation at budget 5 (seeds 1–2, 16 runs) with a budget-5 noise reference, and a check of whether the
gain follows sampling randomness (e.g. uniform-with-replacement control) rather than balancing.
