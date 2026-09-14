# exp77 — VIGS final-v7 RPNG/UT-MM 16-sequence benchmark

**Date:** 2026-09-10  
**Verdict:** 15/16 produced mapping and evaluation metrics. Rendering quality is well below 27 dB, one sequence failed to initialize mapping, and one nominally completed sequence is a tracking-metric failure. This run is a VIGS-style pre-final online baseline with queue drain; it is not project-strict sensor-EOS zero-tail.

## Objective

Run the current modified VIGS final-v7 system without per-sequence tuning on all eight ETH-preprocessed RPNG sequences and all eight UT-MM sequences. Record held-out rendering quality, Sim(3)-aligned ATE, scale error, 10 cm recall, runtime, environment, source state, and failures.

## Reproducibility and protocol

- VIGS checkout: `/home/intern/VIGS-SLAM-main-integration-20260828`
- source HEAD: `2a3eeeb5b83743c642bbd7e5278817a4c76228ee`, dirty patch captured with the result
- runner: `benchmarks/online_gs/run_vigs_final_v7_16.py`
- configs: `benchmarks/online_gs/config/vigs_final_v7_{utmm,rpng}.yaml`
- environment: `vigs-slam-5090`; full pip freeze saved in the result root
- tracker `fnet` and `update` TensorRT engines were disabled because their static Aria input shape does not match these datasets. Tracking used PyTorch for those networks; Omnidata TensorRT remained enabled.
- replay budget: 1.5×; seed 0; VIGS final color refinement/BA disabled
- held-out split: every fifth frame plus the final frame. These images are visible to tracking but excluded from Gaussian mapping supervision. Metric rendering itself performs zero map updates.

The original directory label said `fixed1p5_zero_tail_v1`. Log and code inspection showed that after `TRACK_LOOP_DONE`, pending background mapping work is drained before `ONLINE_LOOP_DONE` and the map snapshot. Optimizer work can therefore occur after the last sensor frame. The result and metadata were renamed to **`fixed1p5_prefinal_queue_drain_v1`**. Historical command/path strings inside manifests remain as executed provenance. This protocol must not be reported as the project's strict zero-tail contract, and its held-out split must be aligned before comparing numbers directly with the VIGS paper table.

## Results

All rendering values are the fixed held-out mean. ATE is Sim(3)-aligned; scale error is reported separately because Sim(3) can hide scale drift.

| Dataset | Sequence | Status | PSNR | SSIM | LPIPS | ATE cm | Scale err. % | Recall@10 cm % | Time s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| UT-MM | fast-straight | complete | 16.656 | .6211 | .5288 | 1.129 | .24 | 100.00 | 47.6 |
| UT-MM | slow-straight-1 | **failed** | — | — | — | — | — | — | 48.2 |
| UT-MM | slow-straight-2 | complete | 18.444 | .6611 | .4806 | 1.070 | 23.92 | 100.00 | 61.5 |
| UT-MM | square-2 | **tracking failure** | 16.588 | .5791 | .4897 | **179.303** | 14.01 | **1.37** | 96.0 |
| UT-MM | ego-centric-2 | complete | 17.436 | .5834 | .3487 | 6.213 | 7.69 | 100.00 | 101.7 |
| UT-MM | ego-drive | complete | 21.253 | .7144 | .3255 | 6.297 | .82 | 96.55 | 105.8 |
| UT-MM | ego-centric-1 | complete | 19.376 | .7100 | .2736 | 4.122 | 25.46 | 100.00 | 113.0 |
| UT-MM | square-1 | complete | 17.358 | .6244 | .3618 | 2.736 | 1.41 | 100.00 | 118.0 |
| RPNG | table_01 | complete | 20.419 | .6068 | .3401 | 2.244 | 3.53 | 100.00 | 170.6 |
| RPNG | table_06 | complete | **22.625** | .7526 | .2759 | 1.979 | 2.05 | 100.00 | 182.8 |
| RPNG | table_02 | complete | 16.796 | .4126 | .4423 | 4.121 | 2.73 | 97.58 | 199.2 |
| RPNG | table_07 | complete | 21.207 | .7282 | .2086 | 4.370 | .96 | 100.00 | 298.0 |
| RPNG | table_04 | complete | 18.463 | .5842 | .3035 | 3.817 | 3.25 | 100.00 | 377.6 |
| RPNG | table_05 | complete | 20.954 | .6703 | .3094 | 3.255 | 4.46 | 99.70 | 378.6 |
| RPNG | table_03 | complete | 18.173 | .4865 | .3807 | 3.640 | 3.65 | 100.00 | 432.2 |
| RPNG | table_08 | **weak tracking** | 19.527 | .6773 | .3788 | **16.191** | 5.51 | **61.57** | 513.4 |

| Aggregate over metric-producing runs | n | PSNR mean | SSIM mean | LPIPS mean | ATE mean / median cm | Recall mean % |
|---|---:|---:|---:|---:|---:|---:|
| UT-MM | 7 | 18.159 | .6419 | .4012 | 28.696 / 4.122 | 85.42 |
| RPNG | 8 | 19.770 | .6148 | .3299 | 4.952 / 3.729 | 94.86 |
| Combined | 15 | **19.018** | .6275 | .3632 | 16.032 / 3.817 | 90.45 |

The 15 completed runs consumed 3,196.1 s in total; including the failed attempt gives about 54.1 minutes. The best held-out rendering result is RPNG `table_06` at 22.625 dB. No sequence reaches 27 dB.

## Failure analysis and interpretation

`slow-straight-1` generated only 13 tracking keyframes, below the configured UT-MM IMU/mapping initialization threshold of 15. The Gaussian map remained empty, then the terminal mature-dust diagnostic indexed an empty one-dimensional opacity tensor and raised `IndexError`. This is recorded as an initialization/mapping failure rather than omitted from the denominator.

`square-2` returned exit code 0 and rendered a map, but 179.3 cm ATE and 1.37% recall constitute a tracking-metric failure. RPNG `table_08` is also weak at 16.2 cm ATE and 61.6% recall. UT-MM `slow-straight-2` and `ego-centric-1` show 23.9% and 25.5% scale error despite low Sim(3) ATE, demonstrating why scale must accompany the aligned ATE.

This establishes a runnable cross-dataset baseline and exposes generalization and initialization failures. It does not establish strict online 27 dB performance, strict zero-tail compliance, or a paper-table reproduction. A strict comparison needs a sensor-EOS snapshot that drops pending map work and an evaluator/split matching the paper protocol.

## Evidence

- [Per-sequence CSV](evidence/summary.csv)
- [Aggregate JSON](evidence/aggregate.json)
- raw result root: `results/benchmarks/fixed1p5_prefinal_queue_drain_v1/vigs_final_v7/2a3eeeb5_dirty_20260910`

