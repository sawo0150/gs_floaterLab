> 번호 통합(2026-09-11): 이 문서는 **exp77 단계 C**의 기록이다. 본문의 exp79는 이전 ID다. [통합 카드](../README.md)

# exp79 — Aria fixed 1× sensor-EOS optimizer zero-tail

Date: 2026-09-10

## Verdict

User-requested **fixed 1× mapping optimizer budget and zero optimizer updates
following the final sensor frame** passed in both evaluated runs. Held-out
PSNR was **26.177473 / 27.498561 dB**, mean **26.838017 dB**. Only 1/2 runs
exceeded 27 dB, with a 1.321087 dB range: stable 27 dB reproduction fails.

This is an optimizer-cutoff diagnostic of current final-v7, not the historical
exp57 freeze800 recipe and not an end-to-end latency certification.

## Setup

- Same Aria directory and 1,303 frames as exp78; fixed held-out 262 frame IDs
  exactly match exp78, with Gaussian mapping supervision exclusion true.
- RTX5090 validated profile, original timestamp 1×, seed 0 in both repeats.
- Legacy causal carve and detached opacity remain off.
- **Terminal pose rematuration and terminal dust pruning disabled.** Logs have
  no terminal rematuration/prune action and report pruning events 0.
- Opt-in `VIGS_SENSOR_EOS_ZERO_TAIL=1`; existing behavior is retained without it.
- Source HEAD `2a3eeeb5` plus pre-existing dirty changes and the saved exp79 diff.
- No MPS input was introduced. Existing RGB/IMU input and online pose/depth
  estimation remain in use. Only the replay harness uses first/last timestamp
  metadata to enforce the fixed budget; future RGB/pose/depth is not supervised.

## Measured results

| Repeat | Held-out PSNR | Held-out SSIM | Held-out LPIPS | 1× budget s | Last optimizer completion s* | Adam calls completed | Updates after budget | Updates after sensor EOS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 26.177473 | .862993 | .253386 | 65.099999 | 65.049690 | 6537 | **0** | **0** |
| 1 | 27.498561 | .869655 | .234221 | 65.099999 | 65.050772 | 6895 | **0** | **0** |

`*` Relative to the producer's monotonic replay start, not consumer queue drain.
The counts cover actual guarded Adam calls (mapping initialization, replay,
exposure, etc.); they must not be equated with replay-only scheduler counters.
One late Adam attempt was skipped in repeat 0; none in repeat 1.

## Cutoff implementation and validation

`vigs/sensor_eos_guard.py` wraps Adam.step only for this opt-in run. Source audit
found that the mapper's Gaussian/camera/exposure/birth optimizers use Adam.
The producer publishes its monotonic replay start, fixed deadline and final
sensor emission time in shared memory. Step starts are rejected after deadline
minus a fixed **50 ms safety margin**, or when producer EOS is already set.
Each accepted step synchronizes its current CUDA stream and records a CPU
completion timestamp, a conservative upper bound on GPU completion.

`vigs/vigs.py` stops admitting new mapping packets and discards queued packets
without processing once the cutoff is reached; idle replay is suppressed too.
Already-running mapping functions may finish bookkeeping, but late Adam calls
are skipped. The guard remains installed during read-only evaluation. Audits
are written after worker shutdown and again after final evaluation; both
completed runs have zero completion timestamps past either boundary. A step
that starts before the cutoff but finishes late causes audit failure rather
than being reported as compliant. The 50 ms margin is not a worst-case execution
time proof; the zero-tail conclusion is based on recorded completion times for
these runs, and every future run must pass its own audit.

Changes: opt-in integration in `demo.py` / `vigs/vigs.py`, new guard module.
Python compile checks pass. Three CPU boundary tests check no updates before
clock initialization, cutoff/EOS rejection, and detection of an in-flight step
whose completion crosses the deadline. Two real CUDA runs complete evaluation
and pass the final audits. Source hashes/diff were unchanged during those runs.

## Interpretation and limits

- exp78 with post-stream rematuration averaged **27.924335 dB**; exp79 is
  **1.086318 dB lower** on average. This is not an isolated causal estimate of
  tail-training benefit: terminal pruning, cutoff behavior and per-step CUDA
  synchronization differ, and asynchronous schedule/topology varies.
- CUDA synchronization costs time inside the 1× budget. This is a conservative,
  instrumented baseline, not evidence of the best achievable native zero-tail
  performance. Optimizing the monitor while retaining reliable completion audits
  is a possible follow-up, not a completed result.
- Only mapping optimizer updates are certified against the sensor/budget clock.
  VIO tracking, in-flight bookkeeping, trajectory filling, diagnostics, map
  export and evaluation may finish later. ONLINE_LOOP wall times including
  process startup and diagnostics were **68.945 / 68.894 s**, and launch-to-exit
  times were **100.16 / 99.77 s**. Do not claim the entire pipeline finishes in
  65.10 s or that no non-optimizer state can change after EOS.
- No post-stream optimizer training or terminal pruning is performed. Region-GT
  floater evaluation was not run; this is a held-out rendering experiment.
- Two startup attempts failed before sensor execution (an integration indentation
  error and an existing terminal-simple-policy validation dependency). Both were
  fixed, their logs retained in `failed_startup/` and `failed_startup2/`, and they
  are not counted among the two evaluated quality runs.

## Reproduction

```bash
cd /home/intern/VIGS-SLAM-main-integration-20260828
VIGS_SENSOR_EOS_ZERO_TAIL=1 bash exp72_axes/run_scheduler_ablation.sh \
  aria1253 /absolute/new/output baseline
```

The actual driver clears inherited EXP69/70/72/73 and VIGS overrides before
setting the opt-in. Wrapper startup messages still show profile defaults;
`SENSOR_EOS_CONFIG` records effective overrides in demo.py. All logs, maps,
optimizer timestamps, source backups, before/after patches, tests, driver and
summary code are retained in:
`results/experiments/exp79_aria_1x_zero_tail_20260910/`.

- [Summary](evidence/summary.json)
- [EOS audit 0](evidence/sensor_eos_audit_repeat0.json)
- [EOS audit 1](evidence/sensor_eos_audit_repeat1.json)
- [Provenance](evidence/provenance.json)
