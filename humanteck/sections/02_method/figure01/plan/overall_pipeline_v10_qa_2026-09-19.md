# v10 sampling 분포 수정 검수

2026-09-19. Imagegen 스킬의 내장 편집 도구로 v09의 sampling 영역 수정을 요청했다. v09는 보존했다. 원본 생성 이미지를 시각 확인했다.

## 반영된 내용

- K1 / I2 / K3 / I4 / K5 순서에 counts 12 / 9 / 6 / 3 / 0 표시. Gray bar 높이도 감소하며 마지막 count는 0.
- 동일 열에 probabilities 10% / 14% / 18% / 25% / 33% 표시. Blue bar는 증가하고 모두 양수. 표시값의 합계 100%.
- `Earlier admitted → Later admitted`, `Fewer selections → higher probability` 추가.
- 단순히 K는 낮은 확률, I는 높은 확률로 보이던 교대 패턴을 없앴다.
- 최고확률 K5가 아닌 I2를 선택한 예시를 유지한다. 확률적 선택이며 argmax가 아니다.
- 수치는 β=0.1, `p_i ∝ exp(-β n_i)`의 반올림 예시이며, 실제 측정값이나 실제 configuration이 아니다. 연령 자체가 아니라 count에 따라 확률을 정한다. 이번의 count-시간 단조 관계는 가능한 한 상황을 그린 것이다.

## 미완성 연결 / 생성 시 부수 변화

- Selection-history loop는 위로 옮겨졌지만 arrowhead가 count 막대에 직접 닿지 않고 pool→sampling junction 부근에 닿는다. 최종본에서 선택→count 갱신으로 고쳐야 한다.
- Probability strip에서 선택 I2 card로 향하던 명시적 화살표가 사라졌다. 복구 필요.
- 변경하지 말라고 요청한 keyframe-depth 경로도 변형됐다. 기존 bottom evidence line은 중간에서 위로 꺾이고 오른쪽 evidence 유입은 base input과 이어져 보인다. Intermediate selected view가 depth evidence를 제공하는 듯한 오독 위험이 있으므로 최종 사용 전 source를 frontend depth로 명확하게 분리해야 한다.
- v09의 map callout이 normal thumbnail을 통과하는 문제, initialization source, 동일 ID thumbnail 불일치 등 기존 QA 문제는 해결하지 않았다.

## 판단

사용자가 요청한 **count와 확률 분포의 관계**는 반영됐다. v10은 이 부분 검토용 시안이며 정확한 전체 데이터 흐름을 갖춘 제출본으로 간주하지 않는다. Loss 구현·TeX·Overleaf는 수정하지 않았다.

- [v10 이미지](overall_pipeline_v10.png)
- [생성 프롬프트와 확률 근거](overall_pipeline_v10_prompt.md)
