# Online → offline gap decomposition — result (2026-10-08)

PREREG: [PREREG.md](PREREG.md). Patch `offline_ladder_patch.py`, runner `run_gap_ladder.py`; results
`results/campaigns/gain_attribution/gap_ladder/v1/`. 18 runs (6 scenes × D2 seq, D1 cnt, D4 hyb85), seed 0, all valid
(sequence replay used the recorded queue for ~99% of draws). Mean PSNR on final-map held-out views:

| scene | online uniform_iid | D2 seq | D1 cnt | offline | online ERVS | D4 hyb85 |
|---|---:|---:|---:|---:|---:|---:|
| square-1 | 21.73 | 21.99 | 21.94 | 22.72 | 21.98 | 22.21 |
| aria1253 | 24.66 | 26.65 | 26.59 | 26.90 | 24.85 | 26.17 |
| aria1253rot | 24.49 | 26.23 | 25.93 | 26.75 | 24.70 | 25.49 |
| table_06 | 24.56 | 24.89 | 24.88 | 25.20 | 24.78 | 24.92 |
| ego-drive | 20.69 | 21.22 | 20.92 | 22.04 | 20.81 | 21.57 |
| Retail_Street | 26.71 | 27.83 | 28.06 | 28.40 | 26.74 | 27.58 |

Decomposition of offline − online uniform (mean 1.53 dB):
- **training during the stream** (online → D2, same views/order/counts, trained after the stream): **+0.99 dB (65%)**;
  up to +2.0 dB on the Aria scenes.
- chronological order (D2 → D1): −0.08 dB (≈0; shuffling does not help).
- **count allocation** (D1 → offline, equal per-view counts): **+0.62 dB (40%)**.

D4 (ERVS online for 85% of the credit, last 15% as an epoch-RR sweep after the last non-terminal arrival):
**+0.68 dB vs online ERVS (6/6)**, recovering 50% of the ERVS → offline gap.

**Reading.** The largest share is not *which* views are trained but *when*: the same updates are worth ~1 dB more
when applied after the stream. Poses move little after a KF's first appearance (0.01–0.45% of scene extent, <0.3°;
Spearman with the gap 0.41 over 27 scenes), so the stream-time loss is mostly attributed to training a map that is
still growing (later births/pruning and new regions overriding earlier updates), with pose updates a minor part —
to be split by an oracle-pose arm if needed. Allocation is the second factor; order does not matter. A short
consolidation sweep at the end already recovers half of the gap. Single seed, 6 scenes.
