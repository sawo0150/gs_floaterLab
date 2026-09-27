# κ / τ with existing motion-blur gate — predeclared 2026-09-26

User requests κ/τ optimization together with the existing motion-blur policy, after the KF RGB-only attribution control.

Keep the current unified40 render/KF,3:3:6,per-imageAdam,cumulativeERVS,scale projectionON,densify/prune/phase gateOFF,seed0 and the same Aria1253/RPNGtable_06/UTMMsquare-1 frozen causal tracker/held-out cohorts. No scene-specific settings. No extra live/geometry claim.

## Growth semantics

KF is mandatory and ungated. `membership=growth`, `growth_budget_scope=dense_only` earns one dense admission per κ completed optimizer steps in the map generation. Failed/reserved/cancelled work earns nothing. All roles contribute completed steps. At current optimizer_batch_size1 this is also render count. Candidates are already-arrived bracketed observations passing the existing blur gate; select largest temporal coverage hole, without a sequence horizon. No data is physically deleted after admission; CPU history is preserved. Existing immediate baseline remains default.

## Finite staged search

1. Blur ON, tau1: immediate and κ4/8/16, each3scenes (12runs).
2. At selected κ, blurON: tau0.25 and4 (6runs); tau1 already measured. Tau is the scalar coefficient divided by actual KF/dense pool N separately.
3. At best observed κ/tau, blurOFF comparison (3runs).

Total21runs, each saved map evaluated twice. This is a coarse staged search, not exhaustive joint or a claimed global optimum. The blur thresholds stay at energy0.8/frequency0.9. The previous no-blur baseline is reference for exact render prefixes and poses; a fresh immediate/tau1/blur baseline reproduces prior blur service selections.

Selection: reject candidates dropping any scene >0.05dB vs fresh immediate/tau1/blur baseline; among candidates within0.02dB of highest mean PSNR choose smallest mean mapping time. These bands are an engineering selection rule, not confidence intervals. All conditions disclosed. These are development scenes; repeat/independent scene validation remains necessary for broader claims.

Outputs: `results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/`
Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_growth_entropy_blur_panel.py`

Each completed run is appended below and to INDEX/STATUS; failures are retained and stop the panel.

**2026-09-26 growth/entropy/blur immediate_t1_blur / aria:** execution=True, audit=True, PSNR=25.614341794079497, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/immediate_t1_blur/aria.

## Implementation validation

CPU30 tests PASS plus selection-rule guard check. Growth reservations/cancellations earn no admission credit; committed prefixes do. Mandatory KFs are ungated. Independent audit rejects admissions before their κ threshold. `sampler_pool_tau` now reports actual separate KF/dense weights, avoiding reliance on the inherited combined-pool `effective_tau` summary. No sampling formula/default behavior change for immediate membership.

**2026-09-26 growth/entropy/blur immediate_t1_blur / rpng:** execution=True, audit=True, PSNR=25.089143038225604, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/immediate_t1_blur/rpng.

**2026-09-26 growth/entropy/blur immediate_t1_blur / utmm:** execution=True, audit=True, PSNR=22.09905055128498, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/immediate_t1_blur/utmm.

**2026-09-26 growth/entropy/blur k4_t1_blur / aria:** execution=False, audit=False, PSNR=None, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/k4_t1_blur/aria.

## v1 runtime guard failure / v2 continuation

v1 completed all3 immediate/tau1/blur baselines, then κ4/Aria failed before training because OnlineMapperRuntime still shared the paired full-pool-only guard. Preserve failure and logs; no PSNR. Fix restricts that guard to paired schedule, with unified runtime growth wiring added to the existing regression test. No optimizer/sampler changes relative to v1. v2 reuses the3 already validated immediate baselines, records source differences explicitly, re-audits them and runs remaining18conditions. New output `gpu40_v2`; original `gpu40_v1` retained.

**2026-09-26 growth/entropy/blur k4_t1_blur / aria:** execution=True, audit=True, PSNR=25.684785697296377, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k4_t1_blur/aria.

**2026-09-26 growth/entropy/blur k4_t1_blur / rpng:** execution=True, audit=True, PSNR=25.108031738556182, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k4_t1_blur/rpng.

**2026-09-26 growth/entropy/blur k4_t1_blur / utmm:** execution=True, audit=True, PSNR=22.043257966453645, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k4_t1_blur/utmm.

**2026-09-26 growth/entropy/blur k8_t1_blur / aria:** execution=True, audit=True, PSNR=25.700358368968235, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k8_t1_blur/aria.

**2026-09-26 growth/entropy/blur k8_t1_blur / rpng:** execution=True, audit=True, PSNR=24.97500921369673, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k8_t1_blur/rpng.

**2026-09-26 growth/entropy/blur k8_t1_blur / utmm:** execution=True, audit=True, PSNR=21.978632038022266, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k8_t1_blur/utmm.

**2026-09-26 growth/entropy/blur k16_t1_blur / aria:** execution=True, audit=True, PSNR=25.831853204101098, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t1_blur/aria.

**2026-09-26 growth/entropy/blur k16_t1_blur / rpng:** execution=True, audit=True, PSNR=25.133578357181033, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t1_blur/rpng.

**2026-09-26 growth/entropy/blur k16_t1_blur / utmm:** execution=True, audit=True, PSNR=22.07020735446318, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t1_blur/utmm.

**2026-09-26 growth/entropy/blur k16_t0.25_blur / aria:** execution=True, audit=True, PSNR=23.529499297833624, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t0.25_blur/aria.

**2026-09-26 growth/entropy/blur k16_t0.25_blur / rpng:** execution=True, audit=True, PSNR=24.73448858175192, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t0.25_blur/rpng.

**2026-09-26 growth/entropy/blur k16_t0.25_blur / utmm:** execution=True, audit=True, PSNR=21.865269357775464, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t0.25_blur/utmm.

**2026-09-26 growth/entropy/blur k16_t4_blur / aria:** execution=True, audit=True, PSNR=25.899103892668514, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_blur/aria.

**2026-09-26 growth/entropy/blur k16_t4_blur / rpng:** execution=True, audit=True, PSNR=25.205477929330087, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_blur/rpng.

**2026-09-26 growth/entropy/blur k16_t4_blur / utmm:** execution=True, audit=True, PSNR=22.234002501876265, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_blur/utmm.

**2026-09-26 growth/entropy/blur k16_t4_no_blur / aria:** execution=True, audit=True, PSNR=25.885081065520076, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_no_blur/aria.

**2026-09-26 growth/entropy/blur k16_t4_no_blur / rpng:** execution=True, audit=True, PSNR=25.23090243983913, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_no_blur/rpng.

**2026-09-26 growth/entropy/blur k16_t4_no_blur / utmm:** execution=True, audit=True, PSNR=22.219356218973797, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_no_blur/utmm.

## 완료

[결과 요약](SUMMARY.md) / [구현](IMPLEMENTATION.md)
