# v04–v05 디자인 검수

날짜: 2026-09-19. 이미지 생성 결과를 직접 시각 검토했다. **디자인 검토용이며 과학적으로 검수 완료된 제출용 도판이 아니다.** 기존 v01–v03 및 Overleaf는 보존했다.

## 디자인 측면의 변화

- Online observations / Training-view management / Gaussian map optimization이라는 기능 구조를 사용한다.
- Growth와 Sampling을 같은 영상 배열에 표현하고, geometry를 최적화 영역에 넣었다.
- 영상 pool과 큰 Gaussian room이 화면을 채우며, contribution별 설명 박스의 나열을 줄였다.
- v05에서 v04 외곽의 검은 노이즈가 제거됐다. 선택 영상은 Observed RGB로 연결되고 지도에서 렌더 영상으로 내려오는 경로가 구분됐다.
- 장면·지도는 모두 생성된 설명용이다. 데이터셋, 실제 결과, 성능 향상의 증거가 아니다.

## 아직 고쳐야 할 정확성 — 제출/본문 삽입 전 필수

1. **Appearance loss 연결:** v05의 loss junction 화살표가 영상 쪽으로 향하고, 아래 geometry inset으로 향하는 선이 생겼다. 두 영상 → appearance loss → Update가 맞다. Appearance loss → Geometry supervision 연결은 삭제해야 한다. 현재 렌더 영상에서 Update로 바로 가는 선도 loss 출력을 명시하는 형태로 고친다.
2. **영문 오타:** 오른쪽 영상의 `Cendered RGB`를 `Rendered RGB`로 고친다.
3. **완료 update feedback:** 주황 점선이 지도 뒤에 가려 끊어진 것처럼 보인다. Update → Growth의 단일 연속 경로로 위쪽 통로에 배치한다.
4. **초기화 경로 출발:** 회색 위쪽 선이 filmstrip 근처에서 출발한다. frontend pose/depth 출력에 연결한다. keyframe depth에서 초기화로 이어지는 의미도 분명히 한다.
5. **Selection history:** 파랑 선이 선택된 pool 영상 쪽으로 향한다. 선택 이력 → 확률 갱신과 pool → selected view 경로를 구분한다. 확률 막대에 짧은 label도 필요하다.
6. **현재 지도와 ray inset:** inset의 Gaussian들이 공유 지도의 ray 단면임을 작은 callout으로 명시한다. 별도의 geometry 후처리로 오해하게 하지 않는다.
7. **색 의미:** keyframe 외곽과 admission에 주황이 함께 쓰였다. 최종본에서 keyframe 외곽은 회색으로 바꾸면 역할 구분이 더 분명해진다.
8. **인쇄 가독성:** 실제 2쪽 지면에서 축소한 결과는 아직 검증하지 않았다. 지금은 원본에서 구성과 문자 상태를 확인한 수준이다.

## 다음 단계

사용자와 먼저 전체 디자인·정보 위계를 확인한다. 그 후 편집 가능한 도판에서 선과 문자를 정확히 마무리하고, 허용된 실제 데이터 예시가 있으면 설명용 생성 영상과 교체한다. 현 시안에서 보이는 잘못된 화살표를 근거로 Method를 변경하지 않는다. 같은 구도로 이미지 생성만 반복하며 모든 연결이 자동으로 정확해질 것이라고 가정하지 않는다.
