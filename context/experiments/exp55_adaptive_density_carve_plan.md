# exp55 — 내용-적응 per-frame gaussian 예산 + carve loss 이식: "적게 시작해서 필요한 만큼만 키우기"

- 상태: **계획 단계 (2026-07-22). 미착수.** (사용자 가설 구체화 요청 — 실행 전 3단계로 분해)
- 배경: exp53+54로 실시간(0.94배)은 달성했지만, exp54는 `pcd_downsample`을 **장면
  전체에 균일하게** 적용하는 방식이었다. 사용자 제안: keyframe마다 gaussian 개수를
  **그 프레임 내용에 맞게** 다르게 배정하면(디테일 많은 프레임엔 많이, 단조로운
  프레임엔 적게) 같은 총 gaussian 예산으로 더 높은 품질을, 혹은 같은 품질을 더 적은
  예산으로 달성할 수 있다는 가설. 여기에 "init을 아주 작게 주고 densify로 채우는 게
  처음부터 dense하게 시작하는 것보다 누적 연산량이 적다"는 두 번째 가설을 결합하고,
  densify가 활발해지며 생기는 floater 위험은 우리가 이미 검증한 **carve loss**로
  통제하자는 3단계 구성.

## 사용자 가설 원문 요약 (3개 축)

1. **Per-frame max gaussian cap + 작은 init + densify로 채움**: 원래 gaussian 개수가
   적은 데서 많아지는 쪽이(처음부터 dense한 것보다) 시간을 더 적게 먹는다는 원리 활용.
2. **내용-적응 per-frame 예산**: GT 이미지의 Sobel/std 값이 큰(엣지·디테일 많은)
   프레임은 gaussian이 많이 필요하고, 작은(단조로운) 프레임은 적게 필요할 것 —
   "PSNR 고정 시 GT 이미지의 Sobel/std 값과 필요 gaussian 개수의 관계"를 실제로
   구해서 그 관계를 per-frame 예산 산정에 사용.
3. **Carve loss로 floater 통제**: densify가 활발해지면 일부 gaussian은 커지고 일부는
   작아지는 등 geometry가 불안정해질 수 있음 — 이미 배치 트랙에서 검증된 carve loss
   (exp38~44d2)로 이를 억제.

## exp54와의 관계 — 정직한 긴장 포인트부터 짚기

exp54에서 이미 **비슷해 보이는** 실험을 했고 결과가 엇갈렸다 — 이번 계획이 그것과
어떻게 다른지 먼저 명확히 해야 한다:

- **축2**(`pcd_downsample_init` 32→64, init만 성기게): 최종 gaussian 수가 densify
  보정으로 오히려 **더 커짐**(202,089 vs 축1의 122,957), 시간도 +1.2% — 역효과.
- **축6+2 결합**(축2 + `densify_grad_threshold` 3배 상향으로 보정 증식을 억제): 최종
  gaussian 수는 성공적으로 억제(116,143, 축1보다도 적음)했지만 **시간은 그대로**(60.76s
  vs 60.65s) — 이 지점(tracking 52.31s ≈ mapping 49.79s로 균형)에선 **gaussian
  개수 자체가 더 이상 지배 변수가 아님**이 확인됨.

**이번 제안이 그것과 다른 점**: 축2/6+2는 "전역적으로 얼마나 성기게 시작하고 얼마나
억제하는가"였다 — 결과가 시사하는 바는 "densify가 알아서 채우게 두는 방식으로는
총량을 못 줄인다"였다. 이번 제안은 **(a) 명시적 per-frame 상한**(densify가 무한정
채우지 못하게 캡을 걸고) **(b) 그 상한을 내용별로 차등 배정**(균일이 아니라 엣지
프레임엔 높게, 단조 프레임엔 낮게) — 즉 "총량을 줄이는 것"이 아니라 **"같은 총량을
더 효율적으로 배분하는 것"**이 목표라 축2/6+2가 반박한 가설과 다른 축이다. 다만
"적게 시작해서 키우는 쪽이 시간을 아낀다"는 전제 자체는 축2/6+2 결과로 볼 때
**이 지점(이미 tracking-bound)에서는 의심스럽다** — Phase 1(아래)에서 이 전제부터
별도로 검증 필요.

