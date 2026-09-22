# Fig.3 table_06 높이 축소·frame355 렌더 검증

## 최신 선택 — frame1420

사용자가 Fig.2와 같은 frame1420을 선택했다. 동일 ROI (440,40,564,164)의 실제
800/1400/2600 checkpoint 렌더 6장을 정사각형으로 넣고 높이46.13 mm·하단 범례를
유지했다. 원본 curve 28점·이미지 hash 보존 확인, Inkscape PDF→PNG 검수 완료.
신규 학습·GPU 평가 없음. 수평선은 v2처럼 없는 상태다.
[선택본과 캡션](../../../humanteck/sections/02_method/figure03/analysis/table06_revision/frame1420_selected.md).

## 추가 — v2 레이아웃·수평선 재검토

사용자 피드백으로 장면 제목·상하 arm 설명을 그림에서 삭제하고 범례를 하단 가운데로
옮겼다. 86.49×46.13 mm 크기와 원본 곡선 28점은 유지했다. Baseline-final 교점은
계산상 맞지만 비단조적 곡선의 수렴 속도로 읽기 어려워 수평선·화살표를 제거했다.
22.5 dB 기준 baseline의 첫 sampled 도달은1400, 이후 끝까지 유지 시작은2000이며,
23 dB는 마지막에 미달한다. Threshold와 도달 정의에 따른 민감도를 기록했다.

기존 48장 렌더를 재사용해 8후보의 동일 crop·GT 위치·3시점 비교판을 만들었다.
1110(도형),950(의자·책상),685(포스터)가 대안이며,2370은1400-step에서 −0.22 dB라
후기 품질 이외의 수렴 근거로는 부적합하다. Frame 재선택 전 그림은355를 임시 유지.
신규 학습·GPU 평가 없음. [v2 결과와 후보](../../../humanteck/sections/02_method/figure03/analysis/table06_revision/layout_v2.md).

날짜: 2026-09-21. 기존 저장 map의 추가 시각화 평가이며 신규 학습은 없다.

사용자가 선택한 table_06 곡선을 유지하면서 논문 지면 점유를 줄이기 위해 동일
86.49 mm 폭에서 높이를 63.42→46.13 mm(−27.27%)로 줄였다. y축은 14–25.5 dB로
확대했으며 전체 555 held-out view 평균 28개 원본 checkpoint를 모두 유지했다.

Fig.2 frame1420·2235를 제외하고 8개 후보를 세 시점·두 arm으로 렌더링했다(48장).
공통 평가 pose·전처리·GT>0 mask를 유지하고 원본 per-view PSNR 대비 오차 0.005 dB
이내를 확인했다. Frame355의 다른 포스터 면을 선택했고 동일 crop을 사용했다.
800/1400/2600 step의 전체 frame PSNR gap은 +2.44/+1.64/+2.01 dB다.

기준 수평선은 실제 baseline 최종값 22.6878765 dB에 맞췄다. 첫 교점의 선형 보간
추정은 Ours1189.60/base1974.20 step이며 “≈780 iter.*”로 표시했다. 정확한 측정
step·지속 도달·wall-clock 가속을 뜻하지 않는다. 기존 curve의 coverage/pose
correction 및 사후 장면 선택이라는 해석 한계는 유지한다.

Inkscape PDF와 Poppler PNG를 실제 단 폭에서 검수했다. 데이터 hash·28개 좌표·6장
이미지 hash·48장 PSNR 재현·crop 범위·교점을 검증 결과 파일에 기록했다.
원고 TeX는 수정하지 않았다.

- [도판·선정 기록·캡션](../../../humanteck/sections/02_method/figure03/analysis/table06_revision/README.md)
- [PNG](../../../humanteck/sections/02_method/figure03/output/fig3_table06_compact_frame355.png)
- [검증 결과](../../../humanteck/sections/02_method/figure03/output/qa/table06_compact_validation.json)
- [기존 전체 장면 탐색](fig3_scene_search_2026-09-21.md)
