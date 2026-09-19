# v06–v07 검수: 세부 기여 표현

2026-09-19. 내장 imagegen 출력 원본을 직접 시각 검토했다. 이미지 생성은 도판의 개념과 디자인을 탐색하는 용도이며, **제출 가능한 정확한 연결도 완성은 아직 아니다.** 원본 버전은 모두 보존한다.

## 확인된 개선

- 입력, pool, sampling label에서 K/I badge가 남아 두 종류의 학습 관측을 표시한다.
- 3→4→5장의 세 스냅샷과 주황 추가 표시가 단일 grid보다 성장과 retention을 분명하게 설명한다.
- count와 probability가 두 줄로 구분되고 같은 view 열에 정렬된다. 높은 count에 낮은 probability를 주는 정성적 관계가 보인다.
- I2와 K5를 선택해 가장 큰 확률의 영상만 강제 선택하는 그림을 피한다. 비복원 선택 및 한 update에 한 view라는 문구가 있다.
- RGB와 geometry가 독립적으로 Map loss로 합류한다. v05의 RGB loss → geometry 오연결은 해소됐다.
- geometry의 ray, surface evidence, 앞쪽 unwanted opacity, termination profile을 함께 보여준다.
- v07의 completed-update 점선은 v06처럼 지도 뒤에서 끊어지지 않고 상단 외곽을 따라 Growth로 돌아간다.

## 아직 불완전하거나 수정이 실패한 점

1. **영상 identity:** 같은 K/I ID에 배정된 그림이 스냅샷·입력·선택 출력에서 완전히 같지 않다. 특히 I4의 초기/후기 내용이 다르다. 최종 도판은 동일 이미지 asset을 복제해야 한다. 현재는 badge와 집합 membership의 개념만 신뢰할 수 있다.
2. **RGB viewpoint:** observed/rendered 이미지가 여전히 서로 다른 시점처럼 보인다. 같은 선택 view의 관측과 렌더를 넣어야 한다. crop도 실제 해당 위치에서 잘라 넣어야 한다.
3. **초기화와 arrived-view 경로:** v07의 gray initialization 선은 source 쪽이 끊겼고 Growth의 짧은 유입선은 camera 부근에서 끝난다. frontend pose/depth → map initialization과 all arrived views → admission을 분리해 다시 연결해야 한다.
4. **Selection history 방향:** 현재 파랑 feedback은 probability label 부근 및 queue를 잇는다. 선택 동작 → count 갱신의 단일 방향으로 고쳐야 한다.
5. **v07 Ray detail 회귀:** 지도에서 geometry inset으로 연결하라는 수정이 rendered RGB 쪽 `Ray detail` 표기로 잘못 반영됐다. 이 표기를 삭제하고 map → Rendered RGB에는 `Render`를 복구한다. map ↔ ray inset은 별도의 callout으로 표현한다.
6. **확률 막대:** 정성적 역관계만 표현한다. 정확한 softmax 값이나 실제 선택 로그가 아니며 caption에 schematic임을 유지한다. 막대 높이를 논문 결과로 해석하면 안 된다.
7. **Ray profile:** 현재 두 peak는 문제 상태의 설명이다. depth evidence와 termination weight의 직접 KL 일치를 뜻하지 않는다. 지도 update 후 모든 앞쪽 peak가 제거된다는 성능 보장도 아니다.
8. **Sampling queue:** 두 영상은 다음 두 update의 설명용 예시다. 일반 K를 2로 고정하거나 동시 batch로 해석하지 않는다.
9. **분량/가독성:** 원본에서는 label을 읽을 수 있지만 실제 초록의 삽입 폭·높이에서 검증하지 않았다. 지면이 부족하면 camera trajectory 중복을 먼저 줄이고 count/probability 및 loss의 비교 대상은 유지한다.

## 판단

이번 결과의 주된 산출물은 [근거 기반 세부 설계](../plan/04_detail_visualization_literature_2026-09-19.md)와 그 디자인 시안이다. v07은 모든 요청이 정확히 반영된 완성본이라고 보고하지 않는다. 현 구도가 합의되면 동일 실제 thumbnail과 편집 가능한 선·문자로 정확한 도판을 만드는 것이 후속 단계다. Overleaf/Method TeX는 수정하지 않았다.
