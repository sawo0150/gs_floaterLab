# 5070ti_1.5x_strict — original VIGS hard-deadline baseline

날짜: 2026-09-14
상태: **20-scene canonical queue 실행 중**

## 계약

- GPU: RTX 5070 Ti
- algorithm code: original VIGS-SLAM `origin/main@22ffe24c`
- 입력: RGB timestamp 순서, 원래 시간 간격의 1.5배 wall-clock replay
- 지도 cutoff: 첫/마지막 source timestamp로 정한 고정 final-capture deadline
- ingress: adapter가 decode를 미리 하고 source timestamp에 방출하며, 처리 queue가
  차면 실제 live sensor처럼 가장 오래된 RGB frame을 버림
- zero-tail: deadline 뒤 Gaussian Adam, birth, densify/prune, opacity reset, rescale 0회
- queue: deadline 뒤 pending GS packet 폐기; optimizer drain 없음
- 측정: 실제 `torch.optim.Adam.step()` 완료 횟수. batch/render 수를 step으로 세지 않음
- disabled: final global BA와 26k color refinement
- 평가: 지도 update 없이 full online trajectory를 보간하여 PSNR/SSIM/LPIPS 계산

기존 `5070ti_1.5x_streaming`은 timestamp pacing 뒤 producer backpressure와 final
GS drain을 허용한 `paced + unbounded completion` 결과다. 이 폴더의 결과만 strict
vanilla 기준선으로 사용한다.

## 범위

- Aria 4: `aria1253`, `aria1253rot`, `aria301_12F`, `aria301_305`
- UTMM 8개 전 장면
- RPNG `table_01`–`table_08`

전체 실행 전 RPNG length300, Aria length300, UTMM fast-straight 대표 검증에서
`sensor_eos_audit.json`의 모든 deadline 위반 수가 0임을 확인했다. 다만 vanilla
tracking은 대표 구간에서도 마지막 frame 처리가 0.23--0.66초 늦었으므로 map
strict와 end-to-end strict 판정을 분리한다. 계약 실패 output은 삭제하거나 성공으로
집계하지 않는다.

## 파일

- `streaming_demo.py`: 보존된 adapter의 strict entry point
- `config/`: vanilla dataset config + `Training.parallel=true` overlay
- `run_one.sh FAMILY SCENE`: 단일 장면
- `run_all.sh`: 20개 장면 resume-safe 직렬 실행
- `collect_metrics.py`: strict audit와 held-out 결과 집계