## exp44 PPM/Instant-GI 선례 — 방법론적으로 이미 절반은 검증됨

exp44(배치 트랙)에서 이미 거의 같은 질문을 다뤘다: Instant-GI(2D Gaussian 이미지
표현, 내용-적응 점 배치 사상)를 3D에 이식하려다, **44e2에서 "사전학습 ConvNeXt
PPM(신경망)이 수제 Sobel 확률맵과 사실상 동급"**임을 확인 — 즉 **"내용-적응
샘플링"의 가치는 신경망이 아니라 Sobel/std 같은 단순 통계로도 거의 다 얻어짐**이
이미 검증됐다. 이번 exp55의 axis2도 신경망(Instant-GI) 대신 **Sobel/std 직접
계산**으로 관계를 구하는 쪽이 맞다 — exp44e2의 교훈과 일치하고 구현도 훨씬 가볍다.
exp54 축7(PPM)에서 이미 이식한 `create_pcd_from_image_and_depth()`의 Sobel gradient
계산을 그대로 재사용 가능.

## Phase 1 — 캘리브레이션: "Sobel/std ↔ PSNR-고정 시 필요 gaussian 개수" 관계 구하기

**목적**: per-frame 예산을 정하려면 먼저 "이 프레임은 gaussian이 몇 개 필요한가"를
그 프레임의 내용 통계만으로 예측할 수 있어야 한다. 지금은 가설일 뿐 — 관계 곡선을
실제로 측정하는 게 axis2/3 작업의 선결 조건.

- **측정 설계**: 1253 시퀀스에서 keyframe들을 뽑아, 각 keyframe 주변 로컬 영역만
  다양한 gaussian 예산(예: 5개 수준)으로 독립 학습 → 로컬 PSNR이 목표치(예:
  baseline 대비 -0.1dB 이내)에 도달하는 **최소 gaussian 개수**를 프레임별로 기록.
- **내용 통계**: 같은 프레임의 GT 이미지에서 (a) Sobel gradient magnitude
  평균/분산 (b) 픽셀 밝기 std — exp54 축7에서 이미 이식한 계산 재사용.
- **산출물**: (Sobel 평균, std) → 필요 gaussian 개수의 산점도/회귀선. exp51의
  λ 스캔, exp25의 tau 스캔과 같은 방식의 "관계 곡선 리포트"로 문서화.
- **리스크**: "로컬 영역만 독립 학습"이 실제 incremental map()의 공동 최적화와
  다이나믹이 다를 수 있음(주변 keyframe들과 공유하는 gaussian 때문에 완전히
  독립적인 "이 프레임만의 필요 개수"를 분리하기 어려움) — 근사치로 취급하고,
  Phase 2에서 실제 온라인 루프에 넣었을 때 재검증 필요.

## Phase 2 — Per-frame 적응 예산 컨트롤러 구현

Phase 1의 관계식이 나오면:

1. `create_pcd_from_image_and_depth()`(exp54 축7에서 PPM 경로 추가한 바로 그 함수)에
   **셋째 경로**를 추가 — 현재 `downsample_factor`(고정 상수)를 프레임별 Sobel/std
   통계로부터 계산한 **적응적 downsample_factor**로 대체.
2. **init을 최소로**: `pcd_downsample_init`을 지금보다 훨씬 크게(성기게) 주고, 각
   keyframe의 상한은 Phase 1 곡선으로 계산 — 이후 `densify_and_prune`이 그 상한
   **이내에서만** 채우도록 `size_threshold`/`densify_grad_threshold`에 상한 캡
   로직을 추가(현재 VIGS엔 "이 gaussian 수를 넘으면 densify 중단" 로직이 없음 —
   신규 구현 필요, `gaussians._xyz.shape[0]`를 densify_and_prune 호출 전에 체크).
3. **측정**: exp54와 동일한 하네스(온라인 루프 총합/PSNR/evo APE/최종 gaussian
   개수)로 1253 재검증. **핵심 비교 대상은 exp54의 최종 채택 레시피(61.34s,
   0.94배, PSNR 22.78/23.14)** — 같은 시간에 PSNR이 더 높아지는지, 혹은 같은
   PSNR을 더 짧은 시간에 달성하는지 둘 다 확인.

