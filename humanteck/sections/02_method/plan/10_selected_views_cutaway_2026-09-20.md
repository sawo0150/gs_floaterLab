# 선택한 실제 자산과 shared-map cutaway

## 추가 수정: 벽 법선 정렬 / 점 표시 강화

이 절이 최신 상태다. 아래 최초 S3 선택·43,706개 표시 기록은 이전 이력으로 남긴다.

- 사용자 후속 요청에 따라 trajectory A scatter alpha를 0.26→0.34, size를 0.65→0.85pt²로 높였다. 궤적·frustum·색상·source Gaussian은 그대로다.
- C07 좌표의 벽 상단 band에서 Gaussian 중심 6,000개를 seed123으로 표본 추출했다. RANSAC 600회, 4cm 지지 거리, SVD refinement로 주 벽 평면을 추정했다. 1,510개 지지점, RMS 약 2.23cm. 이는 표시 방향을 정하기 위한 추정이며 GT normal이 아니다.
- C07 기준 법선은 `[-0.40425447, 0.05089343, 0.91322953]`. 카메라의 좌우 각도와 공간 절단 상자를 이 벽 평면에 맞췄다. 직전 비스듬한 S3 대신, 벽 정면에서 위로 24° 올라간 새 S5를 채택했다. 광축이 법선과 완전히 평행한 것은 아니며 바닥·책상이 보이도록 elevation을 남겼다.
- 벽 정렬 좌표의 표시 범위는 `[-4.0,-1.80,-1.90]`~`[4.0,0.60,0.48]`m. 앞쪽·하단·좌우 범위를 조정해 30,587/177,099개 중심을 표시한다. 개별 Gaussian 품질·scale·opacity 기준 제거는 하지 않았다. 경계의 큰 타원체가 평면을 넘어 보이는 한계는 그대로다.
- 여섯 near-frontal 구도를 재렌더했고 현재 후보판도 갱신했다. 직전 PDF/PNG/SVG, cutaway, trajectory와 active provenance는 `archive/before_wall_alignment/`에 복사해 보존했다.
- 기존 extractor만 diff 수정했고 원본 지도·C10 이미지·기본 overview 구조는 변경하지 않았다.

## 사용자 결정과 적용

- 첫 번째 후보판: C07, UID786. Shared map의 기준 영역으로 사용한다.
- 두 번째 modality 후보판: C10, UID1091. Rendered RGB/depth/normal, frontend depth/normal prior, 선택된 K3 입력까지 같은 UID로 맞춘다.
- 궤적: A. 실제 pose·frustum 위치와 방향은 그대로, Gaussian 중심 점의 표시 농도만 높인다.
- Shared map은 카메라 내부 RGB 화면 대신, 외부에서 실내 구조가 보이는 cutaway로 표현한다.
- 승인한 3열 구조와 Times New Roman을 유지한다. Python 파일을 새로 복제하지 않고 기존 extractor/builder에 diff로 반영한다.

## 실제 구현

저장된 exp94 Aria1253 normalized_variance_s0 prefinal 지도를 사용한다. 추가 학습·optimizer update 없음. 원본 PLY SHA256은 `3c6b132bd64d3e0047b83c5c7673b0d320c9dfbf091ac66a66e88b43b2ac6766`이다.

1. K/I 예시는 시간순 UID1073(K1), 1079(I2), 1091(K3), 1104(I4), 1123(K5)로 정렬했다. 실제 keyframe 여부, mapping 포함, held-out 아님을 검증했다. Count·probability·pool 확장 단계는 여전히 설명용이다.
2. 궤적 A는 115개 저장 keyframe pose와 11개 실제 방향 frustum을 사용한다. 배경은 Gaussian 중심의 DC 색상 점 투영이며, scatter alpha 0.10→0.26, size 0.50→0.65로 조정했다. 원본 Gaussian opacity 변경이 아니다.
3. C07 camera를 기준으로 정방향 right/up/forward 좌표계를 만들고, 로컬 범위 `[-4.5,-2.1,-0.6]`부터 `[4.5,0.70,4.6]`m까지의 중심을 갖는 Gaussian을 임시 표시한다. 177,099개 중 43,706개다. 자세한 원점·기저·카메라는 provenance에 기록했다.
4. 이 동일 공간 절단을 6개 외부 camera에서 렌더링했다. S3의 비스듬한 외부 구도가 바닥·뒷벽·책상을 함께 보여주므로 현재 overview에 적용했다. S3는 제작 과정에서 고른 구도이며 사용자가 추가 승인한 선택은 아니다.
5. 선택본은 alpha PNG에서 nonzero인 모든 픽셀을 포함하고 22px 여백을 둔 bbox로 빈 캔버스만 줄인다. 내부 물체·잡음 픽셀을 따로 지우거나 채우지 않는다.

## 해석과 한계

- Cutaway는 사용자 요청에 따른 **표시용 공간 절단**이다. 학습된 지도에서 잘못된 Gaussian을 찾아 제거한 결과가 아니다. 원본 PLY는 쓰거나 덮어쓰지 않았고 해시로 동일성을 확인한다.
- 절단 기준은 Gaussian 중심이다. 타원체가 절단 평면을 조금 넘을 수 있어 정밀 mesh 절단면처럼 보이지는 않는다.
- C07은 영역 기준이고 외부 camera는 inspection용으로 새로 정한 pose다. UID786 RGB 시점에서 그대로 촬영한 화면이라고 주장하지 않는다.
- C10의 RGB/depth/normal은 절단을 적용하지 않은 동일 저장 지도에서 나온다. Geometry prior와 rendering normal은 출처가 다르며 smoothing하지 않는다.
- 이 run은 ray-space loss가 꺼져 있다. 전체 제안 방법의 성능이나 floater 제거 효과를 입증하는 그림이 아니며 caption에 제한을 남긴다.
- PDF 재렌더 검수와 폰트 embedding 확인 대상이다. 본문 TeX compile·실물 인쇄 검수는 별도다.

## 결과 위치

- [현재 overview](../figures/production/current/overview.png)
- [LaTeX PDF](../figures/production/current/overview.pdf)
- [외부 cutaway 시점 6개 비교](../figures/production/candidates/04_cutaway_cameras.png)
- [Cutaway provenance](../figures/production/assets/cutaway/provenance.json)
- 이전 선택 전 그림은 `production/archive/before_cutaway/`에 보존했다.
