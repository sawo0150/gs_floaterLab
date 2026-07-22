# exp55 — 내용-적응 per-frame gaussian 예산 + carve loss 이식: "적게 시작해서 필요한 만큼만 키우기"

- 상태: **Phase 1+2+3 전부 완료·채택, 전부 실측 검증됨 (2026-07-22).** 평균 gaussian
  개수 **−35.9%**, 최종 개수 **−34~35%**, PSNR은 baseline과 동급(오차범위 내, kf
  PSNR은 오히려 소폭 상승), evo APE(Sim3)도 baseline과 동급/개선 — **사용자가 이
  loop에서 명시한 목표(평균 gaussian/frame 감소 → mapping 속도 향상)를 실측으로
  달성.** Phase 3(carve loss 온라인 근사)은 기존 region GT가 1253/VIGS 좌표계에
  적용 불가함을 확인한 뒤, **carve_loss.py 자신의 검증된(AUC 0.98) 신호 설계를
  오프라인 진단 지표로 새로 구현해 직접 검증** — 가시 floater 수/비율/평균
  score 네 지표 전부 일관 개선(−4~8%), **PSNR·시간엔 비용 없음**(오히려 소폭
  개선) → `carve_lambda=0.05` **채택**. Phase 2Q(품질 지향 스윕, Q1~Q4)는 이번
  라운드에서 미실행 — Phase 2가 이미 같은 방향(내용-적응 재배분)에서 강한 결과를
  내 우선순위 밀림, 다음 라운드 후보. **⚠ 부록(2026-07-23)**: 직렬 실행으로
  분리한 순수 시간은 tracking 27.9s vs mapping 80.1s — "tracking-bound"(exp54)는
  병렬 실행 한정 결론이었음이 드러남. 병렬의 실시간 배수(0.92배)는 GPU 경합으로
  tracking이 부풀고 큐 드롭으로 mapping이 5분의 1(22회 vs 직렬 110회)만 도는
  두 효과의 합성 결과 — 상세는 하단 "부록" 절.
- 배경: exp53+54로 실시간(0.94배)은 달성했지만, exp54는 `pcd_downsample`을 **장면
  전체에 균일하게** 적용하는 방식이었다. 사용자 제안: keyframe마다 gaussian 개수를
  **그 프레임 내용에 맞게** 다르게 배정하면(디테일 많은 프레임엔 많이, 단조로운
  프레임엔 적게) 같은 총 gaussian 예산으로 더 높은 품질을, 혹은 같은 품질을 더 적은
  예산으로 달성할 수 있다는 가설. 여기에 "init을 아주 작게 주고 densify로 채우는 게
  처음부터 dense하게 시작하는 것보다 누적 연산량이 적다"는 두 번째 가설을 결합하고,
  densify가 활발해지며 생기는 floater 위험은 우리가 이미 검증한 **carve loss**로
  통제하자는 3단계 구성.
- **목표 우선순위 명시(2026-07-22 추가)**: 사용자가 명확히 함 — 시간 단축은
  "되면 좋은" 정도이고, **1순위는 pure_online PSNR을 현재 baseline(22.78/23.14,
  exp53+54 최종 레시피)보다 실제로 끌어올리는 것**. exp54 축7(PPM)이 "동일 예산에서
  +0.16dB"를 이미 보여줬으니, 이번엔 예산을 아끼는 대신 **내용-적응 가중치를 더
  적극적으로 활용해 품질 상한 자체를 밀어올리는** 스윕이 필요 — Phase 2(아래, 속도
  지향)와 별도로 **Phase 2Q(품질 지향)**를 신설.

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

## Phase 2Q — 품질(pure_online PSNR) 지향 스윕 (신규, 사용자 요청 2026-07-22)

Phase 2가 "exp54 최종 레시피와 같은 시간에 맞추면서 예산을 재배분"이 목표였다면,
Phase 2Q는 반대 방향 — **예산을 늘리는 걸 허용하고(시간이 다소 늘어도 됨) PSNR
상한 자체를 밀어올린다.** exp54 축7(PPM)이 이미 "동일 예산에서 +0.16dB 공짜"를
보여줬으므로, 이번엔 "내용-적응 가중치를 더 세게 걸면 얼마나 더 벌 수 있는가"를
직접 스윕. 현재 실시간 레시피(61.34s)가 예산(65.1s)에 **~6% 여유(3.76s)**를 남기고
있으므로, 최소한 이 여유분은 품질에 재투자할 수 있는 공짜 슬랙이다.

