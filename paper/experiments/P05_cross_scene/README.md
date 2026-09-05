# P05 — Cross-Scene 일반화

| 항목 | 값 |
|---|---|
| 세우는 claim | A4 |
| 비교 arm | 최종 config 고정, 장면만 변경 |
| 핵심 지표 | held-out PSNR/SSIM/LPIPS, late temporal bins, 3회 mean±std |
| 장면 | aria1253, rot, 301_305, 12F |
| 머신 | 양쪽 |
| 담당 | 나 |
| 상태 | 미착수 |

> ⚠ exp59에서 aria1253 전용 튜닝이 rot −1.85dB, 305 16.95dB로 무너진 전례. **절대 프레임 경계 하드코딩 제거가 선결.**

- **계획(사전등록)** → [`plan/CURRENT.md`](plan/CURRENT.md)
- **결과** → [`result.md`](result.md) (append-only)
- **평가 계약** → [`../protocol/CURRENT.md`](../protocol/CURRENT.md)

## 버전 이력

| 종류 | 버전 | 날짜 | 트리거 | 무엇이 바뀌었나 |
|---|---|---|---|---|
| plan | [v01](plan/v01_2026-09-05_initial.md) | 2026-09-05 | paper/ 폴더 개설 | 최초 작성 |
