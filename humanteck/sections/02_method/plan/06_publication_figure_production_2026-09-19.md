# Overview를 LaTeX용 도판으로 제작하는 계획

2026-09-19. 사용자 요청에 따른 제작 설계 및 read-only 자산 조사다. SVG/PDF 제작, 새 학습·GPU 렌더링, TeX 삽입은 아직 실행하지 않았다. v12는 구도 참고일 뿐 데이터나 정확한 연결도의 원본으로 사용하지 않는다.

## 1. 제작 방식

**직접 제작한 SVG 벡터 도식 + provenance가 확인된 실제 raster 이미지 → hybrid vector PDF.**

- Python에서 SVG의 위치·도형·텍스트·연결선·반복 프레임을 생성한다. 생성 PNG 자동 tracing이나 PNG를 SVG 컨테이너에 넣는 방식이 아니다.
- SVG의 레이아웃/텍스트/카메라/분포/기하 개념도는 벡터다. 실제 RGB·depth·normal·지도 screenshot은 raster로 embed한다.
- Inkscape CLI로 PDF 및 검수 PNG를 출력한다. 사진까지 벡터가 되는 것은 아니다.
- 생성 이미지의 방이나 Gaussian을 잘라 실제 데이터인 것처럼 재사용하지 않는다.
- 디자인 reference는 합의한 DN-Splatter Fig. 1, PGSR Fig. 4의 **overview**로 제한한다.

환경 확인: Inkscape 1.4.4 및 pdftoppm 설치됨. 확인한 PATH에서 pdflatex / xelatex / latexmk / tectonic을 찾지 못했다. 따라서 현 환경에서 SVG/PDF 렌더 검수는 가능하지만 실제 TeX compile 검수는 별도 TeX 환경 또는 Overleaf가 필요하다. 이번에는 설치하지 않았다.

