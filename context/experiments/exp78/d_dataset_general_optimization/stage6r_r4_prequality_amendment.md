# Stage-6R R4 pre-quality protocol amendment

Date: 2026-09-15

Status: **locked after the fresh uniform-control mapping audit and before the
R4 candidate was run or either arm was evaluated. No R4 PSNR/SSIM/LPIPS value
had been generated or inspected.**

The paper-side R4 contract initially required the candidate to service
strictly more unique historical keyframes than the uniform control during
`BALANCED/REPLAY`. The quality-blind uniform-control ledger showed that this
metric is saturated: 8,400 historical services cover all 197 historical
keyframes at least once. No selector can exceed the complete causal pool, so
the original promotion condition is mathematically impossible and cannot
measure ERCB's intended service-shortfall effect.

The selector implementation, candidate flags, seed, work, causal pool and
quality thresholds remain unchanged. Only the saturated structural promotion
metric is replaced as follows.

For every map generation containing `BALANCED/REPLAY` rows:

1. take the historical keyframes already present in the first such row;
2. retain the stable anchor cohort present in every later balanced/replay row
   of that generation;
3. count completed native historical services for each anchor UID;
4. report the cohort's `max(count)-min(count)` spread and population
   coefficient of variation (`std(count)/mean(count)`).

Promotion requires both the sequence-equal mean spread and mean coefficient
of variation to be strictly lower for R4 than for the fresh uniform control.
The candidate must still have strictly positive overall fixed held-out PSNR
delta. The frozen retention gates remain `R4-control >= -0.10 dB` and
`R4-render-matched vanilla >= +1.00 dB`. Unique historical coverage remains a
reported descriptive statistic but is no longer a promotion gate.

At lock time the uniform control's sole balanced generation has 33 stable
anchor keyframes, service-count range 75--109, spread 34 and coefficient of
variation 0.0969352. These are scheduling telemetry only; no rendering-quality
metric was read.
