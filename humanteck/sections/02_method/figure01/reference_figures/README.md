# 참고 논문 도판 모음

2026-09-19. HumanTech overall figure의 loss·sampling·view growth 표현을 조사할 때 확인한 원문 이미지 모음이다.

- `loss_figures/`: 최근 loss 조사에서 참고한 **도판 9개**, 원문 Figure 번호와 캡션을 포함해 추출.
- `full_pages/`: 이전 view-selection·pipeline 조사까지 포함한 **전체 페이지 18개**. 문맥과 수식 확인용.
- 원문 PDF와 공식 URL: [참고문헌 목록](../../../../ref/figure_design/README.md).
- 해석 및 적용안: [loss 조사 메모](../../plan/05_loss_visualization_study_2026-09-19.md), [이전 세부 표현 조사](../../plan/04_detail_visualization_literature_2026-09-19.md).

원문 그림의 연구·디자인 참고용 사본이다. 생성 이미지나 우리의 실험 결과가 아니다. 도판 내용·색상·라벨은 변경하지 않았고 crop만 했다. 우리 제출 도판에 그대로 삽입하지 않는다. 페이지 번호는 저장한 PDF의 1-based 페이지다.

## Loss 도판 빠르게 보기

### DN-Splatter Fig. 1

전체 loss 연결과 작은 기하 도식을 병행하는 구성.

[도판 PNG](loss_figures/dn_splatter_fig01_overview.png) · [전체 페이지](full_pages/dn_splatter_fig01_p02.png) · [원문 PDF](../../../../ref/figure_design/dn_splatter_wacv2025.pdf)

![DN-Splatter Fig. 1 원문 도판과 캡션](loss_figures/dn_splatter_fig01_overview.png)

### mip-NeRF 360 Fig. 6

분포와 화살표로 regularizer의 작용을 설명.

[도판 PNG](loss_figures/mipnerf360_fig06_distortion_mechanism.png) · [전체 페이지](full_pages/mipnerf360_fig05_fig06_p06.png) · [원문 PDF](../../../../ref/figure_design/mipnerf360_cvpr2022.pdf)

![mip-NeRF 360 Fig. 6 원문 도판과 캡션](loss_figures/mipnerf360_fig06_distortion_mechanism.png)

### DS-NeRF Fig. 3

density·alpha·transmittance·termination distribution의 구별.

[도판 PNG](loss_figures/dsnerf_fig03_ray_termination.png) · [전체 페이지](full_pages/dsnerf_fig03_p04.png) · [원문 PDF](../../../../ref/figure_design/dsnerf_cvpr2022.pdf)

![DS-NeRF Fig. 3 원문 도판과 캡션](loss_figures/dsnerf_fig03_ray_termination.png)

### PGSR Fig. 9

기하 관계 안에서 loss의 비교 대상을 표시.

[도판 PNG](loss_figures/pgsr_fig09_multiview_losses.png) · [전체 페이지](full_pages/pgsr_fig09_p08.png) · [원문 PDF](../../../../ref/figure_design/pgsr_2406.06521v2.pdf)

![PGSR Fig. 9 원문 도판과 캡션](loss_figures/pgsr_fig09_multiview_losses.png)

### PGSR Fig. 4

rendered quantities에서 각 loss로 이어지는 supervision 경로.

[도판 PNG](loss_figures/pgsr_fig04_overview.png) · [전체 페이지](full_pages/pgsr_fig04_p04.png) · [원문 PDF](../../../../ref/figure_design/pgsr_2406.06521v2.pdf)

![PGSR Fig. 4 원문 도판과 캡션](loss_figures/pgsr_fig04_overview.png)

### DN-Splatter Fig. 2

normal supervision 방식에 따른 실제 결과 비교.

[도판 PNG](loss_figures/dn_splatter_fig02_normal_supervision.png) · [전체 페이지](full_pages/dn_splatter_fig02_p05.png) · [원문 PDF](../../../../ref/figure_design/dn_splatter_wacv2025.pdf)

![DN-Splatter Fig. 2 원문 도판과 캡션](loss_figures/dn_splatter_fig02_normal_supervision.png)

### mip-NeRF 360 Fig. 5

RGB와 depth를 함께 보여주는 실제 loss ablation.

[도판 PNG](loss_figures/mipnerf360_fig05_distortion_ablation.png) · [전체 페이지](full_pages/mipnerf360_fig05_fig06_p06.png) · [원문 PDF](../../../../ref/figure_design/mipnerf360_cvpr2022.pdf)

![mip-NeRF 360 Fig. 5 원문 도판과 캡션](loss_figures/mipnerf360_fig05_distortion_ablation.png)

### DS-NeRF Fig. 6

MSE와 KL objective의 실제 rendering 비교.

