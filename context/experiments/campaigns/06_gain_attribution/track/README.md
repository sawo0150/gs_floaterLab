# Online vs offline tracking — result (2026-10-09, aria1253 seed 0, scale clamp off, 2 valid runs)

Final-map PSNR unchanged by the measurement: online 25.17 (noscale_iid 25.19), offline 26.89 (gates PASS; 26.89).
**Births.** Online: covered old KFs −92.7 summed at births, +85.7 recovered between births (same as before).
Offline: the probe recorded no events (the trainer pool is not synced during the stream, so no "old KFs" exist);
births happen before any training, so there is no trained result to damage.
**Forgetting (final generation, every pool KF every 50 renders).**
| | smoothed peak − final (mean / median / p90) | KFs with drop > 0.5 dB | pool-mean PSNR at the end |
|---|---|---:|---:|
| online | 1.54 / 1.51 / 2.76 | 79% | 25.22 |
| offline | 0.23 / 0.11 / 0.68 | 18% | 26.98 |
Online pool-mean PSNR (training views) climbs to **26.93 at 1,500 renders** (≈ offline's final 26.98) and stays ~26.3–26.9
until ~1,950, then same-KF PSNR drops **−1.55 dB** within one 50-render interval (newest KF frame 1091→1123, which spans
the pose_scale_correction at frame 1118), partly recovers (+1.09), and drops again −0.80 (frames 1201→1217). The
corrections at 1076 (+0.01) and 1187 (−0.08) did little. Offline trains after all corrections and rises monotonically.
**Reading.** Online is not inefficient: it reaches offline-level quality on the KFs it has, then **late-stream events
crash the trained map** (−1.55 and −0.80 dB), and the remaining budget recovers only part of it. The −1.55 coincides
with a Gaussian-moving pose/scale correction; the −0.80 is not yet attributed (snapshot resolution 50 renders).
Earlier readings ("training efficiency", "no forgetting") are superseded.

## Amendment 1 result — event probe (2026-10-09, aria1253 seed 0, clamp off, 1 valid run, PSNR 25.16)
Every pool KF rendered before/after each event, final generation, sums of the mean-KF ΔPSNR:
births −13.46 (90), tracker packets −12.52 (95, includes their births), correction packets −1.43 (4; the Gaussian move
alone −6.44 is measured before the camera poses are updated in the same packet, so only the packet total is
meaningful), pruning −0.12 (7), training between events +43.13.
**12 of 90 births carry −11.43 of the −13.46**, each lowering the mean over *all* pool KFs by 0.3–1.95 dB and
>0.5 dB on 50–71% of KFs: frames 1082/1091/1108/1123 (−0.39/−0.94/−1.95/−1.09) and 1193–1272 (−0.30…−1.18).
They are **revisits**: 1082–1123 return to the start (nearest older KF 49/62, 1.2–1.6 KF-steps, view angle 6–68°);
1184–1272 retrace the path backwards (nearest older KF 934–1016, 0.1–0.9 KF-steps, view angle 149–176°).
The −1.55 drop in tracking is the birth at frame 1108 (−1.95), not the correction at 1118 (−0.01); the −0.80 is the
births at 1209–1233. Corrections are a minor term.
**Reading.** On aria1253 the online→offline gap comes from births during revisits: re-observed, already-trained space
gets a fresh layer of Gaussians at opacity 0.5 that degrades most old KFs at once; online spends the remaining
budget recovering part of it. Offline births the same layer before training and trains all views jointly.

## Amendment 2 result — event probe with low-opacity births (2026-10-09, 1 valid run, final-map PSNR 25.63)
Old KFs (frame < 900, n=61), after 1,850 renders, additive split (births nested in packets; training = between events):
| | start → end | births | corrections | training |
|---|---|---:|---:|---:|
| opacity 0.5 | 26.95 → 24.66 (**−2.30**) | −13.52 | −1.65 | +12.88 |
| opacity 0.12 | 27.04 → 26.17 (**−0.87**) | −1.65 | −0.30 | +1.09 |
Revisit-birth damage drops ~8× (per-packet −0.30…−1.18 → −0.03…−0.21) and the late old-KF decline shrinks from −2.30 to
−0.87; a residual remains. Gap to offline at the end (training-view PSNR, offline track final snapshot):
| | old KFs | recent KFs (≥ frame 900, n=29) |
|---|---:|---:|
| opacity 0.5 | +3.25 | +1.34 |
| opacity 0.12 | +1.74 | +1.39 |
**Reading.** Low initial opacity mostly fixes the revisit damage but not all of it (−0.87 residual), and old KFs also
peak below offline (27.04 vs 27.91). Recent KFs are 1.4 dB below offline in both arms — unaffected by births; they
arrive late and get fewer updates online (allocation / late-view under-training).

## Amendment 4 result — selective births 0.5 / 0.02 (2026-10-09, 1 valid run)
82.5% of new points on already-explained pixels (start 0.02), the rest 0.5. Old KFs after 1,850 renders, additive:
| births | PSNR | old KFs late | births | corr. | training | gap to offline: old / recent | pruned (final gen.) | final GS |
|---|---:|---|---:|---:|---:|---|---:|---:|
| all 0.5 | 25.19 | 26.95→24.66 (−2.30) | −13.52 | −1.65 | +12.88 | +3.25 / +1.34 | 30,553 | 210,179 |
| all 0.12 | 25.63 | 27.04→26.17 (−0.87) | −1.65 | −0.30 | +1.09 | +1.74 / +1.39 | 50,534 | 190,198 |
| sel. 0.5/0.02 | **25.72** | 26.93→26.48 (**−0.45**) | −0.49 | −0.14 | +0.19 | +1.43 / +1.55 | 77,010 | 163,722 |
Revisit-birth damage nearly gone (−0.49); the late old-KF decline shrinks to −0.45. Many covered births are pruned
(below the 0.1 threshold once unprotected): −22% Gaussians vs all-0.5, yet PSNR is the best of the three. Remaining
gap to offline: old KFs +1.43 (mostly their lower peak), recent KFs +1.55 (late-view under-training, slightly worse).

## Amendment 5 result — selective births 0.5/0.02 with ERVS K16 (2026-10-09, 1 valid run)
| sampler | PSNR | held-out first 70% / last 30% | train-KF gap to offline old / recent | KF counts old / recent (offline 12–13 each) |
|---|---:|---|---|---|
| uniform w/ repl. | 25.72 | 26.88 / 23.06 | +1.43 / +1.55 | 15.0 / 6.6 |
| ERVS K16 | 25.72 | 26.87 / 23.05 | +1.43 / +1.46 | 15.5 / 6.0 |
ERVS changes nothing here: recent KFs (≥ frame 900) still get about half of offline's count (6 vs 12–13), because they
arrive late and the budget left after their arrival is small; balancing within the pool cannot move credit backwards.

## Online − D2 residual by stream position (2026-10-09, no GPU, final-map per_view, clamp off)
Held-out PSNR by stream fifth:
| | 0–20% | 20–40% | 40–60% | 60–80% | 80–100% | all |
|---|---:|---:|---:|---:|---:|---:|
| online 0.5 | 27.33 | 26.49 | 25.41 | 23.98 | 22.79 | 25.19 |
| online selective 0.5/0.02 | 27.71 | 27.55 | 26.65 | 24.19 | 22.57 | 25.72 |
| D2 | 28.69 | 28.47 | 27.50 | 25.36 | 22.65 | 26.52 |
| offline | 27.93 | 28.55 | 27.56 | 26.49 | 23.98 | 26.89 |
D2 − selective: held-out +0.97/+0.92/+0.86/+1.17/+0.08, training views +1.02/+0.64/+1.19/+1.06/+0.09.
**Reading.** Online − D2 is not a late-view budget effect (D2 has the same counts; last fifth ≈ 0). After the revisit
fix, a roughly uniform ~1 dB remains over the first 80% of the stream; cause not identified. Offline − D2 sits in the
last 40% (+1.13, +1.33): that part is allocation (late-view under-training).

## The ~1 dB online−D2 residual: two candidates (2026-10-09, no GPU)
**(1) Cumulative non-revisit births.** Per old KF (frame < 900, n=61), whole-stream sums of its own PSNR changes:
online 0.5: births −1.45, revisit births −13.44, corrections −1.65, pruning −0.07, training +19.61;
selective 0.5/0.02: births −0.48, revisit −0.49, corrections −0.14, pruning −0.09, training +6.42.
After the revisit fix, ordinary births cost ≤0.5 dB per old KF over the whole stream and are repaired → too small for
the ~1 dB residual.
**(2) Training on an incomplete map.** Surviving Gaussians grouped by birth time (fifths of the KF stream), clamp off,
both arms born at 0.5:
| birth fifth | online: n / median max-scale / p95 / opacity | D2: n / median / p95 / opacity | offline |
|---|---|---|---|
| 0–20% | 41,502 / 0.0232 / 0.110 / 0.72 | 38,326 / 0.0206 / 0.098 / 0.66 | 40,266 / 0.0200 / 0.093 / 0.66 |
| 20–40% | 29,176 / 0.0236 / 0.077 / 0.65 | 22,249 / 0.0254 / 0.085 / 0.68 | 29,307 / 0.0225 / 0.070 / 0.65 |
| 80–100% | 52,647 / 0.0163 / 0.068 / 0.34 | 46,470 / 0.0213 / 0.096 / 0.53 | 48,411 / 0.0218 / 0.089 / 0.57 |
Earliest-born Gaussians online are ~13% larger, more opaque and 8% more numerous than in D2/offline (consistent with
compensating for missing neighbours) but the signature is modest and not consistent in the 20–40% group. By
elimination (order, counts, clamp, revisit births, ordinary births, corrections all small or matched), the residual
is the map state each update acts on (updates applied to a partial map), but this is not directly shown.

## Amendment 6 result — lagged window (lag 6) (2026-10-09, 3 valid runs)
Final-map held-out PSNR (all / by stream fifth):
| scene | arm | all | 0–20 | 20–40 | 40–60 | 60–80 | 80–100 |
|---|---|---:|---:|---:|---:|---:|---:|
| aria1253 | selective | 25.72 | 27.71 | 27.55 | 26.65 | 24.19 | 22.57 |
| aria1253 | selective + lag 6 | 25.55 | 28.13 | 27.63 | 26.27 | 23.90 | 21.91 |
| aria1253 | D2 | 26.52 | 28.69 | 28.47 | 27.50 | 25.36 | 22.65 |
| square-1 | online 0.5 | 21.75 | 22.86 | 21.89 | 22.73 | 21.21 | 20.08 |
| square-1 | selective | 21.72 | 23.02 | 21.82 | 22.58 | 21.17 | 20.02 |
| square-1 | selective + lag 6 | 21.33 | 23.20 | 21.88 | 22.52 | 21.10 | 18.00 |
| square-1 | D2 | 21.85 | 23.23 | 21.78 | 22.98 | 21.41 | 19.86 |
Lag 6 loses overall (−0.17 / −0.39), mostly in the last fifth (−0.66 / −2.02: the newest KFs lose window training).
Over the first 80% it is neutral (aria 26.48 vs 26.53; square-1 22.18 vs 22.15), only the first fifth gains
(+0.42 / +0.18). Delaying window training by 6 KFs does not recover the online−D2 residual. On square-1 selective
births change nothing (21.72 vs 21.75), as expected without big revisits.
