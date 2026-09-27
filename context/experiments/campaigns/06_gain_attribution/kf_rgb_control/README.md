# KF RGB-only control — predeclared 2026-09-26

Question: does the dense-slot gain require additional viewpoints, or does replacing native KF RGB+depth+normal supervision by RGB-only explain it?

Three arms, all nominal 3:3:6: window native KF / full-pool native KF / auxiliary.
- dense_rgb: auxiliary full dense pool, existing RGB-only function.
- kf_native: auxiliary full KF pool, native RGBD+normal.
- kf_rgb: auxiliary full KF pool, exactly the dense RGB-only function.

KF controls must match selected UID sequence, batches, cumulative counts, and per-image LR exactly. All arms match total and prefix renders and Adam steps (40 renders per KF admission, including map reset re-admissions), same frozen causal tracker inputs and held-out evaluation. Bootstrap pool shortages may change auxiliary allocation between dense and KF arms; report actual counts. Each batch uses distinct images. No blur filter, no densify/prune/phase gate; existing scale projection ON. Seed0, Aria1253/RPNG table_06/UTMM square-1. No scene tuning. Default mapping stays dense_rgb.

Each saved map evaluated twice (evaluator consistency, not independent training repeat). These are development scenes with frozen causal tracking and fixed work, not simultaneous tracking or wall-clock real-time validation. All failures and source changes recorded; fail closed.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_kf_rgb_control_panel.py`
Outputs: `results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/`

**2026-09-26 KF RGB control dense_rgb / aria:** execution=True, audit=True, PSNR=25.59209155308381, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb/aria.

**2026-09-26 KF RGB control kf_native / aria:** execution=True, audit=True, PSNR=24.729860684343876, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_native/aria.

**2026-09-26 KF RGB control kf_rgb / aria:** execution=True, audit=True, PSNR=25.05776095208321, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_rgb/aria.

**2026-09-26 KF RGB control dense_rgb / rpng:** execution=True, audit=True, PSNR=25.11788134531932, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb/rpng.

**2026-09-26 KF RGB control kf_native / rpng:** execution=True, audit=True, PSNR=24.81117957175315, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_native/rpng.

**2026-09-26 KF RGB control kf_rgb / rpng:** execution=True, audit=True, PSNR=25.0034789798496, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_rgb/rpng.

**2026-09-26 KF RGB control dense_rgb / utmm:** execution=True, audit=True, PSNR=22.105193120461923, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb/utmm.

**2026-09-26 KF RGB control kf_native / utmm:** execution=True, audit=True, PSNR=21.41564631756441, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_native/utmm.

**2026-09-26 KF RGB control kf_rgb / utmm:** execution=True, audit=True, PSNR=21.763058300371522, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_rgb/utmm.

## 완료

[결과 요약](SUMMARY.md) / [구현](IMPLEMENTATION.md)
