# VGGT 평가 (닫힌 축, 2026-06-30 종결)

**결론: VGGT는 현 시점 OpenMAVIS 대체재로 부족.** 재검토 조건이 충족되기 전에는 이 축을 다시 열지 않는다.

## 근거

- Frame 수: 16/32/64/80 성공, 64가 최적 균형. **96/128은 CUDA OOM** (병목은 RAM이 아니라 VRAM/attention memory).
- 3DGS 7k 비교 (64 frames): VGGT64 Test PSNR 17.04 vs OpenMAVIS64/MPS 18.65. VGGT는 compact하지만 render 품질 낮음.
- Camera EVO (MPS 기준): OpenMAVIS APE RMSE 0.56m vs VGGT 2.68m — global alignment에서 OpenMAVIS 압승.

## 재검토 조건

chunked inference / lower resolution / point cap 조정 / frame selection 개선 중 하나 이상 확보 시.

## 원본 기록

- 상세 수치: `legacy_20260707/current_findings.md` §4-5, `legacy_20260707/experiment_timeline.md` Phase 5-7
- EVO report: `results/archive/evo_camparam_mps_vggt_openmavis_64_20260630/report.md` (openmavis64_* 파일은 invalid, `openmavis_orb_64.*`가 올바름)
- result dirs: `results/archive/vggt_smoke_*`, `results/archive/exp13_vggt64_3dgs_7k_retry_20260630_112335`, `results/archive/exp14_openmavis64_3dgs_7k_20260630_112820`