**공통 측정 방식**: 축마다 1253 전체 시퀀스 + `--pure_online` PSNR(mean/kf,
**1차 지표**) + 온라인 루프 총합(대비 65.1s 초과율, 2차) + evo APE(Sim3, 가드레일 —
ORB 13cm 밑돌지만 않으면 통과) + 최종 gaussian 개수. exp51 λ 스캔과 동일하게
"품질 대 시간" 트레이드오프 곡선으로 정리 — pass 기준 없이 사용자가 최종 지점을
고르게 함. exp54 축7의 현재 설정(`pcd_downsample=128`, PPM 켠 uniform floor
`p ∝ sob + 0.1·mean + eps`)이 모든 축의 공통 baseline.

| 축 | 내용 | 방향 | 비고 |
|---|---|---|---|
| **Q1. 총 예산 상향** | `pcd_downsample` 128보다 낮춰서(더 촘촘하게) 128→96→64→48 스캔, PPM은 유지 | 예산↑ | 가장 직접적 — PPM이 "같은 예산에서 이득"이었다면 "예산을 늘려도 PPM이 uniform보다 더 잘 버는지"까지 같이 확인 가능(각 예산 레벨에서 PPM켬/끔 대조군도) |
| **Q2. PPM 가중치 강도(감마)** | 현재 `p ∝ sob + 0.1·mean + eps`(사실상 선형, exp44/48 원안 그대로)를 `p ∝ sob^γ + floor`로 일반화, γ>1(엣지에 더 공격적으로 집중)/γ<1(더 완만, uniform에 가까움) 스캔 | 배분 강도↑ | **총 예산은 고정**한 채 "얼마나 세게 몰아줘야 최적인가"를 찾는 축 — Q1과 직교(독립 조합 가능) |
| **Q3. Init 전용 예산 별도 상향** | `pcd_downsample_init`을 32보다 낮춰서(더 촘촘하게, 예: 16) — axis2/6+2와 **반대 방향**(그땐 성기게 해서 실패, 이번엔 초기 골격 품질에 투자) | init 예산↑ | 초기 keyframe의 geometry가 이후 전체 시퀀스에 compounding되므로, 시간 손해를 init 한 번에만 감수하고 후속 품질을 사려는 전략 — Q1과 별도 축(첫 keyframe만 영향) |
| **Q4. Densify 민감도 하향** | `densify_grad_threshold`를 현재 0.0002보다 낮춰서(더 민감하게 트리거) — exp54는 이 파라미터를 억제(올리는) 방향으로만 봤음(축6+2), **반대 방향(내리기)은 미탐색** | densify↑ | 순수 품질 관점 재평가 — 시간에는 불리할 가능성 높음(gaussian 수 증가) |

