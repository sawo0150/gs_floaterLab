# Exp119 — corrected exact-render unified dense global slot

Date: 2026-09-24

## Method

Exp118's early-pool supplement bug is corrected by freezing the number of
global renders that the control can actually afford at each iteration:

```text
G       = min(n_global_views, available_historical)
dense   = min(1, G, available_dense)
tracked = G - dense
```

The recent keyframe window is untouched. The one dense replacement is drawn
transactionally from the same LPM-mass normalized-variance pool used by the
two fixed dense replay slots. It contributes RGB gradient and native
visibility/densification statistics inside the existing multi-view Adam step.
The replacement updates view-service counts but explicitly does not advance
the topology controller's D1 lifecycle clock.

## Result — UTMM square-1

| Arm | PSNR | Delta | SSIM | LPIPS | Dense renders/share | Total renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mass normalized control | 21.220422 | 0 | 0.716066 | 0.341520 | 142 / 1.52% | 9,345 | 757 | 120,132 |
| unified mass + normalized ERCB | 21.208358 | -0.012064 | 0.716294 | 0.341234 | **625 / 6.69%** | 9,345 | 757 | 120,736 |
| unified mass-only RR | 21.182736 | -0.037685 | 0.715337 | 0.344014 | **625 / 6.69%** | 9,345 | 757 | 120,684 |

The two unified arms committed exactly 483 global replacements. Every one had
LPM evidence; `142 + 483 = 625` dense renders exactly. Normalized and RR chose
different global dense identities on 70 rows. Every ledger row satisfies the
corrected cardinality equation, keeps the recent window, avoids the cap, and
commits its optimizer update. Archive/config/event/render/Adam/admission,
held-out, double-evaluation, zero-tail, and lifecycle parity all pass.

## Verdict

**PASS.** Dense supervision now owns 4.4x more physical renders and participates
in native mapping/topology statistics without adding work or materially losing
quality. Normalized ERCB is +0.02562 dB above the matching RR arm, but this is
still a single-scene noise-scale result rather than a quality contribution.
The exact one-slot rule and formula are frozen for RPNG table_01 and Aria1253
transfer. Any -0.5 dB drop or parity failure stops expansion.

Artifacts:
`results/experiments/exp119_unified_dense_global_corrected/utmm/square-1/`.
