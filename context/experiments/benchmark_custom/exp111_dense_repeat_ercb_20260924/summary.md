# Exp111 — first-service floor + dense repeat ERCB isolation

The candidate replaces the existing auxiliary-keyframe one-view slot
with a dense repeat slot. It adds no render or Adam step. Only the
primary dense service mints admission credit; every newly admitted
view receives a hard first service, then repeat slots use the
normalized-variance Gibbs law over the admitted pool.

| Scene | R4 | Dense repeat N | Dense repeat RR | N-R4 | N-RR | Dense trace diff | Repeat/count range | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| utmm/square-1 | 21.213002 | 21.220787 | 21.224967 | +0.007784 | -0.004181 | 1 | 69/0-6 | PASS |
| rpng/table_01 | 25.581742 | 25.565026 | 25.572162 | -0.016716 | -0.007136 | 2 | 265/0-7 | PASS |
| aria/aria1253 | 25.722904 | 25.777053 | 25.736435 | +0.054149 | +0.040618 | 0 | 99/0-7 | PASS |

Completed scenes: **3/3**.
Mean dense-repeat minus R4: **+0.015072 dB**.
Mean normalized minus dense-only RR: **+0.009767 dB**.

## Work and service accounting

| Scene | Render / Adam (all arms) | Control dense/KF | Candidate dense/KF | First/repeat | Dense render share control→candidate |
|---|---:|---:|---:|---:|---:|
| UTMM square-1 | 9,345 / 757 | 70/70 | 140/0 | 71/69 | 0.75%→1.50% |
| RPNG table_01 | 38,302 / 3,030 | 267/267 | 534/0 | 269/265 | 0.70%→1.39% |
| Aria aria1253 | 13,620 / 1,055 | 100/100 | 200/0 | 101/99 | 0.73%→1.47% |

The candidate did not add work. It replaced every existing auxiliary-keyframe
one-view Adam/render with a dense repeat. The primary dense-service clock and
registered UID list remain identical to control, so repeat work cannot mint
extra views. All 9 arms pass frozen archive/config/event, equal render/Adam,
equal admission, held-out disjointness, double evaluation, and zero-tail
checks. The first-persistence topology ticket adds no render or Adam step.

## Interpretation

The first-service floor makes the intended mechanism real: normalized arms
perform 69/265/99 completed repeat draws, and the final-generation count range
reaches 0–6 or 0–7 instead of the previous one-pass maximum of one. The
three-scene mean quality change versus direct R4 control is `+0.015072 dB`, so
the reallocation preserves the R4 quality base across UTMM, RPNG, and Aria.

However, with `gamma=log(1.5)` and the exact normalized-variance potential,
the effective coefficient is `gamma/(T+1)`. Normalized and dense-only RR
therefore differ in only 1, 2, and 0 selection rows despite 140, 534, and 200
dense services. Their mean PSNR gap `+0.009767 dB` is not causal evidence for
ERCB and must be treated as run-level variation. Exp111 validates the dense
repeat structure, not the current ERCB temperature as a quality lever.

## Inline verifier incident

The source-locked runner completed every arm but its inline verifier compared
selector-internal snapshots when it meant to compare immutable slot work, and
compared a cumulative primary clock against a final-generation counter. It
therefore raised after each completed scene. No mapping or evaluation artifact
was lost. `report_exp111_dense_repeat_ercb.py` performs artifact-only v2
verification using `(event, generation, Adam, render)` slot skeletons and
cumulative clocks across arms; all scenes pass. The original failing reports
remain preserved for provenance.

## Decision

Retain first-service plus dense-repeat reallocation as a quality-safe Track-A
candidate. Do not yet claim ERCB quality causality. The next development-only
test may choose one common normalized temperature that produces a measurable
selection divergence without scaling with `T`; multiplying by `T+1` would
cancel the normalization and silently return to raw-variance sampling, which
is forbidden. A selected temperature must then transfer unchanged.
