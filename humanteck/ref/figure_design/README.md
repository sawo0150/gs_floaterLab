# 세부 기여 시각화 조사 자료

2026-09-19. 논문 소개 문단을 추가하기 위한 조사가 아니라 HumanTech overall figure 내부 표현을 설계하기 위한 자료다. 공개 원문 PDF를 내려받아 관련 도판 전체 페이지와 Method 설명을 함께 확인했다.

| 로컬 파일 | 공식 원문 | 확인한 도판 / PDF 페이지 |
| --- | --- | --- |
| [iMAP](imap_iccv2021.pdf) | [CVF](https://openaccess.thecvf.com/content/ICCV2021/papers/Sucar_iMAP_Implicit_Mapping_and_Positioning_in_Real-Time_ICCV_2021_paper.pdf) | Fig. 3–4 / p.4, §3.5–3.6 |
| [On-the-Fly GS](gaussian_on_the_fly_2503.13086v1.pdf) | [arXiv v1](https://arxiv.org/abs/2503.13086v1) | Fig. 2–3 / p.4, §IV-A–D |
| [GSORB-SLAM](gsorb_slam_2410.11356v2.pdf) | [arXiv v2](https://arxiv.org/abs/2410.11356v2) | Fig. 1–3 / pp.2–4, §III-B |
| [PGSR](pgsr_2406.06521v2.pdf) | [arXiv v2](https://arxiv.org/abs/2406.06521v2) | Fig. 4 / p.4, Fig. 9 / p.8 |
| [DS-NeRF](dsnerf_cvpr2022.pdf) | [CVF](https://openaccess.thecvf.com/content/CVPR2022/papers/Deng_Depth-Supervised_NeRF_Fewer_Views_and_Faster_Training_for_Free_CVPR_2022_paper.pdf) | Fig. 1 / p.1, Fig. 3 / p.4, §3 |
| [mip-NeRF 360](mipnerf360_cvpr2022.pdf) | [CVF](https://openaccess.thecvf.com/content/CVPR2022/papers/Barron_Mip-NeRF_360_Unbounded_Anti-Aliased_Neural_Radiance_Fields_CVPR_2022_paper.pdf) | Fig. 5–6 / p.6, §4 |
| [DN-Splatter](dn_splatter_wacv2025.pdf) | [CVF](https://openaccess.thecvf.com/content/WACV2025/papers/Turkulainen_DN-Splatter_Depth_and_Normal_Priors_for_Gaussian_Splatting_and_Meshing_WACV_2025_paper.pdf) | Fig. 1 / p.2, Fig. 2 / p.5, §4 |
| [2D Gaussian Splatting](2dgs_siggraph2024.pdf) | [저자 공개 원문](https://www.cvlibs.net/publications/Huang2024SIGGRAPH.pdf) | Fig. 3 / p.4 (표현·렌더링), Fig. 6 / p.7 (loss ablation), §5 |
| [Urban Radiance Fields](urban_radiance_fields_cvpr2022.pdf) | [CVF](https://openaccess.thecvf.com/content/CVPR2022/papers/Rematas_Urban_Radiance_Fields_CVPR_2022_paper.pdf) | §4.2 / p.4, expected-depth와 line-of-sight 수식 비교; 독립적인 loss 도식 사례로 분류하지 않음 |

기존 [CaRtGS v2](../../../paper/ref/convergence/cartgs_2410.00486v2.pdf)의 Fig. 3–4 / pp.3–4 및 adaptive optimization 설명도 다시 확인했다. 도판 번호는 실제 확인한 버전 기준이며 최신 버전과 같다고 가정하지 않는다.

분석과 우리 도판 적용안: [세부 시각화 조사](../../sections/02_method/plan/04_detail_visualization_literature_2026-09-19.md).

추가 loss 조사: [loss의 작용을 설명하는 그림](../../sections/02_method/plan/05_loss_visualization_study_2026-09-19.md). DS-NeRF Fig. 6 / p.8의 MSE–KL 비교도 추가 확인했다.

논문 그림을 우리 제출 도판에 복사하지 않는다. 시각적 설명 원리를 참고해 새로 구성한다. 생성 이미지의 장면은 실험 결과로 사용하지 않는다.
