# F1 — A안: 실제 장면 중심 teaser

작성: 2026-10-01. 사용자 A안 선택에 따른 실제 자료 제작 계획. 원고 TeX는 변경하지 않는다.

## 목적

큰 장면 지도 → 같은 위치의 외관 비교 → 실제 수렴 그래프라는 A안의 읽기 순서를 유지한다. 생성형 mockup의 내용을 실험 결과처럼 재현하지 않고, 확인된 기존 결과만 배치한다.

## 만들 구성

- 왼쪽: RPNG table_06의 실제 저장 Gaussian 지도와 실제 추정 keyframe pose/frustum. 표시용 spatial cutaway임을 명시한다.
- 가운데 위: 기존 F04의 held-out frame 1420, 동일 ROI [440,40,564,164], VIGS-SLAM/Ours 비교. 아래는 동일 평가 카메라의 실제 expected-depth 렌더를 공통 색 범위로 배치한다.
- 오른쪽: 같은 capture run의 555-view held-out PSNR, 28개 실측점을 모두 유지한다. x축은 로그의 training renders이며 optimizer steps나 wall-clock 시간으로 부르지 않는다.
- SVG 180×61mm 전후, Times New Roman 실제 폰트, Inkscape PDF 변환 후 Poppler 재렌더 검수.
- RGB/지도/깊이/curve는 동일 scene 및 capture pair의 final checkpoint에서 연결한다. baseline/ours 각각 34,437 training renders이며 중간 checkpoint마다 input prefix까지 같다는 주장은 하지 않는다.

## 비교 조건과 해석

이 historical run은 Carve off다. 기하 패널은 **실제 depth 시각화**이지만 독립 GT 검증이나 Carve ablation이 아니며, 제목도 Reliable geometry 대신 Rendered depth로 제한한다. 최종 full-method teaser로 승인하기 전에 기하 증거를 교체해야 한다. 표면이 보이도록 자른 지도는 공간 문맥용으로만 쓰고, 비교 crop/depth는 절단하지 않은 원본 지도를 렌더한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../humanteck/sections/02_method/figure02/README.md)
- [README.md](../../../../humanteck/sections/02_method/figure01/production/README.md)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/geometry_main_validation/SUMMARY.md)

## 다음 제작 작업

저장 PLY를 읽기 전용 렌더하여 후보 시점을 확인하고, SVG 연결선은 동일 투영으로 계산한다. RGB 재렌더 PSNR이 기존 frame 평가와 0.005 dB 이내로 일치하는지 검증한다. 새 학습이나 실험 recipe 변경은 하지 않는다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- `candidates/real_A_2026-10-01/`: 실제 렌더 및 자산 provenance.
- `output/scene_centered_A_2026-10-01/`: 편집 가능한 SVG, PDF, PNG, caption, provenance, QA.
- `scripts/build_scene_centered.py`: 단일 유지보수 코드. 이후 수정은 이 파일에 diff로 적용한다.
- 현재 `current/`와 manuscript는 보존한다. historical draft를 최종 full-method 결과로 자동 승격하지 않는다.
