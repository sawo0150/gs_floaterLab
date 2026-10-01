# F11 — 동일 시간에서의 online 품질 비교

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

동일 학습량 비교에 더해 실제 tracking과 mapping을 함께 실행했을 때 동일 시간의 품질을 그래프로 비교한다.

## 만들 구성

- 주 패널: x=센서 입력 시작 후 실제 elapsed seconds, y=고정 held-out PSNR. VIGS-SLAM/Ours.
- 1×와 1.5× 시간 허용 조건을 별도 패널로 표시한다. 1.5×는 60초 데이터를 90초에 입력하는 조건이다.
- 보조 패널: x=completed training renders, y=PSNR. 동일 iteration 비교는 image/Adam 정의가 같을 때만 사용한다.
- 필요하면 아래 얇은 패널에 input lag와 완료 render 누적량을 붙인다.
- 같은 시간의 지도 비교는 같은 wall-clock checkpoint에서 저장한다. plot용 held-out 평가는 저장 지도에서 따로 한다.

## 비교 조건과 해석

실제 tracking을 함께 실행한다. 모델 warm load 제외 여부, 초기화 포함, optimizer zero-tail, queue capacity를 명시한다. 두 budget의 endpoint만 연결한 선은 budget-response이지 시간 수렴 곡선이 아니다. 최신 live의 RPNG/UTMM tracker 설정 차이는 전체 시스템 비교로 공개하며 mapper-only 효과라 하지 않는다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../context/experiments/campaigns/06_gain_attribution/fifo_live/README.md)
- [LIVE_FIFO_COMPARISON.md](../../../../../VIGS-SLAM-custom/docs/LIVE_FIFO_COMPARISON.md)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/render_budget40_feasibility/SUMMARY.md)

## 다음 제작 작업

현재 4 scenes×2시간조건×2방법의 endpoint는 존재한다. 실제 중간 품질 곡선은 snapshot 시간과 observer overhead를 통제해 추가 수집한다. T2와 같은 run manifest를 공유한다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.
