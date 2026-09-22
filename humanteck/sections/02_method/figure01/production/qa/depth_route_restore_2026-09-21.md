# Verified depth 연결선 복원 및 penalize 용례 — 2026-09-21

- 사용자 피드백에 따라 추가한 depth 전용 하단 트랙과 Carve 박스 오른쪽 우회선을 제거했다. 원래 공통 prior 경로 및 짧은 내부 depth 연결선을 복원하고 `Verified keyframe depth` 라벨을 되살렸다.
- `Gaussian initialization`, `Camera pose`, `Penalize free-space opacity`, opacity 감소 기호와 구간선은 유지했다.
- `penalize`와 `opacity`의 직접 결합 용례를 확인했다. [StereoGS 공식 프로젝트](https://stringerywh00.github.io/StereoGS_project_page/)의 framework overview에 `penalizes Gaussian opacities`가 있다. 정확한 전체 문구가 정착된 명칭인지와 두 단어가 자연스럽게 함께 쓰이는지는 별개의 질문이다.
- Uncertainty는 방법론 초고의 외부 surface-depth posterior 및 안전 여유에 근거해 추가했다. Gaussian covariance/shape uncertainty를 뜻하지 않는다. 보라색 Gaussian과 band의 색이 겹쳐 설명이 모호하므로 overview에서 band/라벨을 빼고 본문에 남기는 방향을 권고한다. 이번 요청은 이유 설명이므로 해당 요소는 아직 변경하지 않았다.
- PDF 재생성 및 loss 영역 확대 확인. Poppler word bbox 중첩 0쌍, 페이지 밖 단어 0개, 원고 PDF 바이트 일치 확인.
- 직전 결과: `archive/before_depth_route_restore_2026-09-21/`.