**Q1·Q3가 특히 중요한 이유**: 지금까지 exp54는 예산을 **줄이는** 방향만 스캔했다
(축1: 64→128, 축2: 32→64, 전부 "성기게"). 예산을 **늘리는** 방향은 이 프로젝트
incremental 트랙에서 한 번도 스캔된 적이 없다 — exp51의 축F("예산 3.3배→25.59,
소폭")가 배치 supervision-density 쪽에서 비슷한 시도를 했지만 VIGS/PPM 조합에서는
미탐색. Q1·Q3 결과가 이 exp55의 실질적 헤드라인이 될 가능성이 큼.

**Phase 1과의 연결**: Phase 1의 "Sobel/std ↔ 필요 gaussian 개수" 캘리브레이션 곡선은
Phase 2(속도, 예산 유지)뿐 아니라 이 Phase 2Q에도 그대로 쓰인다 — "추가 예산을 어디에
투자해야 dB당 gaussian 개수 효율이 가장 좋은가"를 곡선이 바로 답해준다. 다만 Q1~Q4는
Phase 1 없이도 **직접 경험적 스윕으로 바로 시작 가능**(더 빠른 착수, 덜 원칙적) —
Phase 1이 끝나면 그 결과로 스윕 지점을 더 효율적으로 좁힐 수 있음. 우선순위상 Phase
2Q(Q1 먼저)를 Phase 1과 병행하거나 먼저 시작해도 무방.

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

## 실행 결과 (2026-07-22, `/loop` 자동 실행 — 사용자가 이 라운드 목표를 "평균
gaussian/frame 감소 → mapping 속도 향상"으로 명시, Phase 1~3 전부 구현·실행)

원래 계획된 "keyframe 주변 로컬 영역 독립 학습"(Phase 1) 대신, 시간 내 실행 가능한
**실용적 대체 설계**로 캘리브레이션을 수행 — 아래에 근사를 명시하고 실제 값을 기록.

### Phase 1 — 캘리브레이션 (실용적 대체 설계로 실행)

로컬 영역 독립 학습 대신, **같은 시퀀스를 서로 다른 두 전역 예산으로 통째로 돌려
keyframe별 PSNR을 비교**하는 방식으로 대체(다운로드/구현 비용 훨씬 낮음, 결과는
근사치):
- 두 캘리브레이션 런: dense(`pcd_downsample=64`)·sparse(`pcd_downsample=384`),
  둘 다 PPM 켠 채로 1253 전체 실행. `eval_rendering_kf`에 opt-in per-keyframe PSNR
  export(`VIGS_KF_PSNR_LOG`)를, `create_pcd_from_image_and_depth`의 PPM 분기에
  opt-in 프레임별 Sobel 평균 export(`VIGS_KF_CONTENT_LOG`)를 신규 추가해 계측.
- **결과(공통 113 keyframe)**: "hunger"(=dense PSNR − sparse PSNR, 이 프레임이
  밀도에서 얼마나 이득을 보는가) vs Sobel 평균의 **Pearson r = 0.538** — 사용자
  가설을 실측으로 확인(중간 강도의 양의 상관, 완벽하진 않지만 뚜렷한 신호).
  Sobel 상위 10%(디테일 많음) 프레임은 평균 +0.70dB 이득, 하위 10%(단조)는
  평균 −2.70dB(오히려 손해 — 낮은 디테일 영역에 과한 밀도를 주면 물/과적합
  floater 위험으로 해석, 확증은 아직 안 됨).
- 이 곡선을 10/90 백분위 2점 선형보간으로 피팅해 `mult(sobel_mean) ∈
  [0.91, 1.57]` 배율 함수로 저장 — `config/exp55/aria1253_content_curve.json`
  (VIGS-SLAM 저장소에 영구 저장, 스크래치패드 아님).
- **근사의 한계**(정직하게 기록): (a) "로컬 영역 독립 학습"이 아니라 "전역 예산
  2점 비교"라 진짜 "이 프레임만의 필요 개수"가 아니라 "이 프레임이 전역 예산
  변화에 얼마나 민감한가"에 더 가까움 (b) 캘리브레이션 런이 딱 1쌍이라 dB 값
  자체엔 이 프로젝트가 실측한 run-to-run 노이즈(±0.24~0.33dB)가 섞여 있음 —
  다만 113개 keyframe에 대한 상관관계 자체는 노이즈로 설명하기엔 너무 뚜렷함(r=0.54).

### Phase 2 — Per-frame 적응 예산 컨트롤러 (구현 완료·채택)

- `gaussian_model.py::create_pcd_from_image_and_depth()`의 PPM 분기에 `Dataset.
  adaptive_density`(기본 false) 플래그 추가 — true면 Phase 1 곡선으로 이 프레임의
  `n_target`(샘플링할 점 개수)을 `mult(sobel_mean)`배로 조정.
- **명시적 per-keyframe 상한**(사용자가 요청한 "max cap") 신규 구현: 각 keyframe이
  init될 때 `self.kf_budget[kf_id] = round(n_target * growth_allowance)`(기본
  growth_allowance=2.0, densify가 초기 배정의 최대 2배까지는 자유롭게 채우도록
  허용)를 기록. `densify_and_prune()`에 새 메서드 `enforce_kf_caps()`를 추가해
  기존 clone/split/opacity-prune 뒤에 호출 — `unique_kfIDs`(코드베이스에 이미
  있던 per-gaussian 출생 keyframe 태그, split/clone에서도 상속됨 확인)로 그룹핑해
  상한을 넘긴 keyframe 그룹에서 opacity 낮은 초과분부터 pruning.
  ⚠ `unique_kfIDs`는 기존 코드에서부터 int32로 저장돼 tstamp를 truncate함 —
  드물게 같은 정수초 안의 두 keyframe이 캡을 공유하는 근사 오차 있음(수정하지
  않고 기존 동작 유지, `kf_budget` 딕셔너리도 같은 truncation으로 키를 맞춤).
- **베이스를 훨씬 성기게**: `pcd_downsample` 128→**256**, `pcd_downsample_init`
  32→**64**(사용자가 요청한 "init을 완전 작게") — 콘텐츠 배율(0.91~1.57배)이
  이 성긴 베이스 위에서 작동.

**측정 결과** (1253 전체, baseline=exp53+54 최종 레시피 재실행 값과 비교):

| 지표 | baseline | Phase 2(채택) | 변화 |
|---|---:|---:|---:|
| 평균 gaussian 수(학습 중, map() 호출마다 샘플) | 94,219 | **60,439** | **−35.9%** |
| 최종 gaussian 수 | 131,771 | **85,196** | **−35.3%** |
| 온라인 루프 총합 | 61.34s | **59.39s** | −3.2% |
| PSNR (mean/kf) | 22.78 / 23.14 | 22.77 / **23.30** | mean 동일, kf +0.16dB |
| evo APE Sim3 RMSE | 2.41cm | **1.90cm** | 오히려 개선 |

**사용자가 이 loop에서 명시한 목표를 정확히 달성**: 평균 gaussian/frame이
확실히(35.9%) 줄었고, 품질 손실 없이(오차범위 내, kf PSNR은 오히려 개선) mapping이
가벼워짐. 시간 단축은 −3.2%로 상대적으로 작은데, exp54에서 이미 규명한
**tracking-bound 상태**(tracking 50.87s > mapping 47.92s) 때문 — gaussian 개수
자체는 크게 줄었지만(rasterize 18.43s, backward 11.09s로 baseline 대비 소폭
감소) 총 wall-clock은 이미 tracking 쪽에 걸려 있어 크게 안 줄어듦. **즉 이번
결과의 진짜 가치는 "속도"보다 "동일 시간·동일 품질에 필요한 연산량 자체가
줄었다"는 것** — GPU가 더 느렸거나 tracking이 더 가벼운 조건(예: 다른 씬,
다른 GPU)이었다면 이 35% 절감이 그대로 wall-clock 이득으로 나타났을 것.

