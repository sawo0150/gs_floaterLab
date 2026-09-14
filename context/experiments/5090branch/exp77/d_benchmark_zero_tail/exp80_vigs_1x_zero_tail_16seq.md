> 번호 통합(2026-09-11): 이 문서는 **exp77 단계 D**의 기록이다. 본문의 exp80는 이전 ID다. [통합 카드](../README.md)

# exp80 — RPNG/UT-MM fixed 1× sensor-EOS optimizer-zero-tail benchmark

Date: 2026-09-10. Status: **16 attempted, 13 evaluated, 3 failed. Queue ended.**

## Outcome

All 13 evaluated runs pass the instrumented 1× mapping-optimizer cutoff and
sensor-EOS zero-tail audits. None reaches held-out 27 dB. This establishes the
requested baseline, not a successful quality result or an end-to-end latency
certification. UTMM square-2 remains a tracking-metric failure despite producing
rendering metrics.

| Dataset | Attempted | Evaluated | Held-out mean dB | Matched exp77 mean dB | Paired delta dB | ATE median cm |
|---|---:|---:|---:|---:|---:|---:|
| utmm | 8 | 7 | **15.794** | 18.159 | -2.364 | 4.034 |
| rpng | 8 | 6 | **18.986** | 19.572 | -0.585 | 3.573 |
| all | 16 | 13 | **17.268** | 18.811 | -1.543 | 3.655 |

Means are unweighted across evaluated sequences. Paired comparisons use only
identical metric-producing sequences; exp77's original 15-sequence 19.018 dB
mean is not the denominator for the new 13-sequence comparison. Failures remain
in the 16-sequence attempt count. Best new result: table_06, **21.442 dB**.

| Dataset | Sequence | Status | Held-out dB | vs exp77 dB | ATE cm | Recall@10cm % |
|---|---|---|---:|---:|---:|---:|
| rpng | table_01 | evaluated | 20.250 | -0.169 | 2.222 | 100.00 |
| rpng | table_02 | evaluated | 16.644 | -0.152 | 4.127 | 97.88 |
| rpng | table_03 | evaluated | 17.381 | -0.793 | 3.655 | 100.00 |
| rpng | table_04 | evaluated | 17.041 | -1.422 | 3.853 | 100.00 |
| rpng | table_05 | evaluated | 21.161 | +0.206 | 3.491 | 100.00 |
| rpng | table_06 | evaluated | 21.442 | -1.182 | 2.746 | 100.00 |
| rpng | table_07 | **failed** | — | — | — | — |
| rpng | table_08 | **failed** | — | — | — | — |
| utmm | ego-centric-1 | evaluated | 19.125 | -0.251 | 4.034 | 100.00 |
| utmm | ego-centric-2 | evaluated | 17.980 | +0.544 | 5.387 | 100.00 |
| utmm | ego-drive | evaluated | 20.976 | -0.277 | 7.594 | 89.66 |
| utmm | fast-straight | evaluated | 4.896 | -11.761 | 1.127 | 100.00 |
| utmm | slow-straight-1 | **failed** | — | — | — | — |
| utmm | slow-straight-2 | evaluated | 18.348 | -0.096 | 1.070 | 100.00 |
| utmm | square-1 | evaluated | 13.589 | -3.769 | 2.722 | 100.00 |
| utmm | square-2 | evaluated | 15.648 | -0.940 | 92.761 | 2.74 |

## Exact execution contract

- Current VIGS HEAD `2a3eeeb5` plus existing dirty source and exp79 cutoff module.
  Source tracked diff unchanged across this run; runtime files and hashes saved.
- Same ETH-preprocessed inputs, dataset-specific calibration/IMU initialization
  settings and every-fifth-plus-final held-out IDs as exp77. Exact held-out IDs
  match in every evaluated pair; mapping exclusion is true.
- Validated RTX5090 profile, replay iters 4, original timestamp **1×**, seed 0.
- Legacy causal carve off, detached opacity off, terminal rematuration **off**,
  terminal pruning **off**. Effective overrides are printed by SENSOR_EOS_CONFIG;
  wrapper startup lines still show pre-override profile defaults.
