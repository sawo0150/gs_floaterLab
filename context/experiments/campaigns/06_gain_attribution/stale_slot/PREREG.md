# Rule A: one stale-first dense slot on top of ERVS K16 — PREREG (2026-10-04, user approved)

**Why.** Offline-reference analysis (offline_reference card): under ERVS the earliest final-map views get the same total
count as under uniform but less of it in the second half (42% vs 48%) and sit idle longer at the end (10.2% vs 8.4% of
steps); ERVS loses the first 15% of the final map vs offline (−0.91 vs −0.44 dB, rule group, seeds 1–2). The user asked
for a rule-based fix that leaves the ERVS formula unchanged.

**Arm `ervs_stale1`** (`stale_slot_patch.py`): ERVS K16 group queue unchanged; after each reserve the first dense pick is
replaced by the admitted dense view with the longest time since its last service in this generation (unserved views
count from admission); the displaced ERVS pick goes to the front of the dense group queue. KF/window picks, quotas,
credit, κ, τ unchanged.

**Scenes, budget, seed.** square-1, table_03, table_07, ego-drive, fast-straight, square-2 (rule-selected group on
final-map views) + slow-straight-1, slow-straight-2; budget 25; seed 0; 8 runs. Compared with the existing seed-0
uniform_iid / uniform_k16 / ervs_k16 runs and offline seed 0, held-out views from the final map's first trained view.

**Success (all three, 8-scene mean, seed 0).** (1) online − offline gap over the first 15% of the final-map span closer
to 0 than ERVS; (2) mean PSNR ≥ ERVS − 0.05 dB; (3) gain over uniform_iid in 30–90% at least half of ERVS's. A pass is
a candidate for seeds 1–2, not a result.
