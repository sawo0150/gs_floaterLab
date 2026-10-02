# ERVS (K=16) vs uniform sampling on held-out scenes (2026-10-02)

Status: **EVIDENCE — complete, 12 runs**, seed 0, held-out scenes aria1253 and RPNG table_06 (not used for K tuning).

[PREREG](PREREG.md) (committed `be1f06e` before any run). All runs passed their gates (group queue used; uniform τ
applied; repeated in-batch draws for uniform_iid). Raw and per-cell metrics:
`results/campaigns/gain_attribution/ervs_vs_uniform_k16/v1/` (`summary.json`, `metrics.json`).

## Results

β effect = ERVS K16 − uniform K16 (same group queue, only the count weighting differs);
K effect = uniform K16 − uniform with replacement. Noise references: aria1253 0.021, table_06 0.048 dB.

| Metric | Cell | ERVS K16 | Uniform K16 | Uniform iid | β effect | K effect |
|---|---|---:|---:|---:|---:|---:|
| PSNR | aria 15 | 23.30 | 23.70 | 23.06 | −0.395 | +0.639 |
| | aria 25 | 24.82 | 24.61 | 24.63 | +0.211 | −0.023 |
| | table_06 15 | 23.61 | 23.69 | 23.68 | −0.082 | +0.010 |
| | table_06 25 | 24.52 | 24.56 | 24.33 | −0.036 | +0.228 |
| min-bin PSNR | aria 15 | 22.07 | 22.15 | 22.13 | −0.077 | +0.021 |
| | aria 25 | 22.77 | 22.81 | 22.77 | −0.044 | +0.048 |
| | table_06 15 | 22.11 | 22.55 | 22.54 | −0.437 | +0.006 |
| | table_06 25 | 22.52 | 22.89 | 22.52 | −0.372 | +0.376 |
| worst-Q1 | aria 15 | 20.77 | 21.21 | 20.47 | −0.446 | +0.747 |
| | aria 25 | 22.06 | 22.16 | 22.01 | −0.103 | +0.146 |
| | table_06 15 | 20.82 | 21.01 | 21.11 | −0.183 | −0.103 |
| | table_06 25 | 21.07 | 21.26 | 21.09 | −0.191 | +0.168 |

SSIM/LPIPS differences are ≤ 0.01 in every cell (see `metrics.json`).

## Reading against the PREREG

- **β effect (ERVS count weighting, τ = 4 per_view) is negative on the balancing metrics in 4/4 cells:** min-bin PSNR
  −0.04 … −0.44 dB and worst-Q1 −0.10 … −0.45 dB. Mean PSNR is negative in 3/4 cells (aria 25 is +0.21).
  The claim "ERVS raises the worst views compared with uniform sampling" is **not supported**; the opposite holds here.
- **K effect (group without replacement vs with replacement) is non-negative in most cells:** min-bin 4/4 ≥ 0
  (+0.006 … +0.38), mean PSNR 3/4 (+0.64 on aria 15, +0.23 on table_06 25), worst-Q1 3/4.
- Consistent with the 3dgs-custom paper_ervs_alignment result (uniform group ≈ best; stronger balancing worse).
  B's τ = 4 per_view corresponds to a strong balancing strength (τ_paper = 4/N).
- Single seed, two held-out scenes.
