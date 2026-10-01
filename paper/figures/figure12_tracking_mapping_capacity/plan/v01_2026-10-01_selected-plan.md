# F12 — Tracking 부담과 KF당 mapping 처리량

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

같은 GPU에서도 tracking이 바쁜 구간과 KF 도착 간격에 따라 수행 가능한 mapping 학습량이 달라지는 것을 보여준다.

## 만들 구성

- (a) x=센서 시간, y=공통 시간 bin 안의 tracking 처리시간/GPU busy time과 KF 도착 수. 구간별 tracking 부담을 보여준다.
- (b) 동일 x축에 실제 completed training renders/KF와 Adam steps/KF를 구분해 표시한다. 설정 상한 15/40은 점선으로만 표시한다.
- (c) tracking 부담 또는 KF/s에 따른 실제 renders/KF 산점도. scene별 표식, 1×/1.5×별 색상 또는 패널.
- 부하 이벤트(IMU 초기화, local BA, PGBA 등)는 로그에서 확인된 시점만 주석 처리한다.
- tracking-only / tracking+mapping 실행도 보조 비교로 사용한다.

## 비교 조건과 해석

분모는 final unique KF 수와 mapper admission 수 중 무엇인지 고정한다. reset generation별 재등록, drop된 packet, 초기화 render를 별도 기록한다. KF가 없는 bin은 NA이며 0으로 나누거나 보간하지 않는다. CPU wall time과 겹치는 GPU 작업시간을 단순 차감해 이론적 여유시간으로 해석하지 않는다. 상한이 있는 실행의 실측 throughput은 최대 처리 capacity가 아니다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/live_render_capacity/SUMMARY.md)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/render_budget40_feasibility/SUMMARY.md)
- [README.md](../../../../context/experiments/campaigns/06_gain_attribution/fifo_live/README.md)

## 다음 제작 작업

현재 총량 기록을 먼저 활용하고 timestamp별 tracker/mapper event 로그의 가용성을 감사한다. 최대 capacity를 주장하려면 backlog·상한 비활성 진단과 tracking 지연 조건을 별도로 고정한다. 생산 설정은 이 계획에서 변경하지 않는다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.
