# Fig.3 frame1420 선택본

2026-09-21 사용자 선택: frame1420. [PNG](../../output/fig3_table06_compact_frame1420.png) · [SVG](../../output/fig3_table06_compact_frame1420.svg) · [PDF](../../output/pdf/fig3_table06_compact_frame1420.pdf)

Fig.2와 동일 ROI (440,40,564,164)를 800/1400/2600 iteration의 실제 checkpoint
렌더에 적용했다. 정사각형 비율을 보존하고 위 Baseline/아래 Ours 순서로 그래프
안에 배치했다. 기존 555-view PSNR 곡선 28점, 14–25.5 dB 축, 86.49×46.13 mm
크기, 상단 문구 없음, 하단 가운데 범례를 유지했다.
800-iteration 연결선은 레이블 왼쪽으로 옮겨 곡선·글자와의 겹침을 해소했다.

수평선은 v2처럼 없는 상태다. Baseline 최고 PSNR을 사용한 첫 도달 화살표는
앞선 대화에서 검토한 별도 표기안이며 이번 frame 교체에는 추가하지 않았다.
Baseline 최고 23.28134 dB@2400, Ours 첫 sampled 도달1400이나 이후 하락·재도달하므로
추후 추가하면 첫 도달임을 명시해야 한다.

기존 PNG 원본 hash 6개, curve 좌표 28점 동일성, crop·균일 배율을 검증했다.
PDF를 PNG로 렌더링해 전체 크기와 단 폭 크기에서 확인했다. 신규 학습·GPU 평가 없음.
원고 TeX에는 아직 설치하지 않았다.

> Online mapping quality on RPNG table_06. Curves show mean PSNR over 555 fixed
> held-out views as a function of mapping iterations. Insets show the same
> view and crop as Fig. 2 (frame 1420) at 800, 1,400, and 2,600 iterations
> (upper: VIGS-SLAM; lower: ours). Curves include mapping and pose-correction
> effects under a matched total rendering budget.

[상세 3시점 비교](../../candidates/table06_review_v2/frame_1420_three_stages.png) ·
[검증](../../output/qa/frame1420_selection_validation.json) ·
[provenance](../../output/fig3_table06_compact_frame1420_provenance.json)

재생성: `python humanteck/sections/02_method/figure03/scripts/build_table06_frame1420.py`