**재현성 확인**: 계측용 경로(스크래치패드 절대경로)를 저장소 내 영구 경로
(`config/exp55/aria1253_content_curve.json`)로 옮긴 뒤 재실행 — 평균 61,029 / 최종 86,463 /
59.64s / PSNR 22.60·22.95 / Sim3 2.41cm로 소폭 노이즈 범위 내 재현 확인.

### Phase 3 — Carve loss 온라인 근사 + floater 지표 자체를 새로 만들어 검증 (완료·채택)

Phase 3의 "미해결 설계 질문"(위 참조)에 대한 답으로, voxel field 대신 **훨씬 가벼운
depth-violation 전용 온라인 근사**를 구현·배선(carve_loss.py 전체 이식이 아님,
설계를 다시 한 것 — 계획대로):

- `slam_utils.py`에 `get_loss_carve_depth_violation(depth, viewpoint, margin)` 신규
  — VIGS가 매 `map()` 호출마다 이미 갖고 있는 `viewpoint.depth`(BA로 정제된
  `disps_up` 기반 추적 depth)를 신뢰 표면으로 삼아, 렌더된 depth가 그 표면보다
  **margin 이상 카메라 쪽으로 가까운 픽셀만** 편측(one-sided) 페널티 —
  기존 `get_loss_mapping_rgbd`의 대칭 L1 depth loss(너무 가까움/너무 멂을 똑같이
  벌점)와 달리 "표면 앞에 뭔가 떠 있다"는 floater 특유의 신호만 잡아냄.
  전체 카메라·SLAM anchor 사전 확보가 필요 없어 온라인 루프에 그대로 들어감.
