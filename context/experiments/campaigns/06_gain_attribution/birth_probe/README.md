# Birth probe — result (2026-10-09)

1 run (aria1253, seed 0, online uniform with replacement), 84 birth events, 0 errors; final-map PSNR 24.66 (= online
reference: probing does not change training). Δ = PSNR right after − right before a birth, no training in between:

| old KF group | n | mean Δ | median Δ | p10 Δ | share Δ<0 |
|---|---:|---:|---:|---:|---:|
| covered (sees new points, mean share 0.72) | 444 | **−0.211 dB** | −0.028 | −0.714 | **83%** |
| control (sees none) | 345 | −0.000 | 0.000 | 0.000 | 1% |

By covered share: 0.05–0.2 −0.38, 0.2–0.5 −0.19, ≥0.5 −0.19. Sum over the ≤6 covered views per event −1.12 dB.
**Reading.** Direct evidence: a birth immediately lowers the PSNR of already-trained views that see the new points,
and leaves other views untouched. The drop is skewed (most small, a tail of large drops). This measures the immediate
damage only; how much later training recovers is not measured here. Together with lowop (+0.47 dB), new Gaussians
covering trained regions is a real part of the stream-time gap.

## Correction (2026-10-09): damage vs recovery by sums, not medians
Per probed view, change at births (after − before) vs change between its consecutive probes (training in between):
| run | covered: at births (sum) | covered: between births (mean / sum) | control: between births (mean / sum) |
|---|---:|---:|---:|
| baseline (0.5) | −93.7 | +0.209 / +84.1 | −0.067 / −19.2 |
| selop | −18.0 | +0.073 / +29.3 | −0.049 / −14.2 |
The earlier statement "recovery (median +0.07) cannot keep up with damage" was wrong: by sums, training recovers
~90% of the immediate birth damage. Old views *not* covered by the birth lose −0.05 to −0.07 dB per interval while
other views are trained (may include covering by other births in between) — a sign of training-time interference.

## Per-view net change (2026-10-09, baseline run)
72 old KFs probed ≥2 times (median span 9 birth events): net PSNR change first→last mean −0.19 (at births −1.30,
between births +1.11). The 31 KFs only ever probed as control (never seen by the probed births): net **+0.01**.
So the −0.067/interval control figure above came from views covered by unprobed births in between; **no sign of
forgetting on views untouched by births**. Old views stay roughly flat online; D2's advantage (also +2.2 dB on
training views) is that they end higher, i.e. online steps are less effective, not that quality is lost later.
