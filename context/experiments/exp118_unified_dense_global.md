# Exp118 — unified dense global-slot pilot (fixed-render violation)

Date: 2026-09-24

## Intent

Keep the recent native-keyframe window and Adam count unchanged while
replacing one of six configured flexible historical-keyframe renders with a
transactional draw from the LPM-mass dense ERCB pool.

## Result — UTMM square-1

| Arm | PSNR | Delta | Dense renders/share | Total renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|
| mass normalized control | 21.231306 | 0 | 142 / 1.52% | 9,345 | 757 | 120,029 |
| unified mass normalized | 21.197972 | -0.033335 | 625 / 6.65% | **9,394** | 757 | 120,734 |
| unified mass RR | 21.179603 | -0.051703 | 625 / 6.65% | **9,394** | 757 | 120,693 |

The unified queue itself behaved as designed: 483/483 draws committed,
normalized/RR differed on 70 global rows, every reallocated render had LPM
evidence, the recent window was retained, and the topology lifecycle clock did
not advance. Quality stayed inside the -0.5 dB stop line.

## Failure and root cause

**FAIL: physical render parity was violated by +49 renders.** The first
implementation computed tracked slots as
`min(6 - dense_slots, available_historical)` and then appended one dense view.
When fewer than six historical views existed early in the stream, control used
all available historical views while the candidate used all of them plus the
dense view. Forty-two mapping iterations had fewer than five historical views;
the cardinality differences summed to 49 additional renders.

This is an implementation error, not evidence for or against unified dense
supervision. The result must not be compared as fixed work or transferred.
The correction defines the control-equivalent global cardinality first,
`G=min(6, available_historical)`, then uses
`dense=min(1,G,available_dense)` and `tracked=G-dense`. A new source lock and
experiment root are required.

Artifacts:
`results/experiments/exp118_unified_dense_global/utmm/square-1/`.
