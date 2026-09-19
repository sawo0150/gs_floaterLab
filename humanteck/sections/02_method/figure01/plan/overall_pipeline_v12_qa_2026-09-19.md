# v11–v12: keyframe depth / normal 병렬 표시

2026-09-19. Imagegen 스킬의 내장 편집 도구 사용. v10 → v11에서 왼쪽 thumbnail 추가, v11 → v12에서 국소 connector 정리 시도. 이전 이미지와 프롬프트 모두 보존했다. TeX·코드·Overleaf 변경 없음.

## 확인된 반영

- Online observations의 frontend 아래에 `Keyframe depth`와 `Keyframe normal`을 동일 크기의 두 thumbnail로 병렬 배치했다.
- 두 thumbnail에 동일한 방·가구 배치를 표현했다. 실제 추정 데이터나 정확한 pixel 대응을 검증한 결과는 아니다.
- Depth는 rainbow depth colormap, normal은 cyan/lavender/pink 계열 surface-orientation 표현으로 구분했다.
- Poses 출력, growing pool과 sampling 예시 counts=[12,9,6,3,0], probabilities=[10%,14%,18%,25%,33%]는 유지됐다.
- 오른쪽 loss의 주요 배치와 문구가 유지됐다.
- v11에서 normal 옆에 붙은 출력선은 v12에서 제거되고 thumbnail 아래 경로로 옮겨졌다.

## 남은 한계

- 두 thumbnail 위의 fork는 존재하지만 frontend box와의 명확한 접합은 아직 완전하지 않다. 기존 frontend 아래 선과 하단 outgoing 경로도 뒤섞여 있어 최종 source–destination 연결도 수정이 필요하다. 이번 교정을 완전 성공으로 처리하지 않는다.
- 전체 figure의 initialization source, keyframe priors / verified-depth 유입 경로, sampling probability→selected view, selection-history→counts, ray-detail callout 교차 등 기존 v09/v10 QA 문제는 해결하지 않았다.
- Normal prior가 base normal supervision으로 전달되는 독립 경로는 이번에 추가하지 않았다. 사용자 요청은 Online observations에 두 prior를 표시하는 것이다.
- 그림은 생성된 디자인 검토본이며 제출용 최종 연결도·실험 결과가 아니다.

## 산출물

- [v11](overall_pipeline_v11.png), [v11 prompt](overall_pipeline_v11_prompt.md)
- [v12](overall_pipeline_v12.png), [v12 prompt](overall_pipeline_v12_prompt.md)
