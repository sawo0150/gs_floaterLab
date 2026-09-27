# exp111 — first-service floor and dense-repeat ERCB isolation

- Date: 2026-09-24
- Status: **PASS for dense-repeat quality preservation; ERCB gain unproven**
- Source-locked lab commit: `3c9d34a`
- Source-locked VIGS commit: `d49a29aa`
- Runner: `benchmarks/online_gs/run_exp111_dense_repeat_ercb.py`
- Artifact verifier: `benchmarks/online_gs/report_exp111_dense_repeat_ercb.py`
- Results: `results/experiments/exp111_dense_repeat_ercb/`
- Official summary: [three-family table](benchmark_custom/exp111_dense_repeat_ercb_20260924/summary.md)

## Why this experiment

Exp110 showed that dense and auxiliary-KF service were effectively one-pass,
so normalized-variance ERCB produced exactly the same dense/auxiliary choices
as RR. Adding renders would break the B-track contract, while replacing native
historical slots had already harmed final-v7 in prior experiments. Exp111
therefore reallocates only the existing auxiliary-keyframe one-view slot:

1. the primary dense slot alone advances compute-paced admission;
2. every newly admitted view receives a hard causal first service;
3. the former auxiliary-KF slot becomes a flexible dense repeat;
4. repeat sampling uses the exact normalized potential
   `p_i ∝ exp[-log(1.5)n_i/(T+1)]`;
5. R4 birth/prune/native topology/recent-window work and the dense-evidence
   first-persistence ticket remain unchanged.

The dense-only RR control sets the dense Gibbs energy to zero while native-KF
selection remains normalized, avoiding the native-selector confound measured
in Exp110.

## Result

| Scene | R4 | Normalized repeat | Dense RR | N−R4 | N−RR | Repeat draws | Different rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| UTMM square-1 | 21.213002 | 21.220787 | 21.224967 | +0.007784 | -0.004181 | 69 | 1 |
| RPNG table_01 | 25.581742 | 25.565026 | 25.572162 | -0.016716 | -0.007136 | 265 | 2 |
| Aria aria1253 | 25.722904 | 25.777053 | 25.736435 | +0.054149 | +0.040618 | 99 | 0 |
| **Mean** | — | — | — | **+0.015072** | **+0.009767** | — | — |

Dense/KF one-view service changes from 70/70→140/0, 267/267→534/0,
and 100/100→200/0. Physical renders and Adam steps are exactly 9,345/757,
38,302/3,030, and 13,620/1,055 in every paired arm. Registered dense UIDs,
event IDs, config/archive hashes, held-out exclusion, double evaluation, and
zero-tail all match. Candidate dense render share doubles from about 0.7% to
1.4–1.5% without increasing total work.

## Finding and decision

The reallocation creates genuine dense repeats and preserves the R4 quality
base on all three dataset families. It is a viable Track-A structural change.
It is not yet an ERCB result: the exact normalized coefficient decays as
`1/(T+1)`, and `gamma=log(1.5)` changes only three rows across all three
scenes. The N−RR metric is therefore noise-level even though its mean is
positive.

Use a new development-only temperature experiment to select one common
constant `gamma` by selection-divergence and quality gates, then freeze it for
transfer. Do not scale `gamma` with service count, because that would cancel
the normalization and recreate the raw-variance sampler under a new name.

## Reporting incident

The immutable runner's inline verifier falsely failed after all work completed:
it compared selector snapshots instead of slot-work skeletons and a cumulative
primary clock against a final-generation counter. The separate artifact-only
v2 verifier corrects only those comparisons and passes every scene. Original
inline failure reports are retained; no run was overwritten or reused under a
changed source lock.
