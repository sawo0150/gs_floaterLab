# Exp110 — normalized ERCB / RR / ticket-off isolation

All arms preserve R4 admission, birth, pruning, physical renders,
Adam work, causal pool, growing no-repeat epochs, and transactional
commit. RR sets the Gibbs energy to zero in all three selector
families. The ticket-off arm changes only bounded dense-evidence clone
service.

| Scene | Normalized+ticket | RR+ticket | Norm. ticket-off | Norm-RR | Ticket-off | Clone N/RR/off | Dense/Aux/Native differing rows | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| utmm/ego-centric-2 | 19.483852 | 19.489788 | 19.495748 | -0.005936 | -0.011896 | 455/463/0 | 0/0/9 | PASS |
| utmm/fast-straight | 16.389484 | 16.411041 | 16.370305 | -0.021557 | +0.019179 | 332/322/0 | 0/0/0 | PASS |
| utmm/square-1 | 21.226980 | 21.222601 | 21.225575 | +0.004379 | +0.001405 | 470/472/0 | 0/0/16 | PASS |

Completed scenes: **3/3**.
Mean normalized-RR: **-0.007705 dB**.
Mean ticket-off: **+0.002896 dB**.
This pilot is mechanism isolation, not an all-scene method claim.

## Service activity and interpretation

| Scene | Dense registered/selected | Dense max count | Aux-KF max count | Native-KF services | Native full epochs | Trace changes N/RR (D/A/N) |
|---|---:|---:|---:|---:|---:|---:|
| ego-centric-2 | 50/48 | 1 | 2 | 1,771 | 29 | 0/0/9 |
| fast-straight | 5/3 | 1 | 1 | 14 | 0 | 0/0/0 |
| square-1 | 72/70 | 1 | 1 | 2,723 | 47 | 0/0/16 |

The dense selector completed less than one full growing no-repeat epoch in all
three scenes. Consequently, every selected dense view had count one and the
normalized-variance Gibbs term could not change a dense choice relative to
the RR control. Auxiliary keyframes were similarly single-pass except for one
extra service in `ego-centric-2`, and still produced an identical trace.

Only the native historical-keyframe path repeatedly traversed its pool. It
therefore produced 9 and 16 differing opportunity rows on the two active
scenes, but the resulting normalized-minus-RR differences were only
`-0.005936` and `+0.004379 dB`. The `fast-straight` negative control had an
identical selection trace yet differed by `-0.021557 dB`; this bounds the
observed selector deltas inside run-level nondeterminism for this pilot.

The topology ticket was active in every scene, performed 1,257 clones in the
normalized arms, and added zero render and zero Adam step. Its mean
ticket-on-minus-off effect was `+0.002896 dB`, also indistinguishable from
noise. Exp109 remains the quality-preserving 17-scene result, but neither the
normalized selector nor the bounded ticket may be claimed as the causal source
of its `+1.286809 dB` gain over vanilla.

## Decision

Keep normalized ERCB as the mathematically correct implementation and retain
the ticket as a quality-safe dense-evidence path, but do not present either as
a demonstrated quality lever yet. The next Track-A change must preserve the
causal first-service floor for newly admitted views and reallocate a small,
common portion of existing historical service into repeat opportunities; it
must not add renders, use a scene-specific phase cutoff, or sacrifice the R4
quality floor merely to inflate a dense-view ratio.
