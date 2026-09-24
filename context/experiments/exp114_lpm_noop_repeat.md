# Exp114 — official LPM no-op repeat gate

Date: 2026-09-24

## Question and protocol

Exp113 failed only an exact PLY-byte gate. Exp114 brackets the same LPM probe
with two newly executed untouched controls. The source, archive, causal input,
physical renders, Adam updates, admissions, topology events, held-out set, and
zero-tail contract are fixed. Exact PLY SHA is diagnostic, not a gate; the
predeclared topology tolerance is 0.1% of the two-control mean.

## Result — UTMM square-1

| Arm | PSNR | SSIM | LPIPS | Renders | Adam | GS | Wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| control A | 21.223234 | 0.715732 | 0.340931 | 9,345 | 757 | 120,137 | 40.475 |
| LPM probe | 21.225550 | 0.715801 | 0.341525 | 9,345 | 757 | 120,195 | 40.328 |
| control B | 21.223577 | 0.716448 | 0.340719 | 9,345 | 757 | 120,235 | 39.936 |

- Control PSNR spread: 0.000343 dB
- Probe minus control mean: +0.002144 dB
- Probe GS deviation from control mean: 9 / allowed 121
- Measured LPM GPU share: 0.187%
- Probe mapping-wall delta from control mean: +0.306%
- Score min/mean/max/std: 0.103583/0.242299/0.368564/0.059700
- 142 calls, 72 unique views, 70 repeats, 36 views seen at least twice,
  95 distinct scores

All physical-work, causal, evaluator, signal, cost, and topology-tolerance
checks pass. The three PLY hashes differ, including the two controls, proving
that exact byte identity is not a valid no-op criterion for this CUDA/topology
path.

## Verdict

**PASS.** The exact author-code error-zone primitive is cheap,
non-degenerate, and behavior-neutral at the tested fixed-work point. This
permits a subsequent experiment in which its detached score becomes a bounded
dense-view scheduling utility. It does not yet show a quality gain and does
not justify importing LPM's offline LightGlue/triangulation pipeline or using
the score for hard pruning.

Artifacts:
`results/experiments/exp114_lpm_noop_repeat/utmm/square-1/`.
