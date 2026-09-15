> 번호 통합(2026-09-11): 이 문서는 **exp77 단계 B**의 기록이다. 본문의 exp78는 이전 ID다. [통합 카드](../README.md)

# exp78 — Current-code Aria final-v7 reproduction

Date: 2026-09-10

## Verdict

**Aria final-map held-out 27 dB reproduced in 2/2 runs.** Current-code held-out
PSNR is 27.986900 / 27.861770 dB, mean **27.924335 dB**. This reproduces the
recent exp72/73 final-map baseline, not the historical exp57 freeze800 strict
sensor-EOS zero-tail recipe. No mapping code was modified.

## Reference and exact conditions

- Reference: exp72 `full_baseline_aria1253_seed0` and `full_baseline_repeat_aria1253_seed0`.
- Current source: `/home/intern/VIGS-SLAM-main-integration-20260828`, HEAD
  `2a3eeeb5b83743c642bbd7e5278817a4c76228ee` plus existing dirty changes.
- Dataset directory `aria1253` actually supplies **1,303 RGB frames** here.
- Original timestamp 1×; seed 0; RTX 5090; `vigs-slam-5090` environment.
- Validated RTX 5090 hardware profile: replay iters 4, standard B1 renderer,
  GPU image/input caches, dedicated GS stream, tracking overlap and slack packing.
- Legacy causal carve off; detached opacity off; baseline active/archive scheduler;
  maturity gate retained. Terminal dust-GC and terminal pose rematuration retained.
- Fixed held-out **262 images**, excluded from Gaussian mapping supervision.
  The saved YAML and exact fixed-eval frame IDs match the historical baseline
  in both new runs. Metric rendering reports `map_updates=0`.
- Runtime queues drain after tracking EOS; explicit terminal optimizer work is
  present. Protocol: `original1x_finalmap_queue_drain_terminal_rematuration`.
- GPU compute processes were checked before each run. Existing GUI processes
  were left running. Both attempts exited 0; held-out metrics determine acceptance.

## Results

| Run | Fixed held-out PSNR | Mixed eval PSNR | SSIM held-out | LPIPS held-out | Online loop s | Post-track s | Final replay updates | Explicit terminal updates | Final pool |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Historical 0 | 27.631508 | 27.693318 | .872162 | .235392 | 70.088 | 2.185 | 6229 | 328 | 405 |
| Historical 1 | 27.661030 | 27.722738 | .874397 | .233272 | 70.362 | 2.370 | 6125 | 384 | 428 |
| Reproduction 0 | 27.986900 | 28.033682 | .882536 | .218772 | 71.903 | 4.002 | 7372 | 904 | 403 |
| Reproduction 1 | 27.861770 | 27.933224 | .874714 | .232360 | 69.129 | 1.266 | 6395 | 40 | 464 |

Historical held-out mean is **27.646269 dB**; new mean is **27.924335 dB**
(+0.278066). The familiar 27.708028 dB number in exp72/73 is the historical
`mean_psnr` over the mixed evaluator set, not `fixed_eval_mean_psnr`.
This corrects its interpretation in the preceding discussion; it does not
invalidate the fact that historical held-out quality exceeded 27 dB.

Online time uses ONLINE_LOOP_START to ONLINE_LOOP_DONE; launcher durations
including startup, teardown and evaluation were 101.07 / 100.10 s.
Explicit terminal updates are a subset of post-sensor optimizer work; queue-drain
updates are not separately counted here. Final replay totals include terminal
work and must not be called streaming-only updates. Same-seed repetitions
vary in asynchronous scheduling, pool size, and termination workload. The
positive delta is not evidence of a newly implemented quality improvement.

## Implication for exp77

Current code can still deliver Aria 27 dB under the validated recent Aria recipe.
The 16-sequence result therefore does not demonstrate a general collapse of
Aria performance. It still leaves dataset transfer and execution-contract
mismatches unresolved.

The exp77 runner directly invokes `run_decoupled_geometry.sh`; it does not
explicitly load the validated RTX 5090 profile. Its explicit settings include
1.5× replay and disabled fnet/update TensorRT, whereas this reference uses 1×,
the validated profile, legacy carve off and terminal rematuration on.
Inherited exp77 environment was not fully captured, so exact historical profile
flags cannot all be reconstructed from the runner alone. The missing explicit
profile selection is a reproducibility issue and a plausible performance factor,
not an isolated causal explanation for the 8–9 dB cross-dataset gap.

Next useful comparison: keep dataset and evaluator fixed and compare explicitly
recorded profiles and EOS policies. No RPNG/UTMM rerun or new carve ablation was
performed in exp78. No region-GT floater evaluation was performed; this is a
rendering-quality reproduction only.

## Reproduction and evidence

```bash
cd /home/intern/VIGS-SLAM-main-integration-20260828
bash exp72_axes/run_scheduler_ablation.sh aria1253 /absolute/new/output baseline
```

The actual driver clears inherited EXP69/70/72/73 and VIGS environment overrides
before executing the wrapper. Full commands, return codes, source diff,
untracked regular-source archive, source status, runner/config hashes, logs,
PLYs and evaluation JSONs are preserved under:
`results/experiments/exp78_aria_reproduction_20260910/`.

- [Metric summary](evidence/summary.json)
- [Configuration and frame-ID checks](evidence/comparison_checks.json)
- [Source provenance](evidence/provenance.json)
