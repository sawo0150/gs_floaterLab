# Figure 레이아웃 초안 검수 — 2026-10-01

검수 범위: 선택한 F1/F2/F3/F4/F5/F6/F7/F9/F11/F12의 `current/figure.png`, caption 및 provenance. 모든 PNG를 원본 해상도로 시각 확인했다. ID는 제작 관리용이며 최종 LaTeX 번호가 아니다. [전체 후보판](contact_sheet_draft.png)은 비교를 위한 축소 미리보기다.

이번 산출물은 **논문 배치·비교 구성 검토용 초안**이다. F1/F5/F6는 내장 image_gen으로 생성한 가상 장면, F2는 HumanTech 설명도 재사용, F3는 실제 과거 HumanTech 결과 재사용, 나머지 5개는 합성 수치 그래프다. 어느 자산도 최신 recipe의 새 실험 결과로 해석하지 않는다. 신규 학습·GPU 실험·원본 HumanTech 자산 수정은 하지 않았다.

| ID | 자산 성격 | 시각 검수와 남은 작업 |
|---|---|---|
| F1 | AI 생성 teaser | `DRAFT - AI-GENERATED LAYOUT MOCKUP`과 `Not experimental results`가 크고 명확하다. Baseline/Ours/Reference 3열과 RGB/ellipsoid 2행이 분리되며 라벨 충돌이 없다. 가상 장면이므로 최종본에서 실제 동일 view·budget·ROI로 전부 교체한다. |
| F2 | HumanTech overview 재사용 | 3개 영역과 성장·선택·최적화 연결선이 읽힌다. `Rendered normal` 유지. 원본 자산 내부에는 draft 표기가 없으므로 항상 새 caption 및 current README와 함께 사용한다. `Free-Space Carve Loss`, `+κ updates`, `RGB (K+I) · Depth/normal (K)`는 과거 설명이며 최신 D3/성장 예산/입력 구성을 확정한 뒤 라벨과 경로를 대조해야 한다. map cutaway는 Carve 효과 증거가 아니다. |
| F3 | 실제 과거 HumanTech 곡선·렌더 | 검정 dashed baseline/파랑 ours, 1.4k checkpoint guide와 동일 ROI 3열이 명료하고 충돌이 없다. 19 dB 아래는 압축 축척이며 물결 separator로 표시된다. 이 자산의 `1,000 fewer iter.*`, 1400/2400 값 및 `Ours`는 과거 실행만 가리킨다. *는 baseline 최고 PSNR에 도달한 **첫 저장 checkpoint** 비교이며 지속 도달이나 시간 절감의 증거가 아니다. 최신 checkpoint 곡선·렌더·threshold 분석과 묶어서 교체한다. |
| F4 | dummy 2-panel 그래프 | 큰 draft marker, method별 `(dummy)` 라벨, PSNR/dB와 depth/cm 축 단위가 명확하다. 범례가 곡선과 겹치지 않는다. 실측 전에는 seconds가 sensor time인지 wall time인지, region/first-observed 정의와 공통 mask를 확정해야 한다. |
| F5 | AI 생성 RGB 비교 | draft marker와 `Fictional scenes; not experimental results`가 명확하다. 3열×3행, 동일 위치를 가리키는 색별 ROI와 확대 panel의 구성이 읽힌다. 가상 장면명이나 값이 실제 RPNG/UTMM/Aria 결과로 붙지 않았다. 모든 사진은 matched held-out render로 교체해야 한다. |
| F6 | AI 생성 geometry 비교 | Geometry term off/on/Reference 라벨과 비측정 경고가 명료하다. 하단은 wireframe이 아닌 **꽉 찬 타원체**로 표면과 허공 구조를 보여준다. 상단은 depth-like 도식이며 계량 color scale은 없다. 실제 깊이 비교로 바꿀 때 공통 color range/단위·clip/sigma·독립 reference를 명시한다. |
| F7 | dummy geometry 곡선 | draft marker와 dummy 범례, training-renders/오류율/완전성 단위가 명확하다. 두 범례 모두 곡선과 충돌하지 않는다. 실측판에는 geometry off/on arm 정의, 공통 관측영역·독립 GT·threshold 및 보조 렌더 연산량을 기록한다. |
| F9 | dummy sampling 곡선 | 15/30/60 updates/KF 세 패널과 held-out PSNR 축이 읽힌다. `ERCB/ERVS placeholder`는 아직 확정하지 않은 비교의 자리 표시다. RR–interval ERCB와 현재 per-view ERVS를 같은 실험·알고리즘으로 합쳐 해석하지 않는다. 실제 수치 설치 때 단일 정확한 policy 라벨과 step 정의를 사용한다. |
| F11 | dummy wall-time 곡선 | 상단 품질/하단 누적 render, 1×/1.5×가 분리되며 축·범례 충돌이 없다. caption은 60초 기록을 90초로 재생하는 1.5× 의미를 명시한다. 실측으로 교체할 때 실제 snapshot, tracking 동시 실행, queue·zero-tail·초기화/모델 load 규칙을 연결한다. |
| F12 | dummy tracking/throughput 그래프 | 최종 PNG에서 sensor time/추적 부하/KF arrivals/training-renders 단위, (a) 두 선의 통합 범례, (b) 하단 범례가 명료하며 곡선·라벨과 겹치지 않는다. (c) 점은 단색으로 통일돼 설명되지 않은 색 인코딩이 없다. 설정 상한과 실측 throughput을 구분하며 최대 hardware capacity 결과로 해석하지 않는다. |

F3의 원본 provenance: RPNG `table_06`, fixed held-out 555뷰, 각 method 14개 측정점, Carve disabled, frame1420/1400 iteration 렌더와 동일 ROI `(440,40,564,164)`. 원본 값과 표시 좌표는 변경하지 않았다. 이 정보는 historical 자산 확인용이며 최신 CVPR 방법의 성능 주장이 아니다.

## 수정 확인

- 1차 검수: F12 범례/점 색 설명 수정 권장, F3 캡션의 `*` 정의 보완 권장. 담당 builder에 전달했다.
- 2차 검수: F12 (b) 범례가 하단 여백으로 이동했고 (c)는 단색으로 바뀌었다. (a)에 통합 범례가 추가됐으나 회색 KF-arrival 곡선의 오른쪽 peak가 글자와 겹쳐, 오른쪽 축 상한 확대를 다시 요청했다. F3 캡션에 historical 첫 저장 checkpoint 설명이 추가됐고 apostrophe LaTeX escaping은 추가 확인을 요청했다.
- 최종 검수: F12 오른쪽 축이 0–2.7 KF/s로 확장돼 (a) 범례 겹침이 해소됐다. F3 caption의 apostrophe와 별표 정의가 정상이다. 10개 자산 모두 전체 폭 `figure*` 배치로 바뀌어 F1/F3의 단열 축소 우려를 줄였다. 새 current README에는 F2의 설명용 map 및 과거 라벨, F3의 historical checkpoint 정의를 보완했다.
- 10개 figure의 `stage=layout_draft` 및 PDF SHA 일치를 확인했다. AI PNG는 보존 원본 해시와 같고, F2/F3 PNG/PDF/SVG는 HumanTech source와 같다. 5개 graph의 JSON에는 `synthetic=true`, `experimental_evidence=false`가 명시되어 있다.
- 논문 PDF에 배치한 뒤의 실제 글자 크기·캡션 연결·열 폭은 root의 PDF 검수에서 별도로 확인한다.
