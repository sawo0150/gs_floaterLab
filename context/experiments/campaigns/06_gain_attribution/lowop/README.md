# Low-opacity births (diagnostic) — result (2026-10-09)

1 run (aria1253, seed 0, uniform with replacement), valid (116 low-opacity births, 282,107 Gaussians at 0.12; the 3
first births of each generation at 0.5). Final-map held-out PSNR **25.13**: +0.47 dB over online uniform_iid (24.66);
D2 26.65. Starting new Gaussians nearly transparent recovers about a quarter of the stream-time gap on this scene,
consistent with births covering trained regions (see ../birth_probe). Single scene, single seed.

## Amendment 1 results (2026-10-09)
- aria1253 `lowop_noscale_iid` (opacity 0.12 + no scale clamp): **25.64** (+0.98 vs online 24.66; lowop alone +0.47,
  no clamp alone +0.53 → the two effects add up). D2 26.65: about half the stream-time gap remains.
- square-1 `lowop_iid`: 21.72 vs online 21.73 (−0.01): no effect there (the clamp had none either; D2 gap there only
  +0.26). Both fixes help on aria1253 only so far.
