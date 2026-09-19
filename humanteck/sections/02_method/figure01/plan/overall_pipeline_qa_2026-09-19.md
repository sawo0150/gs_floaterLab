# 생성 그림 검수 기록

날짜: 2026-09-19. 목표: rough concept 검토. 최종 투고용 도판 승인 아님.

## 변경 이력

### v01

- 회색 frontend/초기화, 주황 Growth, 파랑 Sampling, 보라 Geometry의 구분은 명확했다.
- frontend depth가 Growth를 경유하는 것으로 보였고 arrived RGB→geometry 연결이 추가됐다.
- Selection counts와 map update 경로 일부에 양방향 arrowhead가 생겼다.
- 생성기가 p=0.1/0.6/0.3을 임의로 추가했다. n=12/3/7과 대략적인 순위는 맞지만 Method의 exact probability 수치로 사용할 수 없다.
- 이상을 프롬프트 기반 부분 편집으로 수정 요청했다. 원본은 그대로 보존.

### v02

- RGB→geometry 추가 경로 제거, map→render/update와 update→map 분리, 선택 횟수 feedback 방향 수정, p 수치 제거 확인.
- depth 선이 orange 영역을 통과하여 별도 감독 경로라는 점이 시각적으로 모호했다.
- Sampling의 randomness 문구가 사라져, 경로 정리와 문구 복원을 추가 요청했다.

### v03 — 현재 검토본

- depth 선이 orange 영역 밖의 통로로 이동했다. orange 입력 선과 만나는 곳은 bridge 형태로, 연결 노드가 아님을 표시한다.
- Geometry loss가 Mapping update로 들어가며 Sampling 뒤의 후처리로 그려지지 않는다.
- 완료 update→Growth, 선택 횟수→Sampling의 두 feedback을 분리했다.
- 공유 Gaussian map에서 update가 렌더링 입력을 받고 같은 map에 parameter update를 돌려준다.
- 가짜 PSNR, 가속 배수, 실험 curve는 없다. 생성된 실내 장면과 Gaussian은 개념 표시이며 하단에 실험 결과가 아니라고 명시돼 있다.

## 최종 도판 전 남은 사항

1. Sampling 내부 문구가 요청한 `Counts + randomness` 대신 `Counts + randomility`처럼 잘못 생성됐다. **제출본에 그대로 사용하지 않는다.** 정식 그림 제작 시 실제 텍스트 객체로 교체한다.
2. n=12/3/7은 설명용 예시이며 실제 측정값이 아니다. Lower/Higher/Medium은 선택 확률의 상대적 순위다. 최종본에서는 숫자를 빼고 count 막대만 두는 안도 검토한다.
3. selected views의 썸네일 여러 장은 다음 K번의 update에 쓸 서로 다른 영상이라는 의미다. `K distinct views / one per update`를 본문·캡션에 명시하거나 최종 도판에서 짧게 표현한다.
4. 각 선택 영상의 camera pose 전달은 간략화돼 있다. 본문에서 pose가 확보된 관측을 사용함을 설명하고, renderer의 pose 입력을 도판에 별도로 보일지 결정한다.
5. ray의 점선은 기하 도해 내부의 광선 표시다. 범례의 scheduling 점선과 혼동될 가능성이 있어 최종 vector 도판에서는 실선 광선이나 다른 스타일로 바꾼다.
6. 기다리는 영상/편입 영상의 좌우 배치는 상태 구분용이다. 최종본에서는 waiting→gate→admitted의 실제 순서가 더 자연스럽게 보이도록 정리한다.
7. 180mm 전체폭 지면에서 작은 글자의 실제 크기·가독성은 아직 검증하지 않았다. 축소 배치 전 문구·여백을 더 줄일 수 있다.
8. Carve/Hit/조합 중 최종 objective는 아직 미확정이므로 공통 free-space/surface 직관만 표시했다. 이 그림만으로 두 loss 모두 활성화된 최종 구현이라고 주장하지 않는다.

## 판정

v03은 사용자가 **구성·강조점·방법 설명 순서**를 논의할 수 있는 초안이다. 최종 그림으로 확정되거나 실제 실험 결과를 표현하는 단계는 아니다. 현재 배치를 검토한 뒤 Method 본문을 압축하고, 제출용 도판에서는 문자·화살표를 편집 가능한 형태로 정리하는 것이 다음 단계다.
