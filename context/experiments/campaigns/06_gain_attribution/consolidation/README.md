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