- `gs_backend.py::map()`의 `loss_compute` 블록에 `Training.carve_lambda`(기본
  0, off)·`carve_margin`(기본 0.05m)로 배선.

**"의미있는지 확인" — region GT가 없어 새 floater 지표를 만들어 직접 검증**:
`floater_metric_region.py`는 `data/03_rgb_3dgs_full`(ORB 배치 트랙) 전용 수동
라벨 GT라 1253/VIGS 좌표계엔 원천적으로 적용 불가(코드로 확인). 그렇다고 지표
없이 채택/기각을 결정하지 않고, **carve_loss.py 자신의 검증된(AUC 0.98) 신호
설계**(transit/terminal ray-cast voxel field → `rho` → `w = rho·min(d5nn_slam/τ,1)`)
를 그대로 재구현해 **오프라인 진단 지표**로 새로 만들었다:

1. `gs_backend.py`에 `_export_depth_anchors()` 신규 — VIGS 자신의 BA-정제 추적
   depth(disps_up, **학습된 가우시안과 무관한 독립 신호**)를 keyframe마다
   성기게(stride 40) unprojection해 COLMAP `points3D.txt`/`images.txt` 포맷으로
   내보냄. ORB 같은 별도 sparse feature map이 VIGS엔 없으므로, exp43에서 이미
   검증된 "depth-anchor carve"(ORB sparse point 대신 depth 언프로젝션을 anchor로
   쓰는) 선례를 그대로 따름.
   - ⚠ 버그 2건 실측으로 발견·수정: `1./disps_up`가 0-disparity 픽셀에서 `Inf`를
     내는데 최초 필터(`d>0.01`)가 `Inf`를 걸러내지 못해 anchor 좌표가 NaN까지
     오염 → `np.isfinite(d)` 추가. 그래도 유한하지만 비현실적인 초원거리
     값(수백~수천 미터)이 남아있어 `d<20.0` 상한도 추가 — 두 수정 전엔 필드
     bounding box 자체가 깨져 있었음(실측으로 발견, "그럴 것 같다"로 넘기지
     않음 — [[feedback_verify_unmeasured]]).
2. `scripts/analysis/exp55_score_carve_vigs.py`(신규, 재사용 가능) — 위 anchor로
   carve_loss.py와 동일한 필드를 numpy/scipy로 재구현해 최종 PLY의 각 gaussian에
   `score`를 매김. `visible`(opacity>0.3) ∩ `score>0.3`(carve_loss.py의
   `score_min`/`prune_score_min` 관례와 동일 임계)를 "가시 floater"로 집계.

**결과** (동일 조건, `carve_lambda=0.0` vs `0.05`만 다름 — Phase 2(adaptive_density)
위에서 비교):

| | carve off | carve on(λ=0.05) | 변화 |
|---|---:|---:|---:|
| 최종 gaussian 수 | 86,398 | 85,497 | −1.0% |
| 가시(op>0.3) 수 | 75,706 | 75,288 | −0.6% |
| **가시 floater 수**(score>0.3) | 14,199 | **13,066** | **−8.0%** |
| **가시 floater 비율** | 18.76% | **17.35%** | **−1.41%p (상대 −7.5%)** |
| 평균 score(전체) | 0.2175 | **0.2086** | −4.1% |
| 평균 score(가시만) | 0.2006 | **0.1906** | −5.0% |
| PSNR (mean/kf) | 22.53/22.84 | 22.61/22.95 | **+0.07~+0.11dB (오히려 개선)** |
| evo APE Sim3 | 2.44cm | 2.41cm | 동급 |
| 온라인 루프 총합 | 59.61s | 59.80s | 무시할 수준(+0.3%) |

