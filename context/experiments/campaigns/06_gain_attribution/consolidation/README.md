# Settle-triggered consolidation — pre-analysis (2026-10-09, no GPU)

`benchmarks/online_gs/campaigns/gain_attribution/analyze_settle_consolidation.py` on the online uniform_iid seed-0 runs.
Births reconstructed from surviving Gaussians' origin_uid, projected into older KFs (older than the newest 6) with final
poses (frustum + positive depth, no occlusion; pruned Gaussians missing). Touch: ≥ share of a birth's points in the KF.
Rule: KF settled once M KFs arrived since its last touch; each settle schedules one consolidation (KF + anchored dense).
Budget reference: 15% of 25 renders/KF.

| scene | touched KFs / KFs | median touches | M=6, share≥0.05: renders (of 15% budget) | never settle before stream end |
|---|---|---:|---|---:|
| aria1253 | 66/91 | 13.5 | 161 (0.47) | 49 of 66 |
| aria1253rot | 132/140 | 25 | 336 (0.64) | 108 of 132 |
| square-1 | 60/71 | 11 | 118 (0.44) | 25 of 60 |
| table_06 | 179/186 | 90 | **0** | **179 of 179** |

share≥0.3 does not change the picture (table_06: 178/179 never settle at M=6).
**Reading.** A settle trigger fits the budget but (1) does nothing in small scenes revisited all the time (table_06:
almost every KF is touched by almost every birth), and (2) in the other scenes most touched KFs are touched until the end
of the stream, so their consolidation would only happen after the stream (= D4's final pass). The settle-triggered
design is not run; a debt-driven scheduler (no settle requirement) is proposed instead.

## Run result (2026-10-09, aria1253 seed 0, `settle_iid`)
First attempt failed the execution contract (audit record `counts_before` not adapted to with-replacement draws;
training itself correct), fixed and rerun with approval; archived under `consolidation/v1/failed_attempts/audit_record_*`.
Valid run: 158 consolidation draws (60 KF + 98 dense, 7% of 2,233 draws), queues empty at the end, 49 KFs still
touched (never settled). Final-map held-out PSNR **24.03** vs online uniform_iid 24.66 (seeds 0/1/2: 24.66/24.62/24.80)
→ **−0.63 dB**, outside the seed spread. Settle-triggered consolidation hurts on this scene; not pursued further.

## Why it hurts — per-view analysis (2026-10-09, no GPU)
Held-out views (final-map span) vs the mean of online uniform_iid seeds 0–2:
- By stream fifth, settle − online: −0.77, −1.73, −0.96, −0.08, +0.22 → the loss is in the old part, not the recent end.
- KF training counts by stream third barely change (online 593/313/205, settle 607/299/205): recent views are not starved.
- Views after a KF that was consolidated (164/261): **−1.00 dB**; all other views −0.08. Seed-to-seed spread on the same
  split: ±0.38 (consolidated) / ±0.75 (rest). The loss is localized to the consolidated regions.
**Reading.** "Consolidation starves recent views" is refuted. The extra replay itself degrades the replayed region
(held-out). Mechanism not identified; candidates: a burst of one region's views (KF then its dense views back to back)
after a long pause fits those views and hurts nearby held-out views; optimizer state of long-idle Gaussians. To check:
training-view vs held-out PSNR of the consolidated region (overfitting signature).

## Overfitting check (2026-10-09, no GPU: per_view of the existing evaluation, `is_mapping_view` = training views)
| arm − mean(online seeds 0–2) | train, consolidated region (n=56) | train, rest (35) | held-out, consolidated (164) | held-out, rest (97) |
|---|---:|---:|---:|---:|
| online s0 / s1 / s2 | −0.23 / +0.23 / +0.01 | +0.30 / −0.48 / +0.18 | −0.26 / +0.17 / +0.08 | +0.35 / −0.50 / +0.14 |
| settle | **−1.01** | −0.33 | **−1.00** | −0.08 |
| lowop | +0.21 | +0.50 | +0.36 | +0.55 |
| D2 | +2.22 | +1.13 | +2.45 | +1.12 |
Training views of the consolidated region drop as much as held-out views (−1.01 vs −1.00): **not overfitting**; the
extra replay degrades the region's fit itself. Online train ≈ held-out PSNR (25.42 vs 25.44): the online map is
under-fit, not over-fit. Open candidates: supervising old regions with KF poses that changed after the Gaussians were
born (aria1253 current-vs-final pose change: mean 3.6 cm / 0.16°, vs median Gaussian scale ~2 cm; from pose_oracle),
or optimizer state of long-idle Gaussians.

## Stale-pose check (2026-10-09, no GPU: frozen tracker events of aria1253 seed 0)
Events after the last mapper reset: 107 keyframe_update (window BA; camera poses change, Gaussians are NOT moved) and
4 pose_scale_correction at events 90/96/104/112 (frames ≥1076, i.e. after KF 76 of 91; these DO move Gaussians via
`_apply_pose_scale_updates`). KF camera-centre change from first appearance to last window update (no Gaussian move):
median 0.7 mm, p90 2.2 mm, max 4.7 mm; rotation median 0.017°, max 0.075° (KF baseline 0.27, Gaussian scale ~0.02).
50 of 60 consolidations happened before the first correction. **Stale-pose supervision is refuted** as the cause.
Note: the D3 card stated these archives have no pose updates; aria1253 does have 4 pose_scale_correction events
that move Gaussians (the 3.6 cm current-vs-final change comes from them). D3's reading needs this correction.
Also: the consolidated region's total KF training barely changed (first-third KF counts 593 → 607), so the −1 dB is
not a dose effect of "more training"; with one settle run it may still be partly chance beyond the 3-seed spread.