- Aria-shape fnet/update TensorRT disabled for benchmark resolutions, as in exp77.
  Omnidata TRT retained. Environment: `vigs-slam-5090`.
- Exact exp79 guard: 50 ms admission safety margin, current-CUDA-stream completion
  synchronization per accepted Adam step, producer deadline and EOS timestamps.
  All 13 final audits have zero completed Adam steps beyond either boundary.
- Pending packets after cutoff are discarded without optimization; active
  mapper bookkeeping, tracking/PGBA, export and evaluation can finish later.
  Only mapping Adam update completion is certified, not all post-EOS state changes
  or total pipeline latency. Synchronization costs time inside the live budget.
- No per-sequence quality retuning or failed-run parameter retries were performed.
  GPU compute occupancy was checked before sequence launches; GUI processes stayed.

## Failures and operational handling

1. **UTMM slow-straight-1**: 13 KF < 15 initialization threshold; empty map.
   The diagnostic code raises IndexError on empty opacity. No rendering result.
2. **RPNG table_07**: CUDA gather index assertion during PGBA around frame 1697
   (35%). Traceback traverses pgo_buffer / factor_graph / depth_video; asynchronous
   CUDA reporting prevents precise bad-index localization from this trace alone.
3. **RPNG table_08**: OOM around frame 7719 (91%) in frontend correlation-pyramid
   concatenation. Requested ~1004 MiB with ~599.5 MiB device free; process memory
   ~27.63 GiB, allocated PyTorch ~18.90 GiB, reserved-unallocated ~7.22 GiB.

The latter two left owned processes alive after fatal errors. Only their verified
run process trees were terminated; manifests record nonzero exits and cleanup
JSONs preserve the reason/PIDs. They were not reported as successful zero-tail
runs and were not silently dropped.

An initial queue-driver invocation used system Python, so the first completed
SLAM/render run hit `numpy` import failure during CPU trajectory aggregation.
The trajectory evaluation was recovered in the correct conda environment without
retraining. Its launcher elapsed time was not persisted and is recorded null.
The remaining queue used the correct environment and skipped that completed run.
The original error remains in queue.log.

## Root-cause finding and follow-up scope

See [full code/log analysis](exp80_root_cause_analysis.md).

The strongest confirmed configuration mismatch is **40 ms tracking reserve on
~30 fps (33 ms) benchmark streams**. It blocks the intended tracking/replay
overlap: all 13 evaluated benchmark runs record zero overlap gate admissions,
versus 710/675 in the two exp79 Aria runs (~20 fps). Short UTMM initialization
also begins only after ~73–76% of the stream in two examples. Together with
larger maps, this leaves substantially fewer effective replay opportunities.
The magnitude of each cause's PSNR effect is not yet isolated.

Per user instruction, future iterations should use **Aria1253, table_06 and
fast-straight** as the primary small diagnostic set. Start with a matched overlap
reserve ablation; do not rerun all 16 for each candidate. Keep table_02 for a later
transfer check and table_07 for separate short-prefix stability debugging.
No new follow-up training ablation was launched after this benchmark.

## Artifacts / reproduction

- [Aggregate JSON](evidence/aggregate.json)
- [All-attempt comparison CSV](evidence/comparison.csv)
- [Raw-style successful-run CSV](evidence/summary.csv)
- [All 13 optimizer audits](evidence/sensor_eos_audits.json)
- [Telemetry diagnostics](evidence/diagnostics.json)
- [Source/split checks](evidence/checks.json)

Raw run root:
`results/benchmarks/fixed1x_sensor_eos_zero_tail_v1/vigs_final_v7_5090_clean/exp80_2a3eeeb5_dirty_20260910`.
Approximately 637 MiB of artifacts; disk free ~460 GiB at completion.

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/run_vigs_1x_zero_tail_16.py
# Select future diagnostics instead of default full set:
# --only rpng/table_06 --only utmm/fast-straight
```

The existing runner skips completed/recorded-failure outputs; a different
configuration must use a new runset/output root and record its own provenance.
Do not treat --retry-failed as permission to overwrite failure evidence.