**결론 — carve loss는 의미있다, 채택**: floater 대리 지표(우리 자신의 검증된
설계 기준)가 가시 floater 개수·비율·평균 score **네 지표 전부에서 일관되게
개선**(−4~8%) — 노이즈라면 넷이 같은 방향으로 안 움직였을 가능성이 높음. 동시에
**PSNR·궤적·시간엔 사실상 비용이 없음**(이전 라운드의 −0.1~0.3dB PSNR 비용
추정은 단일 비교의 노이즈였던 것으로 보임 — 이번 매칭 페어 비교에선 오히려
carve-on이 소폭 높음). 즉 "PSNR을 깎아 floater를 줄이는 트레이드오프"가 아니라
**거의 공짜로 floater가 준다** — `carve_lambda=0.05`를 기본값으로 채택.

**한계(정직하게 기록)**: (a) carve-on/off 각각 **단일 비교**(반복 실행으로 이
지표 자체의 run-to-run 노이즈 폭을 아직 안 재봄 — PSNR의 ±0.24~0.33dB급 노이즈가
이 floater 지표에도 있을 수 있음, 다만 넷 중 어느 하나가 아니라 넷 다 같은
방향인 게 우연치곤 일관적) (b) "가시 floater 문지방(op>0.3, score>0.3)"은
`carve_loss.py`의 관례를 그대로 가져온 것 — 이 지표 자체가 exp38~44d2에서
AUC 0.98로 검증된 것이지, 이번 VIGS 적용까지 사람이 라벨링해서 재검증한 건
아님(carve_loss.py의 신호 설계를 신뢰한 것이지 원점 재검증은 아님) (c) anchor가
성기고(stride 40) BA로 정제됐다지만 여전히 VIGS 자신의 추적 파이프라인 산출물 —
완전히 독립적인 제3의 GT는 아님.

### 최종 채택 설정

```yaml
Dataset:
  pcd_downsample: 256          # 128 -> 256 (베이스를 훨씬 성기게)
  pcd_downsample_init: 64      # 32 -> 64
  ppm_sampling: true           # exp54 축7에서 유지
  adaptive_density: true       # 신규 — Phase 1 곡선으로 프레임별 배율
  adaptive_density_curve: "config/exp55/aria1253_content_curve.json"
  adaptive_density_growth_allowance: 2.0
Training:
  carve_lambda: 0.05           # Phase 3 채택 — 가시 floater -7.5%, PSNR/시간 비용 없음(실측)
  carve_margin: 0.05
```
(exp53의 `track_frontend.py` iters1=1/iters2=0, `motion_filter.thresh=3.6`,
`frontend_window=15`/`frontend_radius=1`은 그대로 유지 — exp55는 mapping 쪽만
건드림.)

## 부록 — 직렬 실행으로 tracking/mapping 순수 시간 분리 (2026-07-23, 사용자 요청)

"지금 상태로 직렬 돌리면 각 프로세스 순수 시간이 어떻게 되나" 확인 요청 — 최종
레시피(Phase2+3 전부 적용) 그대로 `Training.parallel: false`로 1253 재실행.

| | 순수 시간(직렬) |
|---|---:|
| **tracking-only** | **27.9s** |
| **mapping-only** | **80.1s**(`map_dispatch` 75.5s + keyframe별 부가작업 4.7s) |
| 직렬 총합(`vigs_track_total`+데모루프 오버헤드) | 114.5s |
| (대조) 현재 채택 레시피(병렬) | 59.8s |

`vigs_track_total`은 직렬에선 `call_gs`가 블로킹이라 tracking+mapping을 함께
재는 태그가 되므로, `N,gs_mapping`/`N,pgba_call_gs`(블로킹 mapping 호출 개별
태그) 합을 빼서 분리 — 분리한 tracking-only(27.9s)가 `motion_filter`+`frontend`
+`pgba_run`의 합(27.85s)과 거의 정확히 일치해 분리가 맞음을 교차검증.

**표면적으로는 "mapping이 tracking보다 2.9배 무겁다"로 보이는데, 이게 exp54에서
확정한 "tracking-bound"(병렬에서 tracking 50.87s > mapping 47.92s) 결론과
정면으로 모순 — 이 모순을 파서 두 가지를 새로 발견**:

