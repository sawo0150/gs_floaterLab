# Exp115 — source-backed LPM dense-view utility (inactive composition)

Date: 2026-09-24

## Question

Can the exact LPM error-zone coverage become an explicit dense-view utility
while preserving normalized-variance ERCB, fixed physical work, and the R4
quality floor?

The predeclared composition was

\[
p_i \propto (1+e_i)\exp[-16n_i/(T+1)],
\]

where `e_i` is produced by the downloaded LPM author operation. The `1+e_i`
base measure is bounded in `[1,2]`; it was selected analytically rather than by
PSNR. A second arm removed the count energy to isolate the utility prior.

The score was staged only after a successful Adam update and became visible
together with `commit_pending_draw`; cancellation discarded it. No extra
render, Adam step, topology mutation, future input, or scene/dataset knob was
allowed.

## Result — UTMM square-1

| Arm | PSNR | Delta | SSIM | LPIPS | Trace rows changed | Renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| normalized control | 21.234035 | 0 | 0.715966 | 0.340895 | 0 | 9,345 | 757 | 120,199 |
| LPM probe control | 21.228204 | -0.005831 | 0.716566 | 0.341203 | 0 | 9,345 | 757 | 120,212 |
| LPM + normalized utility | 21.214362 | -0.019673 | 0.715712 | 0.341833 | **0** | 9,345 | 757 | 120,108 |
| LPM utility-only RR | 21.236992 | +0.002957 | 0.716184 | 0.340900 | **9** | 9,345 | 757 | 120,129 |

All four arms passed archive/config/event/render/Adam/admission, held-out,
double-evaluation, and zero-tail checks. Both utility arms consumed all 142
LPM scores transactionally and ended with no pending score. The source commit
was `7c060267`; LightGlue and triangulation remained disabled.

## Verdict

**FAIL**, because the normalized+utility arm changed zero dense selection
rows. It is quality-safe at this point (`-0.0197 dB`, well inside the `-0.5`
dB stop line), but it is not an active method and cannot support a causal LPM
or dense-utility claim. The utility-only arm changed 9 rows but its
`+0.0030 dB` is noise-level, so it also supplies no quality-gain evidence.

The evidence is diagnostic: the uniform unit mass in `1+e_i` diluted the LPM
coverage range enough that the already-active `gamma=16` normalized-count
term and the same Gumbel draws selected exactly the control views. The next
candidate must change the *prior definition* for a source-grounded reason,
not tune a multiplier on PSNR. A defensible option is the LPM significant-zone
mass with a one-patch pseudocount,
`q_i=e_i+1/P_i`, used in `p_i proportional to q_i exp(...)`; it should first
pass a trace-only/quality-stop development gate before any transfer.

Artifacts:
`results/experiments/exp115_lpm_view_utility/utmm/square-1/`.
