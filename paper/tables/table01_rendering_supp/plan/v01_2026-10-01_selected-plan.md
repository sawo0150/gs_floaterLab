# T1-supp — 모든 sequence별 rendering 비교

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

VIGS-SLAM 부록 Table 18–20처럼 모든 sequence의 점수와 dataset 평균을 확인할 수 있게 한다.

## 만들 구성

- dataset별 패널, 행=Metric / Method, 열=각 Sequence / Avg.
- metric block: PSNR, SSIM, LPIPS, #Gaussians(k). T1-main과 같은 방법 목록을 유지한다.
- RPNG table_01–08, UTMM 8 sequences, Aria 4 sequences의 자리와 명시적인 미실행 표기를 둔다.
- source manifest에서 빠진 UTMM slow-straight-1도 행/열을 지우지 않고 상태를 기록한다.
- 온라인 종료 지도를 주 표로 사용한다. final color refinement 결과를 넣으면 별도 조건 표로 분리한다.

## 비교 조건과 해석

T1-main과 같은 run_id/checkpoint/metric evaluator를 사용한다. 과거 19-scene replay와 17-pair 시스템 결과를 하나의 평균에 섞지 않는다. dataset별 mean은 각 metric에 필요한 동일 paired cohort로 계산한다. 실패 때문에 공통 subset을 쓰면 전체 결과와 n/N를 함께 제시한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [5_results.tex](../../../latex/sec/5_results.tex)
- [manifest.json](../../../../context/experiments/ERCB_ablation/benchmark-B/evidence/manifest.json)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/main_validation/SUMMARY.md)

## 다음 제작 작업

VIGS-SLAM 본문/부록 구조를 확인했다. sequence별 빈칸 layout을 준비하고, 같은 원본에서 main과 supplementary mean 일치 여부를 자동 검증한다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.

## 표 틀

[방법 행과 sequence별 빈칸을 포함한 layout](layout.md).
