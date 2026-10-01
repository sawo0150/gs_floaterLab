# T2-supp — 모든 sequence의 시간 조건 비교

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

각 sequence에서 허용 시간과 실제 수행 학습량, 품질, 지연을 모두 확인한다.

## 만들 구성

- 품질 패널: Dataset / Time allowance별 Metric / Method × Sequence / Avg. 구조. PSNR/SSIM/LPIPS/#G.
- 실행 패널: Dataset | Sequence | Allowance | Method | Deadline(s) | Tracking elapsed(s) | Input lag p95(s) | Training renders | Extra geometry renders | Adam steps | Drops | Tail updates.
- T1-supp의 전체 sequence 목록을 공유한다. 각 sequence의 1×/1.5× 두 조건을 별도 기록한다.
- latest FIFO의 대기 packet drop은 학습 pool 삭제와 다름을 caption/각주로 설명한다.

## 비교 조건과 해석

반복 평가 두 번은 독립 학습 seed 두 개가 아니다. queue 이벤트의 reset/rescale/PGBA 보호도 기록한다. 후처리 evaluation-only pose filling은 지도 저장 후 수행하며 학습에 쓰지 않았음을 명시한다. tracking 미완료/지연을 실패 또는 latency로 드러내고 품질 수치만 남기지 않는다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../context/experiments/campaigns/06_gain_attribution/fifo_live/README.md)
- [README.md](../../../../context/experiments/campaigns/06_gain_attribution/fifo_sensor1x/README.md)

## 다음 제작 작업

각 run의 실제 budget·counter·lag·drop·zero-tail 기록을 연결한다. frozen-tracker pilot의 결과는 실제 tracking 표에 넣지 않는다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.

## 표 틀

[방법 행과 sequence별 빈칸을 포함한 layout](layout.md).
