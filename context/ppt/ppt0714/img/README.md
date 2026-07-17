# img/ — PPT 시각자료 (실제 데이터로 렌더됨)

`make_figures.py`가 실제 데이터/이미지에서 아래 16종을 생성한다. `build_ppt.py`의 `IMG_MAP`이
슬라이드별로 이 그림들을 "— 시각자료" 전용 슬라이드에 삽입한다.

## 생성 그림 (make_figures.py)

| 파일 | 내용 | 데이터 소스 | 매핑 슬라이드 |
|---|---|---|---|
| fig_landscape | floater=분지 개념도(두 우물) | 합성 | 4, 28 |
| fig_raycoverage | ray 커버리지 높이별 불균등 | carve_fields.npz transit | 4 |
| fig_auc_plateau | plateau/raw/carve AUC 막대 | 카드 수치 | 6 |
| fig_grad_asym | plateau 0.58×/RGB 2.23× 막대 | exp32 수치 | 6 |
| fig_label_highlight | 표면 vs 라벨 floater(rot) | rot 원본/cleaned ply | 5 |
| fig_region | 사면체 확장 영역 voxel | rot region_mask.npz | 5 |
| fig_rho_section | 빈공간 증거 ρ 수평 단면 | carve_fields.npz | 7 |
| fig_waterfall | exp38–40 7런 region_n 막대 | 카드 표 | 10 |
| fig_ab_render | exp30r vs exp40b 실제 렌더 | exp38_40_visual/ | 10 |
| fig_pareto | 먼지↔test PSNR Pareto | exp42 표 | 12 |
| fig_scenes | 세 장면 대표 이미지 | 각 장면 images/ | 27 |
| fig_sobel_ppm | 이미지+Sobel PPM 히트맵 | 305 image | 14 |
| fig_anchors | SLAM 희소 vs depth 조밀 앵커 | 305 points3D + depth_anchors.npz | 22 |
| fig_huber | depth Huber 보정 산점도 | 305 depth+SLAM | 21 |
| fig_crossscene_auc | 교차 장면 AUC 막대(+0.95) | exp43 수치 | 19 |
| fig_slamfree_ladder | SLAM-프리 vr AUC 사다리 | 12F 수치 | 25 |

## 갱신

```
python context/ppt/make_figures.py          # 그림 재생성
python context/ppt/build_ppt.py             # PPTX 재빌드(그림 삽입)
soffice --headless --convert-to pdf --outdir context/ppt context/ppt/gs_floater_deck.pptx
```

## 아직 텍스트 안내로만 남은 시각자료 (선택 제작)

3D 렌더가 더 필요한 것들: 렌더 A/B 다른 각도, φ 거리장 3D, PPM ConvNeXt판(수제 Sobel만 렌더됨),
파이프라인 다이어그램(슬라이드 24·26) 등. 필요 시 make_figures.py에 함수 추가.
