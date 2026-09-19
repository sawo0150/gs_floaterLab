# 벡터 overview 실행 계획 / 수상작 글꼴 기준

2026-09-19. 사용자 승인: 06 계획에 따라 제작 시작, 글꼴은 기존 수상작을 따른다. 애매한 대표 run은 질문하면서 독립적인 layout 제작을 진행한다.

## 확정된 스타일

- 원본 `humanteck/HumanTeck_Song_s_intern/figure/main.pdf`의 embedded fonts를 pdffonts로 확인: `TimesNewRomanPSMT`, `TimesNewRomanPS-BoldMT`.
- 수상작 PDF 전체 페이지를 렌더링해 확인했다. 일반 label은 Times New Roman Regular, 제목/소절 강조는 Bold를 사용한다. 도판 원본이 PPT에서 만들어졌다는 메타데이터와 폰트 이름을 실제 확인했으며, 모양만 보고 추정한 것이 아니다.
- 본문 class는 mathptmx, 기존 1st_humantech.pdf는 Nimbus Roman 계열 본문과 Times New Roman 그림 글꼴을 포함한다. 본문과 도판을 모두 같은 sans-serif로 바꾸지 않는다.
- 로컬 fontconfig에서 Times New Roman Regular/Bold 모두 확인했다. 대체 글꼴 없이 제작 가능하다.
- Page width 180mm. 초안 높이 75mm부터 검수하고 지면 가독성에 맞춰 조정. 글자 크기는 원본 PPT의 거대한 pt 값을 복사하지 않고 **논문 삽입 후 물리 크기**에 맞춘다.

## 실행 단계

1. [완료] 수상작 font와 원문 도판 시각 확인.
2. [진행] 대표 run 질문, 실제 asset 존재·frame provenance 확인.
3. [완료: layout proof] 생성 PNG를 사용하지 않는 SVG source와 재생성 스크립트 작성. Times New Roman embedded PDF/PNG 출력 및 검수, 실제 Aria RGB 후보 비교판 저장. 데이터 슬롯은 아직 pending.
4. [대기] 채택 run RGB/depth/normal/map/render 묶음 승인·추출.
5. [대기] 이미지 삽입, 크기·동일 frame·경로·확률 검증.
6. [대기] 최종 PDF와 TeX 삽입본 생성·컴파일 검수.

## 진행 중 판단 기준

- 대표 run을 사용자에게 비동기 질문했다. 임의의 baseline/후처리 결과를 ours로 확정하지 않는다.
- Run 답변이 없으면 우선 layout proof를 제작한다. 실제 model/prior가 미확보인 슬롯은 **pending**으로 명확히 표시한다. 생성 이미지로 채우지 않는다.
- Aria RGB 후보가 발견되면 contact sheet와 출처를 별도 저장하되, 승인 전의 K/I 분류나 online causal 상태를 실제 방법의 결과로 주장하지 않는다.
- Missing asset이 있는 동안 파일명은 `overview_layout_v01`로 한다. 제출용 `overview.pdf`와 구분한다.
- 이 단계의 count/pool/ray는 명시적인 schematic이며 실험 성능을 나타내지 않는다.
- 새 학습/GPU 작업/기존 수상자 Overleaf 수정은 하지 않는다. 필요해지면 먼저 범위를 설명한다.

## 산출물 위치

### 대표 장면 후보 확인 (2026-09-19)

- 사용자는 Aria를 선호하며 1253을 후보로 제안했다. 우선 후보를 `aria1253`으로 기록하되 run은 미확정으로 유지한다.
- 실제 RGB 후보 비교판에서 책상·벽·의자와 시점 변화를 확인했다. 동일 장면으로 입력 프레임, depth/normal, 지도 결과를 연결하기에 적합한 후보다. 이는 시각적 적합성 판단이며 기하 정확성 검증은 아니다.
- `exp94_normalized_metric_v2_fixed_eval/aria/aria1253/normalized_variance_s0`에 실제 PLY, intrinsics, trajectory, mapping command/runtime, 평가 기록이 존재한다. 실험 카드는 held-out 25.775702 dB와 zero-tail을 보고한다. 다만 frozen-tracker, mapping-only fixed-work (`--time-scale unbounded`) 결과이므로 strict real-time 완성 시스템의 증거로 제시하지 않는다.
- 해당 command의 compute-paced admission 및 normalized-variance selector는 현재 Method 3.1–3.2와 관련 있어 점검 우선 후보로 삼을 수 있다. 전체 세 기여와의 일치, geometry loss 활성 여부, depth/normal의 동일 시점 출처는 아직 확인되지 않았다. 따라서 최종 ours 자산으로 채택한 것은 아니다.
- 선택 순서: **현재 Method와의 일치 → 동일 run/시점의 자산 확보 → 읽기 좋은 구도**. 최고 PSNR만으로 run을 선택하지 않는다. 입력 RGB와 렌더 결과를 다른 run에서 섞지 않는다.
- 원본 RGB는 옆으로 누운 방향이다. 최종 표시 방향을 정할 때 RGB/depth/normal을 일관되게 배치하고, normal 색상 좌표계와 표시용 회전을 구분해 기록한다. 아직 회전·크롭·밝기 수정은 하지 않았다.
- 이 확인은 기록/파일의 read-only 검토이며 새로운 학습·렌더 실험을 실행하지 않았다.

`humanteck/sections/02_method/figures/production/`

- `build_overview.py`: 직접 SVG 생성 및 Inkscape export.
- `assets_manifest.json`: 승인 상태와 자산/출처/기하 출력 슬롯.
- `overview_layout_v01.svg`, `overview_layout_v01.png`: 글꼴·배치 검토.
- `overview_layout_v01.pdf`: LaTeX에 삽입 가능한 포맷 검증용 layout proof, 최종 결과 아님.
- `README.md`, `QA.md`: 실행법·확인 항목·대기 중 선택.

입력은 실제 자료, 수식 설명은 명시적인 벡터 도식으로 구분한다. 미확정 modality와 잘못된 연결을 숨기는 완성 이미지는 만들지 않는다.
