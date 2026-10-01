# Local RTX 5070 Ti resume — 2026-10-01

## Verified

- Lab main pulled through `362fcbd`; custom main through `50286727`.
- RTX 5070 Ti 16 GB, driver 595.84, Python environment `vigs-slam-5090`, PyTorch 2.8.0+cu128.
- All 119 locked sources and locked extension files match Colin hashes; both D3 and official vanilla imports succeed.
- RPNG/UTMM RGB for all 16 scenes match Colin under recursive rsync checksum comparison. Aria inputs and frozen archives are transferred separately.
- A process-local path profile preserves original source/manifest/setup bytes; runtime files and outputs are on the separate data volume. No optimizer/sampling/resolution change.
- [Aria pilot summary](aria_pilot_summary.json): all 4 runs pass execution checks and saved-map double evaluation. Vanilla also passes matched prefix-render and trajectory checks.

| Training renders/KF | D3 held-out PSNR | Vanilla held-out PSNR |
|---|---:|---:|
|15|23.463187|18.954431|
|40|25.760522|20.856435|

These are frozen causal tracker fixed-work results, not concurrent tracking or real-time claims. D3 proxy rendering remains extra work. This is a hardware migration pilot, not an isolated geometry-loss ablation.

## Resume plan

`resume_cvpr_5070ti.py` observes the initial pilot and transfer PIDs, validates inputs, completes the three-scene 12-run pilot and its checkpoint evaluation, then runs controls. The 19 passed Colin controls are excluded by dataset/scene/budget/arm identity; 121 remain. Pilot controls use fresh local references; other scenes use archived Colin references with no cross-GPU time comparison. The queue evaluates control checkpoints after training.

Failed or partial runs stop the queue; no output is overwritten or silently relabeled as passed. Checkpoint alignment rejection remains visible and does not support convergence claims. Geometry zero-weight controls and original 15/30/60 sampler reproduction remain subsequent work; FIFO/time panels remain deferred.

Local runtime status: `results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v1/queue_status.json`. The companion queue log and per-run logs identify failures. The 3-scene pilot and remaining-input transfers were still in progress when this card was written.