[도판 PNG](loss_figures/dsnerf_fig06_depth_loss_ablation.png) · [전체 페이지](full_pages/dsnerf_fig06_fig07_p08.png) · [원문 PDF](../../../../ref/figure_design/dsnerf_cvpr2022.pdf)

![DS-NeRF Fig. 6 원문 도판과 캡션](loss_figures/dsnerf_fig06_depth_loss_ablation.png)

### 2DGS Fig. 6

normal maps를 통한 regularization ablation.

[도판 PNG](loss_figures/2dgs_fig06_regularization_ablation.png) · [전체 페이지](full_pages/2dgs_fig05_fig06_p07.png) · [원문 PDF](../../../../ref/figure_design/2dgs_siggraph2024.pdf)

![2DGS Fig. 6 원문 도판과 캡션](loss_figures/2dgs_fig06_regularization_ablation.png)

## 전체 페이지 목록

2026-09-19 추가 재검토: [VIGS-SLAM Fig. 2, p.4](full_pages/vigs_slam_fig02_p04.png). Frontend의 pose 출력과 camera frustum의 역할을 확인했다. 이번 pose 재설계에서는 위 목록 중 overview인 CaRtGS Fig.4, GSORB-SLAM Fig.1, DN-Splatter Fig.1, PGSR Fig.4만 디자인 비교에 사용했다.

| 이미지 | 참고 내용 |
| --- | --- |
| [dn_splatter_fig01_p02.png](full_pages/dn_splatter_fig01_p02.png) | Fig. 1: overview 및 기하 도식 |
| [dn_splatter_fig02_p05.png](full_pages/dn_splatter_fig02_p05.png) | Fig. 2: normal supervision 비교, total objective |
| [mipnerf360_fig05_fig06_p06.png](full_pages/mipnerf360_fig05_fig06_p06.png) | Fig. 5: 실제 ablation / Fig. 6: distortion 작용 도식 |
| [dsnerf_fig01_p01.png](full_pages/dsnerf_fig01_p01.png) | Fig. 1: depth-supervised reconstruction 개요 |
| [dsnerf_fig03_p04.png](full_pages/dsnerf_fig03_p04.png) | Fig. 3: ray termination distribution |
| [dsnerf_fig06_fig07_p08.png](full_pages/dsnerf_fig06_fig07_p08.png) | Fig. 6: depth-loss ablation / Fig. 7: training convergence |
| [2dgs_fig03_p04.png](full_pages/2dgs_fig03_p04.png) | Fig. 3: surfel representation·rendering (loss 도식 아님) |
| [2dgs_fig05_fig06_p07.png](full_pages/2dgs_fig05_fig06_p07.png) | Fig. 5: reconstruction / Fig. 6: regularization ablation |
| [pgsr_fig04_p04.png](full_pages/pgsr_fig04_p04.png) | Fig. 4: overview 및 supervision 연결 |
| [pgsr_fig09_p08.png](full_pages/pgsr_fig09_p08.png) | Fig. 9: multi-view photometric·geometric 비교 관계 |
| [urban_radiance_fields_sec4_2_p04.png](full_pages/urban_radiance_fields_sec4_2_p04.png) | §4.2: expected-depth·line-of-sight 수식; 도판이 아니라 방법론 참고 |
| [cartgs_fig03_p03.png](full_pages/cartgs_fig03_p03.png) | Fig. 3: keyframe training count·품질 분석 |
| [cartgs_fig04_p04.png](full_pages/cartgs_fig04_p04.png) | Fig. 4: 기능별 architecture |
| [gsorb_slam_fig01_p02.png](full_pages/gsorb_slam_fig01_p02.png) | Fig. 1: overall pipeline |
| [gsorb_slam_fig02_p03.png](full_pages/gsorb_slam_fig02_p03.png) | Fig. 2: frame 선택 설명 |
| [gsorb_slam_fig03_p04.png](full_pages/gsorb_slam_fig03_p04.png) | Fig. 3: Gaussian ray와 transmittance |
| [imap_fig03_fig04_p04.png](full_pages/imap_fig03_fig04_p04.png) | Fig. 3–4: active sampling·keyframe selection |
| [on_the_fly_gs_fig02_fig03_p04.png](full_pages/on_the_fly_gs_fig02_fig03_p04.png) | Fig. 2–3: streaming 학습 phase 및 view management |

## 추출·검수 기록

Loss 도판은 원문 PDF에서 `pdftoppm -singlefile -scale-to 1750 -x … -y … -W … -H … -png`로 추출했다. 9개 PNG 모두 열어 축·범례·그림 번호·캡션이 잘리지 않았는지 확인했다. 전체 페이지는 기존 조사에서 렌더링한 PNG를 이름만 명확히 바꾸어 복사했다. 기존 PDF·생성 시안·TeX는 수정하지 않았다.
