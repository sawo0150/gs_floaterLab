# Rule A: stale-first dense slot on ERVS K16 — result (2026-10-04)

PREREG: [PREREG.md](PREREG.md). Runner `run_stale_slot.py`, patch `stale_slot_patch.py`. Results
`results/campaigns/gain_attribution/stale_slot/v1/rule_a/`. 8 runs, all valid; replacements per run: 2 (slow-straight-1)
… 1253 (table_03); mean idle of the injected view 7 … 1043 steps.

Seed 0, held-out views from the final map's first trained view, gap = online − offline seed 0:

| arm | mean PSNR | gap, first 15% | gap, 30–90% |
|---|---:|---:|---:|
| uniform_iid | 22.145 | −0.699 | −0.877 |
| uniform_k16 | 22.288 | −0.334 | −0.716 |
| ERVS K16 | 22.259 | −0.572 | −0.714 |
| ERVS K16 + stale slot | 22.159 | −0.561 | −0.839 |

Criteria: (1) early gap closer to 0 than ERVS — +0.011 (6/8), marginal; (2) mean PSNR ≥ ERVS − 0.05 — **fails**
(−0.100, 2/8 up); (3) 30–90% gain over uniform ≥ half of ERVS's — **fails** (+0.038 vs +0.163). **Rule A rejected.**
The slot takes training from the mid/late views that ERVS lifts and gives it to the longest-idle views without fixing
the early gap; square-1 gets worse early (−1.51 vs −0.72). Note on seed 0 the same-group uniform_k16 has the best mean
PSNR and early gap among the four. ERVS stays as is (user decision); rules B/C are not run.
