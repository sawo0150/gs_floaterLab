# ERVS K16, τ = 8 / 16 — result (2026-10-06)

PREREG: [PREREG.md](PREREG.md). Runner `run_ervs_tau_scale.py`; results `results/campaigns/gain_attribution/ervs_tau_scale/v1/`.
124 runs (19 scenes × 3 seeds × 2 τ + FAST-LIVO2 5 × seed 0 × 2 τ), all valid. Page: offline_compare.html (τ selector).

19 scenes × 3 seeds (seed means per scene), held-out views from the final map's first trained view; scene bootstrap 95%:

| arm | PSNR − uniform_iid | PSNR − uniform_k16 | gap MAD − uniform_iid (lower in) | front-loading |
|---|---:|---:|---:|---:|
| uniform_k16 | +0.091 [+0.042, +0.146] 15/19 | 0 | −0.012 (12/19) | 0.291 |
| ERVS τ=4 | +0.063 [+0.013, +0.114] 13/19 | −0.028 [−0.077, +0.016] | +0.033 (8/19) | 0.271 |
| ERVS τ=8 | +0.076 [+0.031, +0.127] 14/19 | −0.015 [−0.051, +0.023] | −0.020 (11/19) | 0.280 |
| ERVS τ=16 | +0.077 [+0.022, +0.134] 14/19 | −0.014 [−0.048, +0.025] | −0.009 (9/19) | 0.285 |

(uniform_iid front-loading 0.275.) Rule-selected group (6 scenes, held-out seeds 1–2): slope change vs uniform_iid
τ4 +0.30 (5/6), τ8 +0.09 (3/6), τ16 +0.07 (3/6), uniform_k16 +0.04; PSNR τ4 +0.12, τ8 +0.10, τ16 +0.14 (6/6), k16 +0.08.
FAST-LIVO2 seed 0 (5 scenes): τ16 +0.16 vs uniform_iid (4/5), τ4 −0.03, τ8 −0.14.

**Reading.** Larger τ moves ERVS toward uniform_k16 in every read-out (front-loading, PSNR, MAD); no τ beats
uniform_k16 on mean PSNR (all within ±0.03, CIs include 0). The count term's distinctive effect, the slope correction in
scenes where uniform under-serves late views, is clear only at τ=4 (5/6) and fades at τ 8/16. τ=4 stays the method.