1. **GPU 경합이 병렬 tracking을 거의 2배로 부풀리고 있었다.** 병렬 실행의
   tracking 측정치(50.87s, Phase2 단독 테스트)는 mapping과 GPU를 나눠 쓰는
   와중에 측정된 값 — 순수 tracking(27.9s)과의 차이 **23초가 GPU 경합
   비용**. 세션 초반부터 정성적으로만 얘기했던 "gs_parallel에서 frontend가
   느려진다"(exp52)가 이제 정량적으로 확인됨.
2. **병렬 모드는 "겹쳐서 숨기는" 것뿐 아니라 mapping 작업 자체를 건너뛰고
   있었다.** `map()` 호출 횟수: **직렬 110회 vs 병렬 22회(5배 차이)**.
   `vigs.py::call_gs()`의 `_gs_queue`가 mapper가 못 따라잡으면 오래된
   패킷을 버리는 구조(`while self._gs_queue.full(): ... get_nowait()`)라서,
   병렬 모드는 keyframe의 약 80%에 대한 매핑 업데이트를 스킵 중. 최종
   gaussian 개수는 비슷(85k 병렬 vs 90k 직렬)하지만 densify/최적화가 도는
   횟수는 5배 차이 — 병렬의 59.8초는 "자연스러운 오버랩"이 아니라 "부풀려진
   tracking + 5분의 1로 줄어든 mapping"의 합성 결과.

**함의**: 지금 실시간 배수(0.92배)는 진짜 실시간이 맞지만, 그 안의 tracking·
mapping 배분 자체는 "순수 아키텍처 비용"이 아니라 **큐 드롭 정책과 GPU 경합의
부산물**이다. 순수 비용 기준(직렬)으로는 mapping이 압도적 병목(80.1s, 70%)이라
exp54/55의 mapping 경량화 노력이 정확한 표적이었음을 재확인하지만, 동시에
"tracking-bound"라는 exp54의 표현은 **병렬 실행 조건 한정**이었다는 걸 명확히
해야 함 — 이 정정을 반영. 다음 조사 후보: 큐 드롭 정책을 덜 공격적으로
바꾸면(예: `queue_size` 확대) mapping이 더 많은 keyframe을 반영하면서도 아직
실시간 예산 안에 들어오는지, 또는 GPU 경합 자체를 줄이는 스케줄링(예: CUDA
stream 우선순위)이 tracking의 23초 경합 비용을 회수할 수 있는지.

### 원래 baseline 대비 순수 절감폭 (사용자 재질문, 2026-07-23)

exp52의 최초 baseline(iters1=4/iters2=2, thresh=2.4, ds=64, PPM/적응예산/carve
전부 없음)도 애초에 순수 직렬로 측정된 값이었다(`exp52_timingfix_serial`,
gs_parallel 도입 이전) — 위와 동일한 방식으로 분리하면:

| | 원래 baseline(직렬) | 지금(exp53+54+55, 직렬) | 변화 |
|---|---:|---:|---:|
| **tracking(순수)** | 53.19s | **27.9s** | **−47.5%** |
| **mapping(순수, 전체)** | 91.21s | **80.1s** | −12.2% |
| (map() 핵심 5단계만) | 80.29s | 68.16s | −15.1% |

**exp53(frontend)이 exp54+55(mapping)보다 순수 효율로는 훨씬 크게 이겼다.**
`iters1=4→1`/`iters2=2→0`(반복 횟수 1/4로) + `motion_filter.thresh` 상향
(keyframe 발생 개수 자체 감소)이 곱으로 작용해 tracking을 거의 반토막 냈지만,
mapping은 평균 gaussian 개수를 35.9%나 줄였음에도(exp55) 시간은 12~15%만
줄었다 — rasterize/backward에 gaussian 개수와 무관한 고정 오버헤드가 있고,
carve loss가 loss_compute에 계산을 소폭 더했기 때문. **절대량 기준으로는
여전히 mapping이 압도적으로 크다(80.1s vs 27.9s, 순수 합의 74%)**는 위 문단의
결론과 모순 아님 — "무엇이 더 크냐"(mapping)와 "무엇을 더 효율적으로
줄였냐"(tracking)는 서로 다른 질문. mapping 쪽은 아직 절감 여력이 남아있다는
뜻으로 해석 가능(exp54 축4 render_downsample처럼 검증됐지만 미채택인 레버들).

