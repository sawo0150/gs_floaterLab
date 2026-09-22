# Fig.3 table_06 — 높이 축소·frame 교체 (2026-09-21)

[최종 PNG](../../output/fig3_table06_compact_frame355.png) · [편집 SVG](../../output/fig3_table06_compact_frame355.svg) · [논문용 PDF](../../output/pdf/fig3_table06_compact_frame355.pdf)

사용자의 명시적 요구는 **세로를 줄여 논문 지면 점유를 줄이는 것**이다.
가로 86.49 mm를 유지하고 높이를 63.42 → 46.13 mm로 줄였다(27.27% 감소).
공통 선형 y축은 14–25.5 dB다. 전체 555 held-out view 평균의 원래 28개
checkpoint를 모두 유지했으며 PSNR 수정, smoothing, checkpoint 제외는 없다.

## 이미지 선정과 검증

Fig.2의 frame1420·2235를 제외하고 저장된 per-view PSNR을 재집계했다.
[후보 순위](frame_ranking.csv)는 1200–2600 step의 평균·최소 gap을 함께 보며,
최종 gap 하나로 선택하지 않는다. 205/355/685/905/950/1110/1630/2370의
800/1400/2600 step, 양쪽 arm을 실제 저장 map에서 렌더링했다(총 48장).
기존 평가와 동일 RGB 전처리·평가 pose·GT>0 mask를 사용하고 원본 per-view
PSNR과 0.005 dB 이내 재현을 검증했다.

선정 frame355는 Fig.2와 다른 면의 포스터를 보여준다. 원본 616×344 이미지에서
동일 crop (230,100,390,180)을 세 시점·양쪽 arm에 적용했다. 원형 표시와
연결된 상자·글자의 선명도 차이를 확인할 수 있다. 전체 frame PSNR 차이는
800/1400/2600 step에서 각각 +2.44/+1.64/+2.01 dB다. 이 값은 crop PSNR이
아니며, 그래프 y값은 여전히 전체 555뷰 평균이다. 선명화나 생성 이미지 보정은 없다.

[8개 후보 전체 보기](../../candidates/table06_revision/candidate_overview.png) ·
[crop 비교](../../candidates/table06_revision/crop_review.png) ·
[선정 crop 세 시점](../../candidates/table06_revision/selected_crop.png) ·
[48장 PSNR 검증](../../candidates/table06_revision/render_checks.json)

## 수평선과 화살표

모호한 “Same PSNR”을 **Baseline final: 22.69 dB**로 교체했다.
실제 기준은 baseline 최종값 22.68787652093011 dB이고 수평선·마름모·수직선은
각 곡선과의 첫 교점에 정확히 맞췄다. 200-step checkpoint 사이 선형 보간으로
Ours 약 1189.60 step, baseline 약 1974.20 step, 차이 약 784.60 step이다.
그림의 “≈ 780 iter.*”는 이를 10-step 단위로 반올림한 설명용 추정치다.
정확히 관측된 도달 step, 지속적으로 기준을 넘는 시점, wall-clock 가속률은 아니다.
Baseline은 이후 비단조적으로 변하며 최종값이 자신의 최고값보다 낮다.

이 장면·frame은 사후 illustration 선택이다. 곡선에는 incremental coverage와
pose correction이 포함되고 native iteration당 작업량·입력 prefix가 다를 수 있다.
전체 run의 rendering budget은 맞췄지만 이 그림만으로 순수 optimizer/ERCΒ
가속이나 모든 장면의 개선을 입증하지 않는다. 전체 장면 표는 별도로 유지한다.

## 캡션 초안

> Online mapping quality on RPNG table_06. Curves show mean PSNR over 555 fixed
> held-out views. Insets compare the same crop of frame 355 at 800, 1,400, and
> 2,600 mapping iterations (upper: VIGS-SLAM; lower: ours). The horizontal
> reference denotes the baseline's final PSNR. *The iteration difference at
> the first crossing of this reference is estimated by linear interpolation
> between checkpoints. Curves include mapping and pose-correction effects
> under a matched total rendering budget.

## 재현·검수

도판만 다시 만들기(CPU):

```bash
python humanteck/sections/02_method/figure03/scripts/build_table06_compact.py
```

Inkscape SVG → PDF → Poppler PNG로 출력했다. 전체 크기와 200 dpi 단 폭 크기에서
레이블·이미지·화살표 겹침 및 잘림을 확인했다. 원고 TeX에는 아직 삽입하지 않았다.
[데이터·이미지 provenance](../../output/fig3_table06_compact_frame355_provenance.json) ·
[검증 결과](../../output/qa/table06_compact_validation.json)
