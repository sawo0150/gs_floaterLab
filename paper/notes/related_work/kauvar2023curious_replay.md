# Curious Replay (Kauvar et al., ICML 2023) — `refs/08_rl_replay/kauvar2023curious_replay.pdf`

Model-based RL (Dreamer). Replay priority per transition i (Eq. 1): p_i = c·β^{v_i} + (|L_i| + ε)^α,
v_i = times replayed; defaults β = 0.7, α = 0.7, c = 1e4, ε = 0.01, p_MAX = 1e5 for new items (SumTree sampling).

## How strong is the count term (compared with our ERVS)
- β^{v} = exp(−0.357·v): absolute visits, not normalized. Each extra visit ×0.7; 7 visits → ×0.08.
- Ours (B): exp(−(n − n_min)/scale), scale ≈ τ × mean services per view → per-visit decay 1/(τ·mean).
  With mean ≈ 10–20, τ = 4 gives 0.013–0.025 per visit (15–30× weaker than CR); CR's count term ≈ our τ ≈ 0.15–0.3.
- But it saturates: c·β^v drops below the loss term (≈ O(1)) after ≈ ln(1e4)/0.357 ≈ 26 visits. After that, sampling is
  by model loss, not by count. So the count term is a catch-up for new data, not a lifetime equalizer.
- Stated purpose: "biases sampling towards recent experiences, and ensures that the agent revisits each experience
  multiple times" — adaptation to a changed environment.

## How they analysed it
- Task metrics: steps to 5th object interaction (object assay), Crafter score, DMC returns.
- World-model error on held-out test trajectories over time (Fig. 2); forgetting test: object added at 0.5M, removed at
  1.5M, error on object trajectories (Fig. A4) — no forgetting with CR, strong forgetting when the buffer is cleared.
- Ablation (Table 2): count-only, adversarial-only, both (object: 2.2 / 1.8 / 0.5 ×1e5 steps; Crafter 16.2 / 17.3 / 19.4).
- β sweep (Table A1, α = 0.7, n = 2 seeds): β 0.1/0.3/0.5/0.7/0.9 → 1.2/1.1/1.4/0.5/0.6 (baseline 3.7). All beat
  uniform; the weaker falloffs (0.7, 0.9) were best. Crafter (Table A2): β 0.5–0.9 within noise (11.9–13.2 vs 11.7).
- Example priorities over the buffer (Fig. A11). No analysis of visit-count evenness.

## Relevance to ROGO
- Same exponential-in-count form (cite first). Difference: our scale is normalized and never saturates, so strong τ keeps
  pushing old views down (our τ sweep: monotonically worse). CR's saturation + loss fallback is the "new-view catch-up,
  otherwise near-uniform" behaviour our replay-rate analysis suggests.
