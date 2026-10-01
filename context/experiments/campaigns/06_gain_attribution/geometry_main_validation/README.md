# Geometry merged-main validation — 2026-09-30

Question: Does main's optional D3 geometry path retain the previously established held-out PSNR gain over official vanilla?

- Main `a2f3f62b`; frozen causal inputs identical to previous main validation.
- Four scenes: Aria1253, RPNG table_06, UTMM square-1, Aria1253rot.
- Fresh D3 and fresh official vanilla per scene, seed0. Previous native fixed40 results are historical references, not new native runs.
- Preserve fixed40 3:3:6, per-image Adam, kappa16/tau4, PPM mean2.5/span2, birth denominator multiplier.8, protected prune .1/300.
- D3 defaults .0315 hard/.25 main/.95 proxy opacity; fixed depth-backward raster + warp. Dense full gradients; maintenance off; no density changes.
- Training renders 40/KF at every arrival. D3 auxiliary renders counted separately; **not an equal total-render or wall-time comparison**.
- Saved-map evaluation twice, same fixed held-out cohort and shared trajectories. No concurrent live tracker claim.
- Record failures, do not tune to recover favorable results. Geometry quality is not established by held-out RGB PSNR alone.
- Runner `benchmarks/online_gs/campaigns/gain_attribution/run_geometry_main_validation.py`.
- Results `results/campaigns/gain_attribution/geometry_main_validation/`.

2026-09-30 geometry main aria/d3: PSNR=25.749060383279815, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/aria/d3

2026-09-30 geometry main aria/vanilla: PSNR=20.872029646662355, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/aria/vanilla

2026-09-30 geometry main rpng/d3: PSNR=25.128307569349133, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rpng/d3

2026-09-30 geometry main rpng/vanilla: PSNR=22.678571195860165, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rpng/vanilla

2026-09-30 geometry main utmm/d3: PSNR=22.09443043779444, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/utmm/d3

2026-09-30 geometry main utmm/vanilla: PSNR=18.87227068123994, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/utmm/vanilla

2026-09-30 geometry main rot/d3: PSNR=24.98509907956983, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rot/d3

2026-09-30 geometry main rot/vanilla: PSNR=21.830012555982247, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rot/vanilla

**2026-09-30 geometry main GPU 검증 완료:** main a2f3f62b에서 D3+fixed raster/warp 4회와 official vanilla 4회 새 실행, 각 지도 2회 held-out 평가 통과. Aria/RPNG/UTMM/rot 이득 +4.877/+2.450/+3.222/+3.155 dB(평균 +3.426). 이전 native 저장 결과 대비 평균 −0.087 dB. 입력 prefix 학습량·trajectory·cohort 일치. D3는 40 training renders/KF 외 약 20~21 proxy renders/KF 추가하므로 동일 총 연산 비교 아님. maintenance off/density 유지; 독립 geometry GT는 미평가. 기본 recipe는 변경하지 않음.

[Summary](SUMMARY.md)
