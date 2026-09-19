# v08–v09: overview 기반 loss 표현 수정 및 검수

2026-09-19. Imagegen 스킬의 내장 도구를 사용했다. v07 편집 → v08, 오른쪽 경로 교정 → v09. 모든 이전 버전은 보존했다. 출력 크기 1816 × 866 px. TeX/Overleaf와 loss 구현은 수정하지 않았다.

## 이번에 적용한 설계 기준

- 참고 figure를 **overview로 한정**했다. DN-Splatter Fig. 1의 기본 supervision + 작은 기하 도식, PGSR Fig. 4의 rendered quantities / supervision 연결을 참고했다.
- mip-NeRF 360의 loss 설명도, DS-NeRF의 분포 도식, 각 논문의 ablation 이미지는 이번 생성의 시각 reference로 넣지 않았다.
- 독립적인 mean-depth counterexample/histogram은 사용하지 않는다. 전체 pipeline의 오른쪽 영역 안에서 geometry 제약이 어디에 작용하는지를 보여준다.
- 표면 앞 opacity 억제를 설명하는 Carve 중심 개념 표현이다. 미확정 후보 objective를 결정하거나 실제 성능을 주장하지 않는다.

## 반영된 내용

1. 입력 / 학습 영상 관리 / 지도 최적화의 세 영역과 K/I 구분 유지.
2. 3→4→5 pool, completed-update 기반 growth, count와 sampling probability의 정성적 역관계 유지.
3. 기존의 큰 observed/rendered RGB 비교 및 crop 쌍을 RGB·depth·normal strip으로 교체.
4. `Base supervision: RGB (K + I) · Depth / Normal (K)`로 기존 항을 작은 묶음에 정리.
5. 새 geometry 항은 camera ray / observed free space / depth evidence / surface uncertainty / 잘못된 앞쪽 Gaussian으로 표현. 분포 차트 삭제.
6. 붉은 Gaussian에 `Suppress premature opacity` 및 downward alpha 표시. 표면으로 위치를 이동시키는 화살표는 사용하지 않음.
7. Base supervision과 geometry가 독립적으로 하나의 Map objective에 합류하고 같은 map으로 Update.
8. v09에서 `Depth-derived normal` 표기와 depth→normal 화살표 추가. Map에서 기하 inset까지의 callout이 끝까지 연결됨.

## 미완성 / 수정 실패 항목

**아직 제출용 정확한 연결도가 아니라 디자인 검토본이다.** 생성 결과 전체를 확인했으며 다음 사항을 그대로 성공 처리하지 않는다.

- v09의 callout은 이제 기하 inset에 도달하지만 normal thumbnail 위를 가로지른다. 독립된 gutter로 옮겨야 한다.
- `Keyframe priors` 텍스트가 sampled-view 입력 화살표 옆에 붙었다. Depth evidence에서 base supervision으로 분기되는 별도의 경로는 제대로 생성되지 않았다. 현재 위치대로면 intermediate I2가 depth/normal prior도 제공하는 것처럼 읽힐 수 있으므로 최종 도판에서 반드시 교정.
- v07에서 남았던 initialization source의 단절, arrived-view 유입선 source 모호성, selection-history arrowhead가 count가 아닌 probability label 부근에 있는 문제는 유지됨.
- 같은 ID의 thumbnail이 모든 위치에서 동일하지 않다. 최종 도판은 동일 실제 이미지 asset을 복제해야 한다.
- 입력/풀의 두-view queue는 v08에서 선택된 I2 한 장으로 단순화됐다. `One view per update`와는 일치하지만, `Sample without replacement`의 K개 queue를 완전히 시각화하지는 못한다.
- RGB·depth·normal의 장면은 대응하도록 생성했으나 정확한 동일 camera/pixel 대응을 검증한 데이터가 아니다. 최종본에서는 실제 렌더링으로 교체.
- 강조한 red Gaussian 외의 free-space Gaussian이 벌점에서 제외된다는 의미는 아니다. 몇 개의 기하 요소를 보여주는 개념도다.
- Actual configuration에서 유효한 keyframe prior, masking, loss 활성화 및 최종 objective를 확인해야 한다. K라는 이유만으로 모든 ray의 depth/normal supervision이 유효한 것은 아니다.
- 인쇄 크기 가독성은 아직 검증하지 않았다. 원본 이미지 수준에서만 확인했다.

## 파일

- [v08](overall_pipeline_v08.png), [v08 prompt](overall_pipeline_v08_prompt.md)
- [v09](overall_pipeline_v09.png), [v09 prompt](overall_pipeline_v09_prompt.md)

생성 이미지는 원리·배치 논의를 위한 도식이며 실험 결과가 아니다. 이번 사용자의 검토 포인트는 **기본 loss를 묶고 새 기하 제약을 작은 공간 도식으로 보여주는 오른쪽 영역의 방향성**이다.
