# ERVS K16 vs uniform with replacement, 3 seeds × four B scenes (2026-10-03)

Status: **EVIDENCE — complete** (34 new runs, all gates passed; 48 runs used with reused seed 0).
[PREREG](PREREG.md) (`c52d0d4`). Raw: `results/campaigns/gain_attribution/ervs_vs_iid_seeds/v1/`; figures
`temporal_abs_seedmean.png`, `temporal_paired_seedmean.png`, bins `temporal_seedmean.json`;
script `benchmarks/online_gs/campaigns/gain_attribution/plot_ervs_vs_iid_seeds.py`.

## Seed-mean difference ERVS K16 − uniform iid (dB)

| Cell | ΔPSNR | seed sd | per-seed ΔPSNR | Δmin-bin | Δworst-Q1 | ERVS / iid PSNR |
|---|---:|---:|---|---:|---:|---|
| aria1253 15 | +0.315 | 0.07 | +0.24 +0.38 +0.33 | +0.146 | +0.602 | 23.41 / 23.10 |
| aria1253 25 | −0.108 | 0.53 | +0.19 +0.21 −0.72 | +0.167 | −0.101 | 24.55 / 24.66 |
| table_06 15 | −0.193 | 0.15 | −0.07 −0.36 −0.14 | −0.384 | −0.015 | 23.58 / 23.78 |
| table_06 25 | +0.092 | 0.14 | +0.19 +0.15 −0.07 | −0.087 | +0.041 | 24.41 / 24.32 |
| rot 15 † | +0.083 | 0.15 | +0.24 −0.07 +0.08 | −0.170 | −0.116 | 23.74 / 23.66 |
| rot 25 † | +0.151 | 0.12 | +0.22 +0.01 +0.23 | −0.053 | +0.065 | 24.58 / 24.43 |
| square-1 15 † | +0.179 | 0.07 | +0.13 +0.26 +0.15 | −0.128 | −0.143 | 20.88 / 20.70 |
| square-1 25 † | +0.161 | 0.13 | +0.24 +0.01 +0.23 | +0.059 | −0.257 | 21.43 / 21.27 |
| **mean of 8** | **+0.085 ± 0.058 s.e.** | | | −0.056 ± 0.064 | +0.009 ± 0.092 | |

† scenes used to select K = 16. ERVS ahead in mean PSNR in 6/8 cells; min-bin 3/8; worst-Q1 3/8.

## Temporal (paired per view, 8-cell mean of seed means; five bins, ± s.e. over cells)

| 0–20% | 20–40% | 40–60% | 60–80% | 80–100% |
|---:|---:|---:|---:|---:|
| −0.22 ± 0.08 | +0.07 ± 0.14 | +0.34 ± 0.14 | +0.23 ± 0.13 | +0.00 ± 0.05 |

## Reading

- With seeds and cells averaged, a clear temporal pattern: ERVS is lower on the earliest 20% of the stream and higher in
  the middle (40–80%); the end is equal. The mean PSNR gain (+0.09 dB) comes from the middle of the stream.
- The worst-region claim is not supported: min-bin and worst-Q1 differences average ≈ 0 and favour ERVS in only 3/8 cells.
- The early-stream deficit matches the mechanism: early views accumulate the most services and get down-weighted.
