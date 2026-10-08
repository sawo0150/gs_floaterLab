# Online → offline gap decomposition ("ladder") — PREREG (2026-10-08, user approved D1–D4)

**Why.** Across 27 scenes the best online sampler is 1.11 dB below the offline reference while all samplers span
only 0.24 dB: ~80% of the gap is outside the sampler. Hypotheses: H1 count allocation, H2 poses corrected after
training, H3 map growth / interference / forgetting, H4 chronological order.

**Arms** (`offline_ladder_patch.py`, seed 0, budget 25; reference online run = uniform_iid seed 0 of the scene):
- **D2 `seq`**: no training during the stream; after the last non-terminal arrival, replay the reference run's exact
  final-generation service sequence (same views, same order, same counts) with the final map and poses.
  online uniform_iid → D2 = effect of training *during* the stream (H2 + H3 growth).
- **D1 `cnt`**: as D2 but the service multiset shuffled. D2 → D1 = chronological order (H4).
  D1 → existing offline arm (epoch RR, equal counts) = count allocation (H1).
- **D4 `hyb85`**: online ERVS K16 until 85% of the earned credit is spent, the remaining 15% spent after the last
  non-terminal arrival with epoch RR over all views (final consolidation). vs online ERVS K16 and offline.
- **D3 (online with final poses)**: needs per-step pose injection for KF and interpolated dense views; first
  estimated from the archive (pose change of each KF between its first and last tracker packet vs the per-scene gap);
  run as an arm only if that analysis supports H2.

**Scenes.** aria1253, aria1253rot (large gap), square-1, table_06 (small gap), ego-drive (UTMM), Retail_Street
(FAST-LIVO2, local runner). 6 scenes × 3 arms = 18 runs on the RTX 5070 Ti.

**Read-out.** Mean PSNR (final-map held-out views) per rung and the share of offline − online explained by each step;
time curves vs offline. Descriptive (single seed); decomposition is reported per scene and as the mean.
