# ERVS K16 with weaker count balancing (τ = 8, 16) — PREREG (2026-10-06, user approved)

**Why.** τ sweep (ervs_tau_strength) showed stronger balancing hurts (τ 1 / 0.25: −0.02 / −0.74 dB vs uniform). The
offline-reference study shows ERVS τ=4 shifts training toward later views (front-loading down, 17/19 vs uniform_k16)
but costs the earliest views. Weaker balancing (larger τ) moves ERVS toward uniform_k16; the question is where the
mean-PSNR / evenness trade-off sits for τ ∈ {4, 8, 16}.

**Arms.** `ervs_t8`, `ervs_t16`: ERVS K16 (group_k_patch, B_GROUP_K=16) with `--tau 8` / `--tau 16`; everything else as
the adopted B recipe. Compared with existing uniform_iid, uniform_k16, ERVS τ=4 and the offline reference.

**Scenes, seeds, budget.** The 19 scenes of ervs_vs_iid_scenes (4 pinned + 15 extra) × seeds 0, 1, 2, plus FAST-LIVO2 5
scenes × seed 0 (local runner, pool cap 700), budget 25: 2 × (57 + 5) = 124 runs on the RTX 5070 Ti. Order: all seed-0
runs first, then seeds 1, 2.

**Read-outs (descriptive, no single pass/fail).** Per τ: mean PSNR vs uniform_iid and uniform_k16 (scene bootstrap);
gap-curve MAD vs offline; front-loading index; validation group (rule-selected scenes) slope and PSNR.
