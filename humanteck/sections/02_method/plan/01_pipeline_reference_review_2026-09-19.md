# Overall pipeline 도판 비교 및 수상자 팁 적용

날짜: 2026-09-19. 아래는 성능 우열 조사가 아니라 **Method를 압축해 전달하는 도판 구성 조사**다. 로컬 PDF의 해당 페이지 전체를 렌더링하고 캡션·주변 설명과 함께 확인했다.

## 1. 비교한 도판

| 자료와 확인 위치 | 실제 그림 구성 | 우리 그림에 적용할 점 | 그대로 옮기지 않을 점 |
| --- | --- | --- | --- |
| VIGS-SLAM, Fig. 2, PDF p.4 | RGB·IMU 입력, frontend tracking, loop closure, GS mapping을 묶음별로 배치. pose/depth→point cloud→initial GS와 렌더링 loss 경로 표시. 데이터·gradient·control 등의 화살표 범례 사용. | 기반 frontend와 Gaussian 초기화의 출처를 명확히 하고, 상태·데이터와 제어 피드백을 구분한다. | ConvGRU, IMU 초기화, pose graph BA 전체를 우리 기여처럼 크게 그리지 않는다. 2쪽 초고에서는 회색 기반 모듈로 축약한다. |
| CaRtGS, Fig. 4, PDF p.4 | 왼쪽 localization, 가운데 geometry mapping, 오른쪽 photorealistic rendering. keyframe pool과 Gaussian map을 별도 객체로 그리고 adaptive optimization, forward/backward, opacity regularization을 학습부에 배치. | **학습 영상 pool과 Gaussian map을 분리**하고 새 방법이 학습부의 어디에 작용하는지 보여준다. | ORB frontend, sparse point-cloud 초기화, loss 기반 배분을 우리 시스템의 구성으로 복제하지 않는다. |
| MonoGS, Fig. 2, PDF p.4 | Tracking·Keyframing·Mapping을 점선 경계로 구분. 공통 3D Gaussian Map에 각 동작이 연결됨. 섹션 번호와 각 모듈이 대응. | 지도를 마지막 결과 이미지뿐 아니라 **반복적으로 갱신되는 공유 상태**로 표현한다. 그림 번호와 본문 설명을 대응한다. | MonoGS와 달리 우리 tracking 전체가 Gaussian map 기반인 것처럼 피드백을 그리지 않는다. |
| SplaTAM, Fig. 2, PDF p.3 | 현재 지도와 RGB-D 입력, tracking, Gaussian densification, map update를 시계방향 루프로 구성. 렌더링·silhouette·mask 이미지를 통해 각 단계의 변화를 보여줌. | 작은 입력/출력 예시와 반복 루프가 추상적인 방법을 직관적으로 설명한다. | 우리 시스템에 depth 센서가 있다고 표현하지 않는다. View Growth를 Gaussian densification으로 혼동하지 않는다. 세 기여를 같은 직렬 단계로 옮기지 않는다. |
| Photo-SLAM, Fig. 2(b), PDF p.2 | Hyper Primitives Map을 가운데 두고 localization, geometry mapping, photorealistic mapping, loop closure를 원형으로 배치. Fig. 2(a)는 별도의 taxonomy. | 상세 계산 흐름 대신 기능 간 관계를 간결하게 표현할 수 있다는 사례. | 이 원형 요약만으로는 우리 admission·sampling·update feedback 차이가 드러나지 않으므로 주 도식으로 채택하지 않는다. |
| 수상자 1차 초록, Fig. 1–3, PDF p.2 | Fig. 1 전체폭 pipeline에서 로봇/서버/전송 데이터/세 선택 단계/병합 결과를 표시. Fig. 2–3은 실제 지도와 교환량 비교. 본문은 Fig. 1(a)–(f)를 따라 설명. | **그림이 설명 순서를 제공하고, 실제 이득은 별도 결과 그림이 입증한다.** 우리도 기반→(a)→(b)→(c)의 읽는 순서를 본문에 대응한다. | 수상자의 세 선택 단계는 cascade지만 우리 geometry loss는 sampling 뒤의 후처리가 아니다. 원본 도판이나 수치를 재사용하지 않는다. |