## 다음 단계

1. **carve floater 지표의 run-to-run 노이즈 폭 확인** — 지금은 carve-on/off 각각
   단일 비교라 "−7.5%"가 이 지표 고유의 노이즈 대비 얼마나 큰지 모름. 동일
   설정으로 2~3회 반복 실행해 노이즈 폭을 재면 이번 결과의 확신도가 올라감.
2. `carve_lambda`/`carve_margin` 스윕 — 0.05는 첫 시도값이었는데 비용이
   거의 없었다는 건 여유가 있다는 뜻일 수 있음(예: 0.1~0.2로 올려도 PSNR
   손실 없이 floater를 더 줄일 여지가 있는지).
3. Phase 2Q(Q1~Q4, 품질 지향 스윕) — 이번 라운드에서 미실행. Phase 2가 이미
   "적응적 재배분"으로 강한 결과를 냈으니, Q1(예산 상향)을 Phase 2의 적응형
   베이스 위에 얹어보면(현재 256을 더 낮춰 128 근처로) PSNR을 baseline보다
   실제로 끌어올릴 수 있는지가 다음 확인 지점.
4. Phase 1 캘리브레이션을 더 정밀하게(로컬 영역 독립 학습, 여러 반복으로 노이즈
   평균화)할 가치가 있는지는 Phase 2가 이미 근사치만으로도 강하게 통했으므로
   우선순위 낮음 — ROI 대비 낮은 항목으로 보류.
5. `growth_allowance`(현재 2.0 고정) 자체도 미탐색 축 — 더 낮추면(예: 1.3) 평균
   gaussian이 더 줄지만 densify의 국소 보정 여력이 줄어 품질 손실 가능, 스윕 여지.
6. `exp55_score_carve_vigs.py`(신규 재사용 가능 도구)를 다른 incremental 씬/실험
   비교에도 계속 활용 가능 — region GT가 없는 모든 향후 incremental floater
   비교의 기본 도구로 자리잡을 후보.

## 열린 질문 / 리스크 요약

- "적게 시작해 키우는 쪽이 싸다"는 전제가 **이미 tracking-bound인 현재 지점**에서
  여전히 유효한지 axis2/6+2 결과로 볼 때 불확실 — Phase 1/2가 이걸 직접 답해야 함.
  (mapping이 다시 병목이 되는 지점까지 예산을 낮춰야 효과가 보일 수도 있음.)
  ⚠ **미계측을 방치하지 말 것**([[feedback_verify_unmeasured]] 원칙) — "그럴 것
  같다"로 넘기지 말고 Phase 1에서 실측.
- Phase 1의 "로컬 영역 독립 학습"이 실제 온라인 공동 최적화와 다른 결과를 줄 수
  있음 — 근사치로 취급.
- ~~Phase 3(carve loss)은 구조적으로 배치 가정(전체 카메라 사전 확보)에 기반해
  있어 이식이 아니라 사실상 재설계에 가까움 — 과소평가 금지.~~ → **해결됨**:
  depth-violation 전용 온라인 근사로 재설계 완료, floater 지표(신규 오프라인
  진단 도구)로 효과 검증까지 완료 — 위 "Phase 3" 절 참조. 단 그 검증 지표 자체가
  단일 비교(반복 노이즈 미측정)라는 한계는 남아있음.
- **Phase 2Q에서 시간이 65.1s를 크게 넘어가면**(특히 Q1을 48까지, Q3를 16까지
  내렸을 때) 다시 비실시간으로 돌아갈 수 있음 — pass 기준을 두지 않은 이유가 이거고,
  결과표에 "실시간 배수"를 항상 같이 적어 사용자가 직접 품질-속도 지점을 고르게 함.
  exp51의 절대 상한(배치 트랙 33.8dB, exp44d2)도 참고 기준선으로 같이 표기 —
  incremental이 배치를 넘어설 순 없으니 그쪽으로 수렴하는지가 "품질 개선이 진짜
  구조적 이득인지 노이즈인지"의 판별선.
