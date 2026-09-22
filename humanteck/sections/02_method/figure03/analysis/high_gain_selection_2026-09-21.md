# Fig. 3 후보 재선정 — PSNR 차이와 시각적 차이 우선

사용자 피드백에 따라 초기 관측 편의성을 우선했던 table_01 추천을 재검토했다.
현재 1순위는 **Aria aria301_305 / frame 1180**이다.
실측 수렴 곡선은 아직 없으며 이 결정은 최종 지도 기반의 시각화 후보 선정이다.

## 수행한 확인

- 기존 Fig. 2 전체 held-out per-view 순위와 17개 scene 평균을 재검토했다.
- aria301_305의 기존 F01(frame 1220), F02(frame 840)와 다른 장면의 이미지를 비교했다.
- GPU compute process가 없는 것을 확인하고, **기존 최종 PLY를 그대로 사용**해
  frame 640 / 980 / 1180 / 1410을 추가 렌더링했다. optimizer update는 없다.
- 전처리, 평가 pose, GT>0 mask를 기존 evaluator와 동일하게 적용했다.
  baseline/ours pose 일치를 확인하고 재계산 full-view PSNR이 기존 로그와 0.005 dB 이내로 일치함을 검증했다.
- 저장 PNG에 적용한 것은 기존 Fig. 2와 같은 90도 display rotation뿐이다.
  비교판은 동일 ROI를 SVG clipPath로 표시하고 Inkscape로 PNG를 출력했다.
  선명화·색 보정·생성형 pixel 변경은 없다.

## 장면 수준

aria301_305 전체 고정 held-out 539뷰의 최종 평균은 **21.9267 → 25.1124 dB (+3.1857)**.
기존 table_01의 장면 평균 차이 +1.6526 dB보다 크다.
539뷰 중 114뷰에서 +5 dB 이상, 34뷰에서 +7 dB 이상 차이가 있었다.
이 비율은 기존 최종 per-view 결과의 기술통계이며 수렴 속도나 통계적 유의성 지표가 아니다.

## 프레임 후보

| frame index | Baseline | Ours | 차이 | 시각적 판단 |
|---|---:|---:|---:|---|
| **1180** | **21.6766** | **33.1488** | **+11.4721** | 1순위. 책상·의자의 경계, 중앙 통로와 배경 벽이 함께 보임 |
| 1220 | 17.4926 | 29.2023 | +11.7096 | 전체 view gain 최대. 다만 일부 책상이 잘려 물체/빈 벽의 균형은 1180이 더 좋음 |
| 980 | 22.7590 | 30.0826 | +7.3237 | 여러 줄의 책상과 의자를 넓게 보여주는 대안 |
| 1410 | 21.3927 | 30.2412 | +8.8485 | 옆면에서 책상·통로를 보는 대안 |
| 640 | 16.6972 | 21.1707 | +4.4735 | 초반 후보지만 Ours 절대 품질이 낮아 우선순위를 낮춤 |

표 수치는 **crop PSNR이 아니라 각 전체 평가 이미지 PSNR**이다.
frame 1220의 정확한 값은 기존 F01 provenance와 비교판을 기준으로 한다.

## 1180의 제안

- UID: `1475350688062.jpg`.
- 확대 ROI: display rotation 적용된 464×464 이미지에서 `(0, 195, 464, 445)`.
- 넓은 crop으로 책상과 의자, 통로를 함께 보여준다. 천장 밝은 조명 위주의 기존 자동 crop을 대체한다.
- 같은 평가 카메라와 ROI를 3개 학습 checkpoint에서 재사용한다.
- graph y는 전체 539 held-out 평균이고, inset만 frame 1180이다. +11.47 dB를 scene 곡선 차이로 표시하지 않는다.

Run pair:

```text
results/experiments/exp94_normalized_metric_v2_fixed_eval/aria/aria301_305/
  native_vanilla_render_matched_s0/
  normalized_variance_s0/
```

둘 다 seed 0, 각 17,620 training renders, optimizer step은 baseline 1,376 / ours 1,344.
현재 결과는 Carve off, mapping 비교다. 최종 지도의 시각적 잡음 감소를 별도 geometry 검증으로 대신하지 않는다.
Baseline event상 frame prefix 1183에 도달했을 때 누적 step은 431이다.
따라서 600 / 900 / 1,200 step은 다음 paired 실행의 잠정 inset checkpoint 후보가 될 수 있다.
양쪽 ROI 가시성·map reset·입력 prefix를 확인한 뒤 결정하며, 현재 자료로 그때의 품질을 예측하지 않는다.
이 pair에도 `3dgs_before_final.ply`만 있어 실제 곡선 및 중간 inset은 checkpoint를 추가한 실행이 필요하다.

## 산출물과 재현

- [실제 3후보 비교판 PNG](../candidates/high_gain_review/high_gain_comparison.png)
- [Inkscape 편집 가능 SVG](../candidates/high_gain_review/high_gain_comparison.svg)
- [신규 4view 재렌더 provenance](../candidates/high_gain_review/manifest.json)
- [동일 crop 좌표](../candidates/high_gain_review/crop_selection.json)
- [기존 map 렌더 스크립트](../scripts/review_high_gain_views.py)
- [비교판 SVG/PNG 제작 스크립트](../scripts/build_high_gain_board.py)

렌더 스크립트 최초 실행은 gaussian 모듈 검색 경로 누락으로 중단됐다.
기존 run의 custom_root를 읽어 해당 vigs 경로를 추가한 뒤 4view 모두 검증 통과했다.
비교판 최초 출력은 nested SVG clipping이 Inkscape에서 적용되지 않아 제외했고,
명시적 clipPath로 수정한 최종 PNG에서 라벨·crop 배치를 검수했다.

이 선정은 **개선이 크게 보이는 사례를 의도적으로 고른 것**이며 평균적인 view라는 주장을 하지 않는다.
목표 품질에 더 일찍 도달하는지는 실제 중간 checkpoint 곡선으로 별도 확인한다.
