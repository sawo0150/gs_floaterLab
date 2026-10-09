# Validation of the online fixes on 6 scenes — PREREG (2026-10-09, user approved: incl. cap 0.5, 6 scenes)

Scenes (gap-ladder set): square-1, aria1253, aria1253rot, table_06, ego-drive, Retail_Street; seed 0.
Arms (all ERVS K16, the adopted sampler):
- A  adopted online (clamp 0.1) — existing runs.
- B  clamp off (`B_ervs_noclamp`).
- B′ cap 0.5 instead of 0.1 (`Bp_ervs_cap05`; scale_cap_patch). Added because clamp-off maps grow giant Gaussians
  (max scale up to 11.7) and give a "floater lottery".
- C  best size setting + selective births 0.5/0.02 (`C_ervs_noclamp_sel` or `C_ervs_cap05_sel`).
- D  C + end-of-stream sweep (D4: ERVS 85% online, RR sweep 15% after the last arrival; `hyb85_selop_noscale` or
  `hyb85_selop_cap05`).
Two phases. Phase 1: B and B′ on 6 scenes (12 runs). **Size-setting rule (fixed now):** use the one with the higher
mean final-map PSNR over the 6 scenes; if within 0.05 dB, use cap 0.5. Phase 2: C and D with that setting on 6 scenes
(existing aria/square-1 runs reused when they match). Read-out: per scene and mean PSNR vs A, D2, offline; per-fifth;
giant-Gaussian counts (scale > 0.3 & opacity > 0.3).

## Amendment 1 (2026-10-09, user approved)
Phase 1 B′ runs all failed (scale_cap_patch wrote the scale parameter in place without no_grad; archived under
`validation/v1/failed_attempts/nograd_*`); fixed and rerun on the 6 scenes. Phase 2 is on hold; the free-space birth gate
is paused by the user.
