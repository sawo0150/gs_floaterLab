# 실제 pose 표현 · 시점 후보 · 작업 폴더 정리

2026-09-19. 사용자 요청: 무의미한 camera trajectory와 가짜 poses를 실제 데이터로 바꾸는 방안, overview 선행 그림 재검토, 우측 view 여러 후보 비교판, 파일 정리. View 최종 선택은 사용자에게 남긴다.

## Overview 원문 재검토

이번에는 ablation/개별 loss figure가 아니라 아래 **overview**만 디자인 근거로 다시 열어 확인했다.

| 원문 | 관찰한 구성 | 이번 적용 |
| --- | --- | --- |
| [VIGS-SLAM Fig. 2, PDF p.4](../figures/reference_figures/full_pages/vigs_slam_fig02_p04.png) | RGB/IMU 입력과 frontend, keyframe pose 출력, point cloud→initial GS, mapping을 분리한다. 카메라 모양은 pose 출력이나 pose graph에 속한다. | 입력 전에 장식 궤적을 두지 않고 RGB→frontend→pose/depth/normal로 의미를 정렬한다. |
| [CaRtGS Fig. 4, PDF p.4](../figures/reference_figures/full_pages/cartgs_fig04_p04.png) | Camera/frustum이 localization과 keyframe pool의 view를 나타낸다. 단독 장식이 아니라 실제 역할과 연결된다. | Frustum을 보여주려면 위치·방향·어떤 view인지에 의미를 부여한다. |
| [GSORB-SLAM Fig. 1, PDF p.2](../figures/reference_figures/full_pages/gsorb_slam_fig01_p02.png) | 오른쪽 Tracking 결과에서 실제 map 위 trajectory를 함께 보여준다. | 실제 Gaussian 중심을 옅게 배경으로 두고 같은 좌표계의 궤적과 frustum을 겹친다. |
| [DN-Splatter Fig. 1](../figures/reference_figures/loss_figures/dn_splatter_fig01_overview.png), [PGSR Fig. 4](../figures/reference_figures/loss_figures/pgsr_fig04_overview.png) | 입력/prior와 렌더된 modality를 구분하고 loss에서 비교한다. | RGB와 depth/normal을 서로 다른 예쁜 view에서 가져오지 않고 같은 후보 UID로 묶어 고른다. |

이들 그림의 실제 궤적 여부를 일반화한 것이 아니라, **도식 안에서 camera/pose가 맡는 역할**을 분석한 것이다. 제출 그림에 타 논문 이미지를 재사용하지 않는다.

## 왼쪽 구성 결정

- 위쪽의 임의 곡선 + camera icon 열과 frontend 옆 임의 pose 열을 제거한다.
- 위에는 실제 RGB filmstrip, 아래에는 frontend를 둔다.
- Frontend output으로 실제 estimated poses를 한 번만 크게 표시하고 depth/normal은 그 아래 병렬로 유지한다.
- `traj_kf_beforeBA.txt`의 115개 camera-to-world pose를 사용한다. Dense `traj_full_beforeBA.txt`는 evaluator의 post-EOS pose fill이 포함될 수 있어 frontend 궤적 근거로 사용하지 않는다.
- Frustum은 실제 intrinsics로 만든 네 image-plane corner를 각 pose의 R,t로 변환한 것이다. 11개만 균등 간격으로 표시해 겹침을 줄인다. 깊이 0.45m는 glyph 표시 크기이며 센서 range가 아니다.
- 지도 배경은 같은 PLY의 실제 Gaussian 중심과 DC color. Mesh/GT/occupancy 그림이 아니다. Camera와 map에 동일한 투영을 적용하고, 위치를 따로 맞추거나 정렬하지 않는다.
- A: pose 주성분 평면에 orthographic 투영. B: 같은 basis의 oblique 투영. 중력 기준 top view라는 주장은 하지 않는다. Plot viewport 밖 점은 표시되지 않지만 PLY를 삭제·prune하지 않는다.
- 저장 endpoint의 추정치를 보여주는 것이지, 각 시점에서 실제 online 화면을 기록한 time-resolved visualization은 아니다.

## 오른쪽 후보판

- 같은 run / 같은 prefinal PLY로 12개 시점을 새로 렌더링했다. Optimizer 실행 없음.
- C01–C12 UID: 201, 284, 389, 487, 589, 687, 786, 893, 998, 1091, 1193, 1272.
- C02=이전 시점. 시퀀스 전반의 시간 간격을 대략 균등하게 확보했고 PSNR 순위로 선별하지 않았다.
- 모두 실제 keyframe pose 사용, mapping 포함, held-out 제외를 확인했다.
- `01_view_candidates.png`: wide-FOV map view 12개.
- `02_modalities_all.png`: 같은 12개 후보의 input RGB / rendered RGB / depth / depth-derived normal.
- 각 후보 폴더에는 같은 UID의 frontend depth/normal도 준비했다. 사용자가 선택하면 대응 자산을 함께 바꿀 수 있다.
- Depth 공통 표시 범위 0.5–7.0m, normal unit camera-space xyz→RGB, 모든 frame modality 동일한 시계방향 90도 회전. 색/밝기 보정·normal smoothing 없음.
- 시각 확인 결과: C03은 모니터/선반, C06–C07은 부품 수납장/책상이 명확해 구조 설명용 구도 후보로 비교할 만하다. 하지만 거친 벽면·noisy normal은 여러 후보에서 보이므로 view 선택만으로 전체 기하 품질이 해결된다고 주장하지 않는다.
- `selected_candidate`는 null 유지. 사용자 선택 전 최종 확정하지 않는다. 우측 기존 view는 임시로 보존한다.

## 폴더 이동

- `current/`: 현재 PNG/PDF/SVG/TeX만.
- `candidates/`: 비교판, manifest, frames/.
- `assets/`: aria1253/ 및 trajectory/와 provenance.
- `scripts/`: 기존 두 Python 파일을 이동한 뒤 diff로 수정. 새 버전 Python 생성 없음.
- `qa/`: PDF 재렌더, 비교, crop, QA·validation.
- `archive/layout_v01/`: 옛 layout과 초기 후보판/코드/manifest.
- `archive/before_pose_revision/`: 이번 pose 수정 전 overview와 README.

파일은 삭제하지 않았다. 기존 시안/원본 수상자/실험 원본은 보존하며, 현재 링크와 코드 출력 경로를 새 위치로 수정한다.

## 추가 피드백 — 구조 유지, Times New Roman

사용자가 현재 구조는 좋다고 평가하고 Times New Roman을 선호했다. 현재 overview의 배치·자산·연결선을 그대로 유지하고 Times New Roman Bold/Regular로 변경했다. 후보 비교판은 화면 탐색용 Arial을 유지한다. PDF로 다시 출력해 글자 폭 변화에 따른 겹침을 검수한다. v01의 빈 슬롯 위주 배치로 돌아가지 않는다.
