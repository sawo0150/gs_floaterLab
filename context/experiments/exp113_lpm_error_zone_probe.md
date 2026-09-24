# Exp113 — official LPM error-zone probe (failed over-strict gate)

Date: 2026-09-24

## Question

Can the exact image-space error-zone primitive from the downloaded LPM author
implementation be measured on an already-paid causal dense render without
changing physical work or mapper behavior?

## Source-backed implementation

- Author repository: `Surrey-UPLab/Localized-Gaussian-Point-Management`
- Pinned commit: `7c060267cf55df76992e9ef2b6df42133ba9349f`
- Ported operator: `lpm/utils.py::get_errormap(diff)` only
- Constants preserved: mean epsilon 0.01, quantile 0.4, 16x16 patches,
  significant-pixel fraction 0.85
- Unit tests compare the port against a literal isolated copy of the author
  operation, including a non-multiple-of-16 image size.

LightGlue, all-pair matching, triangulation, topology mutation, extra renders,
and extra Adam updates are explicitly absent. The probe is telemetry-only and
uses the prediction/GT pair already produced by a paid dense update.

## Result — UTMM square-1

| Arm | PSNR | SSIM | LPIPS | Renders | Adam | GS | Wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| control | 21.218693 | 0.716176 | 0.341625 | 9,345 | 757 | 120,105 | 40.148 |
| LPM probe | 21.225969 | 0.715884 | 0.340801 | 9,345 | 757 | 120,110 | 41.322 |

- PSNR delta: +0.007276 dB
- LPM GPU time / mapping wall: 0.211%
- Mapping-wall delta: +2.924%
- Signal: 142 calls, 72 unique views, 36 repeated views, 95 distinct scores
- Score min/mean/max/std: 0.105992/0.242393/0.369768/0.059340
- Render, Adam, archive, config, event, admission, dense-selection,
  held-out, double-evaluation, and zero-tail checks: PASS

## Verdict

**FAIL**, solely because the predeclared exact saved-PLY SHA check failed.
This failure is retained rather than rewritten. The count difference was only
five Gaussians and every work/trace check passed, suggesting nondeterministic
CUDA/topology ordering rather than a semantic side effect. Exp114 therefore
repeated the control on both sides and replaced byte identity with a
predeclared 0.1% Gaussian-count tolerance plus quality/work checks.

Artifacts:
`results/experiments/exp113_lpm_error_zone_probe/utmm/square-1/`.
