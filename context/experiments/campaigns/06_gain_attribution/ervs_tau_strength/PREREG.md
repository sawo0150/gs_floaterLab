# Preregistration — ERVS balancing strength τ on B (2026-10-03, before any run)

User request: ERVS K16 at τ = 4 barely balances service counts; try stronger balancing.

B's ERVS weight is exp(−(n − n_min)/scale) with scale = τ/N·(T+1) ≈ τ × mean services per view, so a view at the
mean count has relative probability exp(−1/τ): 0.78 at τ = 4, 0.37 at τ = 1, 0.018 at τ = 0.25.

## Arms (B worker/recipe/environment; κ = 16; quotas 3:3:6; group queue K = 16; budget 25; seed 0)

| Arm | τ | Source |
|---|---|---|
| uniform_iid | ∞ (with replacement) | reused, ervs_vs_iid_seeds seed 0 |
| ervs_tau4 | 4 | reused, ervs_vs_iid_seeds seed 0 |
| ervs_tau1 | 1 | new (`group_k_patch.py`, `--tau 1`) |
| ervs_tau0.25 | 0.25 | new (`group_k_patch.py`, `--tau 0.25`) |

Scenes: aria1253, table_06, aria1253rot, square-1. 8 new runs. The scene-extension run (seeds 1–2) is paused after its
current run and resumed afterwards.

## Metrics

Service-count CV per pool (final generation), mean services per view by arrival-time bin, held-out PSNR, min-bin PSNR,
worst-Q1, five-bin paired differences vs uniform_iid. Gate: recorded policy τ equals the arm's τ; group queue used.
Single seed, exploratory: reported for all cells whatever their sign.
