# exp78 D1 — RPNG strict mapping-only transfer

Date: 2026-09-11

## Question

Can the gsSLAM quality path beat vanilla VIGS-SLAM when both mappers receive
the same frozen official tracker packets, raw RGB preprocessing, poses,
calibration, held-out UIDs, RTX 5090 TensorRT tracker state, 1.5x sensor-time
budget, and zero optimizer work after EOS?  Does the result transfer beyond
the two development sequences without per-sequence retuning?

## Frozen protocol and selected RPNG recipe

- Official tracker: clean VIGS commit `22ffe24c6df81d0bf63bd20057565c00c51d2996`.
- Held-out split: predeclared `index % 5 == 0 OR final`, excluded from Gaussian
  supervision and birth before mapper dispatch.
- Mapping state: pre-final, no final BA, no final color refinement, no terminal
  prune, carve disabled.
- gsSLAM: causal dense RGB, IMU-shaped rotation, appearance-only dense replay,
  causal online Sobel rank density (mean 2.5, span 2.0), automatic topology
  freeze, 20 ms deadline reserve.
- Vanilla: official `gs_backend`, 50 ms deadline reserve.
- Reproduction entry point:
  `benchmarks/online_gs/run_exp78b_matched_mapping.sh`.
- All three paired arms below have `post_eos_optimizer_updates=0`, zero
  held-out mapping/birth overlap, identical archive hash within each sequence,
  and no future-frame access.

`table_01` and `table_06` are development sequences. `table_02` is the first
validation sequence and was run with the recipe already frozen above.

## Held-out results

| RPNG sequence | Role | Vanilla PSNR / SSIM / LPIPS | gsSLAM PSNR / SSIM / LPIPS | Delta PSNR / SSIM / LPIPS |
|---|---|---|---|---|
| table_01 | development | 24.228 / .8058 / .1941 | 25.363 / .8355 / .1717 | **+1.135 / +.0297 / -.0225** |
| table_06 | development | 23.078 / .7680 / .2520 | 24.454 / .8141 / .1958 | **+1.377 / +.0461 / -.0562** |
| table_02 | validation | 20.608 / .6886 / .2793 | 22.890 / .7758 / .2351 | **+2.282 / +.0871 / -.0442** |
| sequence mean | 2 dev + 1 validation | 22.638 / .7541 / .2418 | 24.236 / .8085 / .2009 | **+1.598 / +.0543 / -.0410** |

Verdict: transfer is real and wins all three metrics on 3/3 sequences, but the
RPNG mean PSNR acceptance threshold of +2.0 dB is not yet met.

## Resource and service telemetry

| Sequence / arm | Adam steps | Rasterized view-updates | Selected dense UIDs | Gaussians | Peak allocated |
|---|---:|---:|---:|---:|---:|
| table_01 vanilla | 1,910 | 21,697 | 0 | 183,765 | 2.31 GiB |
| table_01 gsSLAM | 1,908 | 21,057 | 536 | 437,702 | 4.84 GiB |
| table_02 vanilla | 2,234 | 24,656 | 0 | 258,600 | 3.14 GiB |
| table_02 gsSLAM | 1,685 | 24,749 | 50 | 603,319 | 6.25 GiB |
| table_06 vanilla | 2,365 | 26,387 | 0 | 171,364 | 1.99 GiB |
| table_06 gsSLAM | 3,146 | 25,431 | 939 | 347,099 | 4.10 GiB |

The table_02 gain with only 50 selected dense UIDs shows that dense replay
count alone is not the causal quality explanation; higher causal birth density
and retained keyframe geometry also matter. Conversely, table_01 loses most of
its advantage in the last 300 frames while its 437k-point map reduces replay
throughput. The remaining optimization problem is therefore a birth/replay
allocation trade-off, not simply “run more iterations.”

## Development ablations (table_06 unless stated)

| Axis | PSNR / SSIM / LPIPS | Decision |
|---|---|---|
| online-rank 2.5 + appearance + auto-freeze (v8) | 24.342 / .8098 / .2057 | base transferable mechanism |
| FIFO first-service every 4 draws | 24.356 / .8106 / .2054 | negligible; reject extra policy |
| density 1.5 / span 1.0 | 24.383 / .8068 / .2144 | PSNR small gain, perceptual regression vs v8 |
| pose-confidence loss weighting | 24.213 / .8058 / .2161 | reject |
| endpoint admission <=0.2 | 24.452 / .8121 / .2069 | LPIPS regression vs v8; reject hard eligibility |
| endpoint admission <=0.3 | 24.366 / .8104 / .2073 | reject |
| density 2.5 / span 2.0 + reserve20 | **24.454 / .8141 / .1958** | provisional RPNG recipe; all metrics improve |
| endpoint-near full geometry <=0.1 | 23.597 / .7775 / .2197 | strong failure; dense translation error still poisons geometry |
| density 1.5 on table_01 | 25.381 / .8304 / .1843 | +.018 dB but SSIM/LPIPS worse than 2.5; reject |

A mixed keyframe+dense replay diagnostic was also rejected: it performed one
post-EOS optimizer update and its non-authoritative metric showed no useful
gain. The invalid run is retained, not promoted into the table.

## Dense-pose diagnosis

For RPNG table_06, causal dense translation error is 44.92 mm mean / 247.82 mm
p95. An oracle using the final right endpoint is 13.56 / 42.35 mm, but that
endpoint is unavailable causally. Raw-IMU rotation shaping is accurate
(approximately 0.079 degrees mean versus 1.303 for rotation slerp), while
translation remains unsafe for geometry gradients. This explains why
appearance-only replay transfers and even endpoint-near full-geometry replay
fails.

Evidence:

- `context/experiments/exp78/b_strict_fair_comparison/evidence/dense_imu_translation_rpng_table06.json`
- `results/experiments/exp78/b_strict_fair_comparison/mapping_only/strict1p5/`
- `results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/official_22ffe24_trt/`

## Infrastructure correction

The archive validator used to materialize and retain every geometry tensor
while checking packet filtering, reaching roughly 80% host memory on table_02.
Validation v2 checks the same payload/tensor hashes without caching mapper RGB
and geometry, used about 2% host memory in the observed run, and stores a
manifest-hash-keyed validation cache in each immutable archive. This is an
infrastructure fix only and does not change mapping or metrics.

## Next gate

Run the fixed recipe on the remaining RPNG validation sequences and the
predeclared UTMM recipe, then report sequence mean, majority wins, 1x results,
multi-seed variance, and Aria 1253/305 regression. No RPNG validation sequence
will receive per-sequence retuning.