## 2. 출처

- [VIGS-SLAM 로컬 PDF](../../../../paper/ref/vigs_slam/vigs_slam_zhu_et_al_arxiv_2512.02293v2.pdf), [arXiv v2](https://arxiv.org/abs/2512.02293v2)
- [CaRtGS 로컬 PDF](../../../../paper/ref/convergence/cartgs_2410.00486v2.pdf), [arXiv v2](https://arxiv.org/abs/2410.00486v2)
- [MonoGS 로컬 PDF](../../../../paper/ref/view_selection/monogs_cvpr2024.pdf), [CVPR 논문 페이지](https://openaccess.thecvf.com/content/CVPR2024/html/Matsuki_Gaussian_Splatting_SLAM_CVPR_2024_paper.html)
- [SplaTAM 로컬 PDF](../../../../paper/ref/view_selection/splatam_cvpr2024.pdf), [CVPR PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Keetha_SplaTAM_Splat_Track__Map_3D_Gaussians_for_Dense_RGB-D_CVPR_2024_paper.pdf)
- [Photo-SLAM 로컬 PDF](../../../../paper/ref/convergence/photo_slam_cvpr2024.pdf), [CVPR PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Huang_Photo-SLAM_Real-time_Simultaneous_Localization_and_Photorealistic_Mapping_for_Monocular_Stereo_CVPR_2024_paper.pdf)
- [수상자 1차 초록](../../../ref/1st_humantech.pdf), [수상자 팁 원문](../../../ref/humanteck_tips)

## 3. 수상자 팁을 실제 설계 결정으로 옮기기

| 팁 | 이번에 반영하는 결정 |
| --- | --- |
| 비전문 독자도 주제를 이해하게 설명 | 제목 아래 긴 전문 용어 대신 각 기여에 짧은 질문을 붙인다: When to include views / Which views to revisit / Where opacity belongs. 정식 명칭은 본문·캡션에서 정의한다. |
| 파이프라인을 따라 Method를 읽게 구성 | (a) Growth, (b) Sampling, (c) Geometry를 본문의 세 방법과 대응한다. 그림의 읽기 순서와 실제 데이터 의존성은 구분한다. |
| 축약이 중요 | frontend 내부 네트워크, Jacobian, entropy 유도, ray 확률식은 그림에서 생략. 핵심 상태와 두 피드백만 남긴다. |
| 결과 설명은 짧게, 정성 결과는 그림으로 | 이번 그림에는 실제 결과를 가장한 생성 지도, 성능 수치, 가짜 convergence curve를 넣지 않는다. 추후 실제 GT/baseline/ours 비교와 예산 표시를 별도 결과 그림에 배치한다. |
| 실용성을 수치로 강조 | 우리에게는 통신량이 아니라 제한된 online update에서 얻는 품질이 대응한다. wall-clock 가속·온보드 동작·기하 개선은 각각 검증된 경우에만 주장한다. |
| 절 제목으로 연구 주제 강조 | 후보: Efficient and Reliable Online Gaussian Mapping. 논문 제목이나 최종 절 제목의 확정은 아니며, 현재는 작업용 이름이다. |

## 4. 결론

이번 시안은 **CaRtGS의 frontend/backend 분리 + MonoGS의 공유 지도 상태 + 수상자 사례의 본문-그림 대응**을 참고하되, 우리 Method의 실제 인과관계로 새로 구성한다. 완성 artwork를 복제하지 않는다.

그림에서 강조할 새로운 관계는 단순히 세 블록이 있다는 것이 아니라, **완료된 update가 관측 편입을 제어하고, 누적 선택 횟수가 재학습 배분을 제어하며, depth evidence는 지도 최적화의 기하 목적에 들어간다**는 점이다.