출력 방식 참고: [Inkscape 공식 CLI 문서](https://wiki.inkscape.org/wiki/Using_the_Command_Line). 설치 버전의 `--help`에서도 PDF·PNG export와 text-to-path 옵션을 확인했다. Text-to-path는 export 시 font 문제가 발생하면 쓰는 fallback이며, master SVG의 text는 유지한다.

## 2. 벡터 / 실데이터 구분

| 현재 요소 | 최종 제작 | 데이터·표현 조건 |
| --- | --- | --- |
| 상단 camera trajectory | 실제 estimated poses로 투영한 trajectory와 벡터 camera icons | GT/MPS trajectory로 대체하지 않음. 도식이면 schematic이라고 명시 |
| K/I 입력 filmstrip | 같은 sequence에서 실제 RGB 5장 | 실제 KF status와 held-out 여부 확인. IDs는 동일 asset을 모든 위치에서 반복 사용 |
| Growing pool 3→4→5 | 실제 thumbnail을 재사용한 벡터 배치 | admission 순서/시간을 frame 도착 순서와 혼동하지 않음. 개념 예시라면 그대로 명시 |
| Frontend keyframe depth | 실제 사용한 frontend depth 배열의 colormap | dataset sensor depth, MPS depth, rendered depth를 frontend estimate처럼 사용하지 않음 |
| Frontend keyframe normal | 실제 keyframe normal prior 배열의 RGB encoding | RGB 사진에 색만 입힌 대체 그림 금지. prior 알고리즘·좌표계를 기록 |
| Count / probability | 코드로 계산·그린 벡터 bars | 현재 예시 [12,9,6,3,0], β=.1의 softmax와 반올림 확률 유지 가능. illustrative임을 명시 |
| Shared Gaussian map | 채택 run의 Gaussian model을 실제 renderer/viewer로 촬영 | 실제 state/snapshot. PLY center point cloud를 Gaussian render라고 부르지 않음 |
| Rendered RGB / depth | 같은 Gaussian snapshot, camera pose, intrinsics로 렌더 | observation과 같은 viewpoint 및 crop. 임의 다른 render를 모아 배치하지 않음 |
| Depth-derived normal | 위 rendered depth에서 기존 loss와 같은 방식으로 계산 | frontend normal prior와 구분. coordinate frame, sign, invalid mask 일치 |
| Ray / free-space / surface / Gaussian 원리도 | 소수의 타원을 사용한 직접 제작 벡터 schematic | 실제 Gaussian의 위치·크기라고 주장하지 않음. 실제 지도에서 추출한 것처럼 연결하지 않음 |

**Gaussian을 모두 실제 사진으로 바꿀 필요는 없다.** Shared map은 실제 결과여야 하지만, loss의 원리를 보여주는 ray 단면은 수식과 맞는 추상 도식이 더 적합하다. 후자는 `Schematic ray constraint`로 구분하고, 실제 map 위치와 대응하지 않으면 특정 map 점에서 확대선을 빼지 않는다. 정확한 map callout을 원하면 해당 pixel ray의 contributor들을 실제 추출해야 하며 이는 추가 작업이다.

## 3. 실데이터 확보 상태

파일 존재를 확인한 후보이며, **논문 채택 결과나 최종 삽입 자산으로 승인한 것은 아니다.**

- 실제 RGB: `data/benchmarks/utmm/prepared/UTMM_Dataset/ego-drive/rgb/`, `data/benchmarks/rpng/prepared/rpngar/table_01/rgb/`.
- Aria 원본: `/home/intern/aria_data/0416_Data/0416_301-1253/0416_301-1253.vrs`. 원본은 있으나 이번에 채택 run에 맞는 RGB/depth/normal 묶음을 찾거나 추출하지 않았다.
- 실제 Gaussian 모델 예시: `results/experiments/exp87_normalized_variance_r4/rpng/table_01/normalized_variance_s0/3dgs_before_final.ply`. 파일명만으로 online 상태나 최종 방법의 유효성을 보장하지 않으므로 run config/로그 대조가 필요하다.
- 저장된 rendering 예시: `results/experiments/exp78/a_paper_reproduction/diagnostics/utmm_fast_straight_seed2_after_ba_before_color/renders/depth_inprocess_prefinal_official/000266.png`. 이는 **diagnostic/official reproduction** 경로다. 우리의 채택 방법 결과로 사용하면 안 된다.
- `/home/intern/VIGS-SLAM-custom/vigs/gs_backend.py`의 `_capture_polish_camera` 및 `save_polish_checkpoint`는 camera UID, pose, depth, normal, keyframe supervision, Gaussian tensors를 저장할 수 있다. 하지만 이 저장 경로는 final BA 이후 상태를 포함할 수 있다. 코드를 찾았다는 이유로 causal online snapshot이 확보되었다고 간주하지 않는다.
- 이번에 확인한 `exp78/paper_full_staged_v1` 범위에서는 `.pt/.pth` checkpoint 후보를 찾지 못했다. 다른 위치나 저장 포맷의 부재까지 단정하지 않는다.

**아직 부족한 것:** 같은 채택 run·시점에 대응하는 RGB/KF status/pose/depth prior/normal prior/Gaussian snapshot/rendered outputs의 완전한 한 묶음. 이것을 먼저 확정해야 그림의 내용이 정확해진다.

UTMM의 `depth/`나 Aria의 MPS 자료는 눈에 보이는 depth라고 해서 대체재로 쓰지 않는다. 실험의 입력 계약과 frontend 추정치의 의미를 지킨다.

## 4. 먼저 하나의 sequence와 snapshot을 고른다

우선순위는 **채택 방법을 설명할 수 있는 재현 가능한 run → 필요한 modality 확보 → 작은 그림에서 식별 가능한 장면**이다. 예쁜 장면/높은 PSNR만 보고 선택하지 않는다.

1. 논문에 대응하는 run과 해당 snapshot의 online/post-BA/post-polish 상태를 확인한다.
2. 같은 구간의 training-eligible keyframes와 intermediate views를 고른다. Held-out 영상은 training pool에 넣지 않는다.
3. 예시 K1/I2/K3/I4/K5는 실제 frame UID를 대체하는 도판용 alias로만 사용하고, alias→UID를 기록한다. 임의 등간격 5장을 골라 K/I badge를 붙이지 않는다.
4. 선택한 keyframe 한 장에 대해 RGB, frontend depth/normal prior, rendered RGB/depth, depth-derived normal을 확보한다.
5. Model render에는 같은 state·camera·intrinsics·crop을 적용한다. Depth prior/rendered depth의 scale과 color limits, normal의 좌표계와 invalid mask를 맞춘다.
6. Model의 3D overview는 실제 camera path 근처의 재현 가능한 view에서 출력한다. 보이지 않는 내부를 보여주려고 벽을 임의로 지우거나 floaters를 제거하지 않는다. Clipping/subsampling을 썼다면 기록한다.

현재 시안은 selected I2 하나만 보여주면서 오른쪽에 depth/normal loss까지 함께 그린다. 최종 도판에서는 **RGB는 K/I 모두, depth/normal/ray 항은 valid keyframe만**이라는 조건을 구조상 명확히 표시한다. 예를 들어 sampling output에 다음 updates의 I2와 K3 두 장을 놓고 `one view per update`를 유지하면, K3의 기하 supervision 예시를 오른쪽에서 보여줄 수 있다. 이것은 simultaneous minibatch가 아니다.

## 5. 연결 관계를 먼저 확정하고 배치한다

생성된 선을 그대로 tracing하지 않고 다음 관계를 port/edge 목록으로 정의한다.

- Arrived observations → frontend, 그리고 causal candidate buffer → View Growth.
- Frontend pose + depth → Gaussian initialization. Normal이 initialization에 사용된다고 임의로 추가하지 않는다.
- Completed updates → View Growth의 admission gate.
- Retained pool → count-based probabilities → sampled views for successive updates.
- Sample use/completed selection → selection counts 갱신. 구현에서 count를 올리는 정확한 시점 확인.
- Selected camera + shared map → render.
- Observed/rendered RGB → base objective (K/I).
- Valid keyframe depth/normal prior + corresponding rendered quantities → base objective.
- Verified keyframe depth + ray contributors from map → geometry objective (valid keyframe rays).
- Base와 geometry objective → 하나의 map objective → 같은 Gaussian map update.

Geometry thumbnail 또는 normal prior에서 verified-depth를 생성하는 것처럼 보이는 잘못된 선을 제거한다. Map-update feedback과 callout, 데이터 흐름은 서로 다른 선 스타일을 쓴다.

## 6. 논문 크기로 재배치

확인한 `humanteck/HumanTeck_Song_s_intern/humantech.cls`는 text width 180mm다. 원본 수상자 Overleaf는 **참고용**으로 보존하며, 새 저자용 TeX 목적지를 결정하기 전 이 파일을 덮어쓰지 않는다.

- 첫 layout target: 전체 폭 180mm, 높이 약 65–75mm. 이는 디자인 출발점이지 대회 규정이 아니다.
- 세 영역은 유지하되 left input은 작게, growth/sampling과 map optimization에 더 많은 폭을 준다.
- 최종 크기에서 일반 label 7.5–8.5pt, 제목 9–10pt 정도를 출발점으로 두고 실제 가독성 검수 후 조정한다. 1-column로 단순 축소하지 않는다.
- 기존 cartoon room이 차지하던 공간을 실제 map crop과 명료한 supervision 경로에 배분한다.
- 두 번 그려진 camera trajectory, film perforation 장식, 반복 문장 등 설명에 기여하지 않는 요소를 줄인다.
- 도식은 alpha ellipse와 선을 사용하되 과도한 SVG blur/filter를 피한다. PDF export에서 도형까지 raster화되는 일을 최소화한다.
- 사진의 DPI는 최종 표시 크기로 검수한다. 가령 25mm 폭의 thumbnail은 300dpi에서 약 295px가 필요하다. 업스케일로 실제 detail이 생기지는 않는다.

## 7. 제안 산출물 구조

아래는 **계획 경로**이며 아직 생성하지 않았다.

```text
humanteck/sections/02_method/figures/production/
  build_overview.py
  assets_manifest.json
  assets/
    rgb_<frame_uid>.png
    prior_depth_<kf_uid>.png
    prior_normal_<kf_uid>.png
    render_rgb_<kf_uid>.png
    render_depth_<kf_uid>.png
    render_normal_<kf_uid>.png
    gaussian_map_overview.png
  overview.svg
  overview.pdf
  overview.png
  overview_insert.tex
  QA.md
```

Manifest에는 scene/run/config hash 또는 commit, snapshot timestamp, frame UID/alias, train/held-out status, KF 여부, asset source, modality/prior-vs-render, intrinsics/pose reference, camera/world normal convention, crop, colormap/range, 실제/도식 구분을 기록한다. 같은 UID는 같은 asset을 참조한다.

SVG master에는 이미지를 embed해 파일 이동 시 경로가 깨지지 않게 하고, export 때 동일 source로 PDF/PNG를 재생성한다. 논문 배포 폴더에는 검수 완료 PDF를 복사하며 생성 시안 PNG와 혼동하지 않게 이름을 분리한다.

## 8. LaTeX 통합 및 검수

통합 시 사용할 구조의 예:

```latex
\begin{figure*}[t]
  \centering
  \includegraphics[width=\textwidth]{figure/overview.pdf}
  \caption{Overview of the proposed online Gaussian mapping framework.
  ...}
  \label{fig:overview}
\end{figure*}
```

SVG를 TeX 안에서 runtime 변환하지 않고 PDF를 직접 삽입한다. `figure/`는 휴먼테크 템플릿 예시이며 CVPR 쪽은 기존 `figs/` 규약에 맞춘다. 수상자 파일의 큰 음수 vspace/trim을 그대로 복사하지 않고 자체 PDF의 page boundary를 맞춘다.

필수 검수:

1. PDF→PNG를 렌더링해 clipping/선 겹침/글자 깨짐 확인.
2. 실제 180mm 폭에서 작은 label·count·probability 식별성 확인.
3. Frame alias의 동일성, 같은 camera의 modality 정합, masks/normal sign 확인.
4. Count와 probability 수치 자동 검증: 양수, 합 1, count에 대한 역관계.
5. Source–destination 관계를 위 edge 목록과 대조.
6. PDF의 font embedding 또는 outlined glyph, raster resolution, crop box를 확인.
7. 최종 TeX compile에서 두 단 폭과 float 위치, 전체 분량 확인. 현 환경에서 compiler 미확인 상태를 숨기지 않는다.
8. Caption에서 실제 데이터 이미지와 illustrative pool/count/ray schematic을 구분. 특정 도식에서 효과가 좋아 보인다는 것을 실제 floater 감소 결과로 취급하지 않는다.

## 9. 권장 실행 순서

**대표 run·자산 묶음 확정 → 정확한 edge 목록 → 벡터 skeleton → 실제 이미지 삽입 → 180mm 검수 → PDF export / TeX integration.**

가장 먼저 할 구현 작업은 예쁜 SVG 전체를 만드는 것이 아니라, 동일 sequence·run에서 쓸 수 있는 실제 자산 묶음을 확보하고 작은 contact sheet로 확인하는 것이다. 필요한 online snapshot이 없으면 임의로 final/postprocessed 상태를 대신 쓰지 않고 그 부족함을 먼저 보고한다. 새 학습은 이번 계획의 일부로 실행하지 않았다.