## Phase 3 — Carve loss 이식 (CLAUDE.md North Star 2단계와 합류)

이 항목은 원래 프로젝트 로드맵의 **"[그다음] floater 억제(carve loss)를 고품질
지도 위에 이식"** 단계와 정확히 같은 작업이다 — exp55가 밀도 제어 축을 다루다가
자연스럽게 이 단계를 앞당기게 됨.

- **왜 지금 필요한가**: Phase 2의 적응 예산이 densify를 더 활발하게 만들수록(특히
  엣지 프레임에서 급격히 densify) 신생 gaussian의 위치 품질이 불안정해질 위험이
  커짐 — exp38~44d2에서 이미 "densification floater(Pop2)"로 규명된 바로 그
  메커니즘. carve loss가 이를 억제하는 검증된 방법.
- **포팅 난이도 — 정직하게 기록**: `3dgs-custom/eval/carve_loss.py`의
  `CarveLoss`는 **"카메라 전체 + SLAM anchor 전체로 한 번에" evidence field를
  빌드**하는 배치/오프라인 구조(`_build_fields`가 전체 camera 리스트를 받음) —
  VIGS의 온라인 루프는 미래 keyframe을 아직 모르므로 이 구조를 그대로 못 씀.
  **미해결 설계 질문**: (a) 지금까지 도착한 keyframe만으로 field를 매번 재구성
  (비용 문제 — voxel field 빌드가 얼마나 무거운지 먼저 측정 필요) (b) 슬라이딩
  윈도우로 최근 N개 keyframe만 반영하는 근사 field (c) 완전히 다른 저비용 온라인
  근사(예: VIGS 자체의 `disps_up`은 이미 BA로 정제된 depth이므로, carve loss의
  depth-violation 채널만 골라 쓰는 게 voxel field보다 훨씬 가벼울 수 있음 —
  `vigs.py:169`에서 이미 확인한 "depth가 포즈와 공동 최적화됨" 특성과 맞물림).
  **이 설계 질문 자체가 Phase 3의 첫 작업**이지 바로 코드 이식이 아님.
- **측정**: region GT 지표(`floater_metric_region.py`, exp43에서 교차 장면
  검증된 그 지표)를 incremental 결과물에도 적용할 수 있는지부터 확인 —
  현재 VIGS 출력이 이 지표가 기대하는 입력 형식(3D 마스크 등)과 호환되는지
  미확인.

## 실행 순서 제안 (미착수)

1. Phase 1 캘리브레이션 — 관계 곡선 없이는 Phase 2가 그냥 또 다른 임의의 상수
   스윕이 되어버림, 반드시 먼저.
2. Phase 2 — Phase 1 곡선을 실제 온라인 루프에 넣어 exp54 최종 레시피 대비
   시간/품질 트레이드오프 재검증.
3. Phase 3 — Phase 2가 floater를 실제로 늘렸는지(시각 진단 + 가능하면 region GT)
   확인한 뒤에만 착수. Phase 2 결과가 floater 증가를 안 보이면 Phase 3의 시급성
   자체가 낮아질 수 있음 — 순서를 건너뛰지 말 것.

## 열린 질문 / 리스크 요약

- "적게 시작해 키우는 쪽이 싸다"는 전제가 **이미 tracking-bound인 현재 지점**에서
  여전히 유효한지 axis2/6+2 결과로 볼 때 불확실 — Phase 1/2가 이걸 직접 답해야 함.
  (mapping이 다시 병목이 되는 지점까지 예산을 낮춰야 효과가 보일 수도 있음.)
  ⚠ **미계측을 방치하지 말 것**([[feedback_verify_unmeasured]] 원칙) — "그럴 것
  같다"로 넘기지 말고 Phase 1에서 실측.
- Phase 1의 "로컬 영역 독립 학습"이 실제 온라인 공동 최적화와 다른 결과를 줄 수
  있음 — 근사치로 취급.
- Phase 3(carve loss)은 구조적으로 배치 가정(전체 카메라 사전 확보)에 기반해
  있어 이식이 아니라 사실상 재설계에 가까움 — 과소평가 금지.
