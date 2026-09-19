# 여기서 후보를 고르기

현재 사용자 선택: **지도 영역 C07(UID786), 렌더 modality C10(UID1091), trajectory A**. 현재 overview에는 이 조합을 적용했다. 지도는 C07 주변의 외부 cutaway로 변경했고, 아래 C10의 RGB·depth·normal은 전체 지도 렌더다.

1. **[01 지도 시점 12개](01_view_candidates.png)** — C01–C12 중 구도를 선택한다.
2. **[02 같은 시점의 RGB·depth·normal](02_modalities_all.png)** — 구도가 마음에 들더라도 실제 modality 상태를 함께 확인한다.
3. **[03 실제 trajectory A/B](03_trajectory_options.png)** — A는 pose 주성분 평면, B는 oblique projection. A를 선택했고 지도 배경을 조금 진하게 했다.
4. **[04 Cutaway 외부 시점](04_cutaway_cameras.png)** — 벽 평면에 맞춘 동일한 공간 절단을 yaw -6/0/+6°, elevation 15/24°로 비교했다. 현재 정면·24°의 S5 적용. 원본 지도는 수정하지 않았다.

C02는 이전 UID284다. Shared map과 렌더 예시는 서로 다른 camera지만 같은 저장 Gaussian 지도를 사용한다.

| 번호 | 실제 frame UID |
| --- | ---: |
| C01 | 201 |
| C02 | 284 |
| C03 | 389 |
| C04 | 487 |
| C05 | 589 |
| C06 | 687 |
| C07 | 786 |
| C08 | 893 |
| C09 | 998 |
| C10 | 1091 |
| C11 | 1193 |
| C12 | 1272 |

선택 판단은 구도와 설명력이다. 이 후보들은 mapping에 사용된 training keyframe이며 held-out 성능 비교가 아니다. 동일 지도, 공통 depth 표시 범위, 무보정 RGB로 비교했다. Normal은 모두 실제 rendered depth의 미분으로 계산했으며 시점에 따라 noisy한 정도가 달라질 뿐 전체적으로 거친 표현이 남아 있다.

`frames/Cxx_uidxxxx/`에는 input, rendered RGB/depth/normal, frontend prior depth/normal, wide_map PNG가 들어 있다. 후보별 출처·pose·hash와 C07/C10/A 선택은 [manifest.json](manifest.json)에 있다. Cutaway의 벽 평면 추정·절단 범위·외부 camera·S5 선택은 [별도 provenance](../assets/cutaway/provenance.json)에 있다. 이전 S1–S6 구도는 archive/before_wall_alignment/에 보존했다.
