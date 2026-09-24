# Exp117 — frozen LPM mass-prior transfer

Date: 2026-09-24

## Protocol

Exp116's development formula was frozen before looking at RPNG or Aria:

\[
q_i=\frac{a_i+256}{H_iW_i+256},\qquad
p_i\propto q_i\exp[-16n_i/(T+1)].
\]

No coefficient, gamma, phase, or scene/dataset condition was changed. RPNG
`table_01` ran first; any activity, fairness, or -0.5 dB quality-floor failure
would have stopped before Aria1253. Each arm was newly mapped and evaluated
twice on the fixed held-out manifest.

## Results

| Dataset / scene | Arm | PSNR | Delta | SSIM | LPIPS | Trace rows changed | Renders | Adam | GS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG / table_01 | normalized control | 25.586171 | 0 | 0.847770 | 0.153696 | 0 | 38,302 | 3,030 | 417,928 |
| RPNG / table_01 | LPM mass + normalized ERCB | 25.575404 | -0.010767 | 0.847315 | 0.153703 | **34** | 38,302 | 3,030 | 417,980 |
| RPNG / table_01 | LPM mass-only RR | 25.583380 | -0.002790 | 0.847318 | 0.153865 | **40** | 38,302 | 3,030 | 417,873 |
| Aria / aria1253 | normalized control | 25.726881 | 0 | 0.825140 | 0.319459 | 0 | 13,620 | 1,055 | 177,273 |
| Aria / aria1253 | LPM mass + normalized ERCB | 25.757892 | +0.031011 | 0.824978 | 0.319542 | **9** | 13,620 | 1,055 | 177,202 |
| Aria / aria1253 | LPM mass-only RR | 25.749919 | +0.023038 | 0.825822 | 0.317568 | **15** | 13,620 | 1,055 | 177,123 |

All work, input, causal, held-out, double-evaluation, zero-tail, source, and
transactional checks pass. Including the Exp116 development scene, the
normalized mass prior is active on all three dataset families with deltas
`-0.0090/-0.0108/+0.0310 dB`; their arithmetic mean is **+0.0038 dB**.
Against the corresponding mass-only RR arms, normalized ERCB changes quality
by `-0.0121/-0.0080/+0.0080 dB`, mean **-0.0040 dB**.

## Verdict

**PASS for untuned activity and quality preservation; quality gain remains
unproven.** This is now a faithful active implementation path: downloaded LPM
code supplies the residual-zone evidence, normalized variance supplies the
explicit count energy, and both alter real dense service without additional
physical work. It should not be advertised as the cause of the current R4
PSNR gain: the effect is noise-level and dense work is still only the two
one-view fixed slots (about 1.4--1.5% of renders).

A 17-scene repeat is not the next informative experiment. The next causal
step is fixed-render source reallocation: keep the recent native keyframe
window intact, but replace a predeclared flexible historical-keyframe render
slot with a draw from the unified causal dense/ERCB pool. This raises dense
leverage without adding rendering or Adam steps; it must first pass the same
three-family stop gates.

Artifacts:
`results/experiments/exp117_lpm_mass_transfer/`.
