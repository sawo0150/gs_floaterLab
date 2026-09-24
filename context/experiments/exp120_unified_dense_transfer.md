# Exp120 — frozen exact-render unified dense transfer

Date: 2026-09-24

## Question

Exp119 increased dense supervision on UTMM without adding physical work. This
experiment asks whether the exact same rule transfers to RPNG and Aria without
scene retuning or a quality collapse.

The implemented primitive remains source-backed: dense-view utility uses the
16x16 significant-error-zone operator ported from the downloaded LPM author
repository at commit `7c060267`. The queue composition and transactional
publication rule are ours, not an LPM-author claim.

## Frozen method

The LPM mass prior and normalized-variance ERCB law are unchanged from
Exp116--119:

```text
q_i = (active_pixels_i + 256) / (H_i W_i + 256)
p_i proportional to q_i * exp[-16 n_i / (T + 1)]
```

The recent keyframe window is untouched. At each native mapping iteration the
control-equivalent historical cardinality is fixed first, and at most one real
historical render is replaced by one dense draw:

```text
G       = min(n_global_views, available_historical)
dense   = min(1, G, available_dense)
tracked = G - dense
```

The dense view participates in the existing multi-view Adam step and therefore
contributes full RGB gradients and native visibility/densification statistics.
It does not add an Adam step or render, and it does not advance the D1 topology
lifecycle clock. The formula, `gamma=16`, slot count, stop line, and dataset
order were frozen from Exp119 before either transfer result was read.

## Results

| Dataset / scene | Arm | PSNR | Delta vs control | SSIM | LPIPS | Dense renders/share | Total renders | Adam | GS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG / table_01 | mass normalized control | 25.579600 | 0 | 0.847415 | 0.153944 | 538 / 1.40% | 38,302 | 3,030 | 417,830 |
| RPNG / table_01 | unified mass + normalized ERCB | 25.393478 | -0.186122 | 0.839563 | 0.165048 | **2,148 / 5.61%** | 38,302 | 3,030 | 419,055 |
| RPNG / table_01 | unified mass-only RR | 25.425005 | -0.154595 | 0.840430 | 0.163714 | **2,148 / 5.61%** | 38,302 | 3,030 | 418,769 |
| Aria / aria1253 | mass normalized control | 25.726313 | 0 | 0.824738 | 0.319123 | 202 / 1.48% | 13,620 | 1,055 | 177,100 |
| Aria / aria1253 | unified mass + normalized ERCB | 25.780710 | +0.054396 | 0.827268 | 0.320940 | **867 / 6.37%** | 13,620 | 1,055 | 177,883 |
| Aria / aria1253 | unified mass-only RR | 25.772388 | +0.046075 | 0.826828 | 0.322628 | **867 / 6.37%** | 13,620 | 1,055 | 177,897 |

RPNG committed 1,610/1,610 replacements and Aria committed 665/665. The
normalized and RR global selections differ on 141 and 82 ledger rows,
respectively. Every replacement has committed LPM evidence.

Including Exp119 UTMM, the three-family arithmetic result is:

| Quantity | Result |
|---|---:|
| Control mean PSNR | 24.175445 dB |
| Unified normalized mean PSNR | 24.127515 dB |
| Unified normalized - control | **-0.047930 dB** |
| Unified normalized - unified RR | **+0.000805 dB** |
| Mean dense share, control -> unified | **1.47% -> 6.22%** |
| Total committed global replacements | 2,758 |
| Normalized/RR trace-difference rows | 293 |

The native topology ledger also changes because the reallocated dense views
now contribute native visibility/densification statistics. For example, RPNG
regular lifetime additions increase from 31,751 to 33,471 and final Gaussian
count from 417,830 to 419,055. This is an active topology path, not just an
appearance-only counter. The separate first-persistence ticket still observes
only the dedicated dense slots (`dense_observations` is unchanged), so these
extra global renders must not be attributed to that ticket.

## Verification

- all three arms use the same frozen archive, config, dense admissions, and
  event sequence;
- physical renders and Adam steps match exactly within each scene;
- held-out sets are disjoint from mapping supervision;
- saved maps reproduce under a second evaluation;
- zero-tail is satisfied;
- recent-window/cardinality/cap/transactional/lifecycle ledgers all pass;
- neither transfer crosses the predeclared -0.5 dB stop line.

## Verdict

**PASS for active, exact-work, quality-safe transfer.** Dense service is now
roughly 4.2x more prevalent and affects actual optimization/topology while the
R4 quality floor remains intact across UTMM, RPNG, and Aria.

This is **not** evidence that ERCB causes a PSNR gain: the normalized-vs-RR
three-family mean is only +0.000805 dB. RPNG also loses 0.186 dB versus its
fresh control, so the present one-slot rule should not be promoted as a new
quality-improving 17-scene result. The next experiment must make the extra
dense work more useful using a primitive taken from a pinned downloaded author
implementation; quality-guided scene tuning and paper-only reimplementation
remain prohibited.

Artifacts:
`results/experiments/exp120_unified_dense_transfer/`.
