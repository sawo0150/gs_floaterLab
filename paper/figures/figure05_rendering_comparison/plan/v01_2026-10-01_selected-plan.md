# F5 — 여러 scene의 RGB 비교

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

최종 또는 동일 중간 예산에서 렌더링 개선이 여러 scene과 시각적 구조에서 나타나는지 보여준다.

## 만들 구성

- 행: RPNG / UTMM / Aria 대표 scene, 열: VIGS-SLAM / Ours / GT.
- 전체 영상과 글자·얇은 구조·경계 등의 동일 ROI 확대를 배치한다.
- T1과 같은 고정-work 또는 T2와 같은 고정-time 중 한 조건으로 도판을 구성하고 caption에 명시한다.
- 추가 baseline을 실행하면 해당 열을 추가한다. 렌더가 없는 방법의 가짜 이미지는 만들지 않는다.
- 각 행에 scene/view UID와 비교 budget을 기록한다.

## 비교 조건과 해석

동일 ROI·해상도·렌더 설정을 사용한다. 밝기·선명도 보정으로 차이를 만들지 않는다. held-out 여부를 명시하고 정성 비교에서만 고른 frame의 PSNR을 데이터셋 평균처럼 쓰지 않는다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../humanteck/sections/02_method/figure02/README.md)
- [provenance.json](../../../../humanteck/sections/02_method/figure02/output/provenance.json)
- [README.md](../../../../context/experiments/campaigns/06_gain_attribution/fifo_live/README.md)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/main_validation/SUMMARY.md)

## 다음 제작 작업

최신 지도에서 공통 held-out frame 후보판을 만든 뒤 선택 이유와 모든 crop 좌표를 보존한다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.
