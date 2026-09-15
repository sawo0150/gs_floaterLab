# VIGS-SLAM 논문 metric 계약과 baseline 수정 감사

작성: 2026-09-14  
상태: **비교 프로토콜 결정용 메모 - 최종 계약은 아직 잠그지 않음**

## 0. 이 문서가 답하려는 질문

우리 논문의 핵심 주장은 단순히 높은 PSNR이 아니라 **실시간 제약 안에서 성장하는
3DGS 지도의 품질**이다. 그러므로 다음 세 질문을 분리해야 한다.

1. VIGS-SLAM 논문의 RPNG/UTMM PSNR은 정확히 어떤 상태와 평가 집합에서 측정됐는가?
2. 논문의 비교 방법들은 정말 동일한 실행·종료·실시간 제약을 따랐는가? 아니라면
   저자들은 어떤 baseline을 어떤 이유로 수정했는가?
3. 논문값 재현, mapping 방법론 비교, 실제 end-to-end 실시간 비교를 우리 논문에서
   어떻게 분리해야 하는가?

이 문서의 표기:

- **[PAPER]**: VIGS-SLAM 본문/보충자료에 직접 명시된 사실.
- **[PUBLIC CODE]**: 공개 저장소 `origin/main@22ffe24c`에서 확인한 사실.
- **[LOCAL]**: 이 프로젝트의 재현·adapter 실행에서 확인한 사실.
- **[INFERENCE]**: 위 근거에서 도출한 해석. 논문 저자의 명시적 주장과 구분한다.

주요 원문은 [VIGS-SLAM arXiv v2 PDF](../../../paper/ref/vigs_slam/vigs_slam_zhu_et_al_arxiv_2512.02293v2.pdf)다.
PDF 페이지는 파일 자체의 1-based 페이지 번호로 적고, 괄호 안에는 논문/보충자료의
인쇄 페이지나 절 번호를 함께 적는다.

---

## 1. 먼저 고정해야 할 결론

### 1.1 논문 rendering 표는 strict 1× streaming 표가 아니다

**[PAPER]** 본문 §4는 DROID-SLAM, Splat-SLAM, HI-SLAM2, VIGS-SLAM의
`online setting`을 **final global BA와 final color refinement 이전 상태**로 정의한다.
이 두 refinement는 통상 10분 이상 걸리며, refinement 이후 수치는 보충자료에 따로
제시한다(PDF 8-9쪽). 보충 §9도 별도 언급이 없으면 final refinement 이전 online
performance라고 재확인한다(PDF 18-19쪽).

그러나 논문에는 다음 항목이 명시돼 있지 않다.

- 원본 timestamp를 1.0× 또는 1.5×로 wall-clock replay했는지
- 마지막 capture timestamp를 optimizer deadline으로 사용했는지
- sensor EOS 뒤 optimizer/topology update가 0회인지
- tracking/mapping queue가 밀릴 때 backpressure, drop, skip, drain 중 무엇을 했는지
- input decoding, tracking, mapping, queue drain 중 어디까지 runtime에 포함했는지
  (Table 9는 총 frame 수/총 runtime이라는 큰 범위만 정의)

따라서 논문의 `online`은 확실히 **pre-final causal state**를 뜻하지만, 우리가 쓰는
`strict native-rate / zero-tail`과 같은 wall-clock 계약을 뜻한다고 볼 근거는 없다.

### 1.2 논문 수치만으로는 RPNG 30 FPS 실시간 mapping을 증명하지 못한다

**[PAPER]** 보충 Table 8(PDF 17쪽)은 RPNG와 UTMM 입력을 모두 30 FPS로 기록한다.
보충 Table 9(PDF 19쪽)의 RPNG 평균은 다음과 같다.

| 항목 | 논문 값 |
|---|---:|
| 입력 RGB rate | 30 FPS |
| VIGS tracking | 39.83 FPS |
| VIGS tracking + GS mapping | 12.02 FPS |
| VIGS tracking + mapping peak memory | 8.51 GiB |

**[INFERENCE]** Table 9의 full-system 처리량 12.02 FPS가 source 30 FPS보다 낮으므로,
Table 18의 22.21dB를 “30 FPS 입력을 모두 보존하고, 원래 sequence duration 안에
mapping까지 끝내고, EOS에서 즉시 멈춘 결과”로 읽을 수 없다. 논문은 높은 online
pre-final 품질과 별도의 runtime 수치를 보여주지만, 두 수치를 strict sensor-clock
계약으로 결합하지 않았다.

### 1.3 논문의 real-time demo와 RPNG/UTMM metric benchmark는 별도 실험이다

**[PAPER]** 보충 §6(PDF 16쪽)의 real-time demo는 iPhone 17 Pro가 RGB+IMU를
Wi-Fi로 RTX 5090+i7-14700K desktop에 전송하는 live demo다. self-captured 입력은
10 FPS RGB, 400 Hz IMU이며 capture 중 intrinsics는 고정된다.

**[PUBLIC CODE]** 공개 README의 `demo_stream.py`도 저장 후 재생이 아니라 첫 frame부터
live SLAM을 시작한다고 설명한다. 다만 연결 종료 뒤 final BA를 수행하며, queue 지연,
drop 수, EOS zero-tail을 평가하는 공식 metric protocol은 제공하지 않는다.

따라서 다음 두 주장을 섞지 않는다.

- “10 FPS iPhone live demo가 동작한다.”
- “30 FPS RPNG/UTMM Table 18/19 품질이 strict real-time에서 나온다.”

첫 문장은 논문이 뒷받침하지만 두 번째 문장은 논문에 없는 추가 주장이다.

---

## 2. 논문의 metric·평가 집합 계약

### 2.1 Tracking

**[PAPER]** 본문 §4, Metrics(PDF 9-10쪽):

- `evo`로 estimated trajectory를 GT에 정렬한다.
- ATE RMSE를 cm 단위로 보고한다.
- Recall은 GT pose 중 translation error가 지정 threshold 아래인 비율이다.
- 초기화 불가 또는 큰 drift는 `F`로 처리한다.

논문의 tracking 표는 method/dataset에 따라 저자 재실행값과 기존 논문 전사값이 섞여
있다. 따라서 모든 ATE가 같은 실행 binary, hardware, seed, 종료 상태에서 나온 것은 아니다.

### 2.2 Rendering

**[PAPER]** 본문 §4, Metrics(PDF 10쪽):

- PSNR, SSIM, LPIPS를 보고한다.
- **어느 비교 방법에서도 keyframe으로 사용되지 않은 frame**을 사용한다.
- mapping에 들어간 모든 view를 제외한다.
- MM3DGS-SLAM rendering 값은 이 계약을 따르지 않아 직접 비교할 수 없다고 논문 스스로
  명시한다.

이 정의는 단순히 “VIGS 자신의 keyframe만 제외”하는 것이 아니다. 비교에 포함된 모든
방법의 keyframe union을 알아야 한다.

### 2.3 Pre-final과 after-refinement 표

**[PAPER]** 보충 Table 18/19(PDF 24-25쪽)은 각각 RPNG/UTMM에 대해 두 상태를 나눈다.

| 상태 | RPNG VIGS 평균 PSNR | UTMM VIGS 평균 PSNR | 용도 |
|---|---:|---:|---|
| Before Final Color Refinement | 22.21 | 20.87 | 본문 Table 3의 online rendering 값 |
| After Final Color Refinement | 25.18 | 21.00 | 종료 후 global color refinement 참고값 |

VINGS-Mono는 final color refinement를 수행하지 않는다고 표 caption에 명시된다.
따라서 after-refinement 표는 모든 방법에 동일한 후처리가 적용된 표도 아니다.

### 2.4 논문 평가 집합의 공개 재현 한계

**[PUBLIC CODE]** 공개 evaluator
`vigs/gaussian/utils/eval_utils.py:38-40,66-67`은 실제로 다음 union을 평가한다.

```text
index % 5 == 0 OR VIGS keyframe OR final frame
```

keyframe을 제외하는 코드는 주석 처리되어 있다. 논문이 요구한 all-method keyframe union
UID도 공개되지 않았다. 따라서 공개 artifact만으로 논문의 정확한 Table 18/19 evaluation
manifest를 복원할 수 없다.

우리 재현에서 사용하는 세 label은 다음처럼 유지한다.

1. `official_public`: 공개 evaluator 그대로, VIGS mapping keyframe 포함.
2. `paper_compatible_self_non_kf`: stride-5/final 중 VIGS 자신의 keyframe만 제외.
3. `predeclared_fixed_manifest`: 방법과 독립적으로 미리 고정하고 양쪽 mapping/birth에서 제외.

1과 2는 paper reproduction 진단이고, **3만 gsSLAM-vs-vanilla 공정 비교의 주 평가 집합**으로
사용한다.

---

## 3. 논문 VIGS-SLAM의 공개 implementation detail

### 3.1 공통 tracking/mapping 설정

**[PAPER]** 본문 §3.3과 보충 §9(PDF 7-8, 18-19쪽):

- optical-flow magnitude가 `2.4`를 넘으면 새 keyframe을 만든다.
- IMU preintegration 구간이 너무 길어지지 않도록 최소 3초마다 keyframe을 강제한다.
- IMU pose-init covariance trace가 `1e-4`를 넘으면 이전 keyframe pose로 fallback한다.
- loop candidate는 최소 55 keyframe 떨어진 과거 frame만 본다.
- loop flow threshold `22`, orientation threshold `120°`를 사용한다.
- vision-only initialization은 keyframe 10개에서 시작한다.
- inertial initialization keyframe 수는 기본 20, FAST-LIVO2 25, UTMM 15다.
- 새 keyframe마다 10 mapping iteration을 수행한다.
- 각 mapping iteration은 frontend graph keyframe과 global keyframe 2개를 사용한다.
- mapping loss는 color L1, depth L1, isotropic regularization의 가중합이다.

**[PUBLIC CODE]** 공개 `config/rpng.yaml`, `config/utmm.yaml`과
`vigs/gs_backend.py`에서 확인되는 추가 값:

- initial mapping service `init_itr_num=1050`
- current mapping window size `10`
- normal-depth regularization `lambda_dnormal=0.5`
- DSSIM weight `0.2`
- 기본 config에는 `Training.parallel`이 없으므로 공개 batch path는 blocking GS mapping이다.
- `parallel=true`일 때만 pending GS queue size가 설정되고 full queue의 oldest mapping packet을
  버리는 경로가 활성화된다.

### 3.2 Runtime acceleration

**[PAPER]** 보충 §10(PDF 19쪽):

- DROID-SLAM/HI-SLAM2 기반 Python loop 병목을 최적화했다.
- neural inference에 TensorRT를 사용했다.
- IMU preintegration을 C++로 구현했다.
- Jacobian/Hessian 계산에 custom CUDA kernel을 사용했다.
- Table 9 hardware는 i7-14700K + RTX 5090이다.

**[PUBLIC CODE]** 공개 README는 TensorRT와 C++ IMU module을 optional로 제공하고, artifact가
없으면 자동으로 PyTorch/Python fallback한다. TensorRT engine은 GPU-specific이며 공개 README
기준 RTX 5090에서 TensorRT 10.13.0.35, CUDA 12.8, FP16 dynamic profile을 사용한다.

따라서 실행 manifest에 engine hash/shape profile을 남기지 않으면 같은 commit과 command라도
실제 실행 backend가 달라질 수 있다. 또한 논문은 Table 18/19 rendering run 각각의 TRT engine
상태를 명시적으로 고정하지 않는다. Table 9 runtime 구현에는 TensorRT 사용이 명시돼 있다.

### 3.3 Finalization

**[PAPER]** 기본 rendering metric은 final global BA와 final color refinement 이전이다.

**[PUBLIC CODE]** 공개 `VIGS.terminate()`는 다음을 연속 수행한다.

1. backend 7/12 global optimization
2. background GS queue drain
3. `final=True` GS mapping call
4. `gs.finalize()`의 global color refinement
5. full trajectory filling과 rendering evaluation

반면 `demo.py --pure_online`은 final BA와 trajectory filler를 건너뛰지만, 공개 경로만으로는
pre-final full-trajectory rendering metric을 자동 생성하지 않는다. 이것이 reproduction에서
별도 metric-only adapter가 필요했던 이유다.

---

## 4. 논문 baseline들이 동일 조건이 아니었던 방식

### 4.1 결과 출처 자체가 다르다

**[PAPER]** 본문 §4, Baselines(PDF 8-10쪽):

| Baseline | 논문 수치 출처/처리 | 동일 실행 계약 여부 |
|---|---|---|
| SVO, TartanVO, DSO, MSCKF, OKVIS, VINS-Mono, ORB-SLAM3의 EuRoC | ORB-SLAM3 논문에서 전사 | 동일 hardware/runtime/seed 재실행 아님 |
| DROID-SLAM의 EuRoC | DROID-SLAM 논문에서 전사 | 동일 실행 아님 |
| Splat-SLAM, HI-SLAM2 및 그 밖의 재현 대상 | official code로 저자 재현 | pre-final online 상태는 맞추지만 strict timestamp 계약은 없음 |
| MM3DGS-SLAM pure visual-inertial | 공개 구현이 불완전하여 UTMM tracking을 원 논문에서 전사 | rendering은 평가 view 계약이 달라 직접 비교 불가 |
| DBA-Fusion, VINGS-Mono | VINGS-Mono 제1저자와 협의해 수정 후 실행 | 원본 default 그대로가 아님 |

따라서 VIGS 논문은 모든 baseline을 하나의 strict live harness 안에 넣은 system benchmark가
아니다. 가능한 방법은 재현하고, 일부는 논문값을 가져오고, 실패를 줄이기 위해 일부 baseline은
명시적으로 수정한 복합 비교다.

### 4.2 DBA-Fusion에 적용한 수정

**[PAPER]** 보충 §8.1(PDF 17쪽):

- EuRoC 초반 정지/저동작 구간에서 vision-only keyframe selection 때문에 IMU
  preintegration 구간이 길어지고 drift가 커지는 문제를 관찰했다.
- motion filter가 trigger하지 않아도 **최소 20 frame마다 keyframe을 강제**했다.
- UTMM 일부 sequence에서 default threshold로는 끝까지 IMU initialization이 안 되는 문제를
  해결하기 위해 해당 sequence의 **IMU initialization threshold를 0.15로 낮췄다**.

이는 baseline을 약하게 만든 수정이 아니라 초기화/안정성을 개선하기 위한 수정이다. 하지만
VIGS와 완전히 같은 keyframe/IMU-init rule을 강제한 것도 아니다. 각 baseline에 맞춘
dataset-specific stabilization이다.

### 4.3 VINGS-Mono에 적용한 수정

**[PAPER]** 보충 §8.2(PDF 18쪽):

- EuRoC/UTMM에는 DBA-Fusion과 같은 keyframe·IMU-init 수정을 적용했다.
- metric depth model이 평가 dataset에 잘 일반화되지 않는다고 판단해 monocular metric depth를
  모든 실험에서 껐다.
- loop closure의 false positive/부정확한 relative pose 문제 때문에 loop closure도 모든
  실험에서 껐다.

즉 VINGS-Mono 수치는 공개 default가 아니라 저자 협의로 안정화한 variant다. 우리 논문에서
다른 GS-SLAM baseline을 넣을 때도 crash/failure를 방치하는 대신, 논문/공식 권장 dataset
adapter를 적용하되 변경점을 표에 모두 공개하는 방식이 선례에 맞다.

### 4.4 Refinement와 평균 계산의 비대칭

- DROID-SLAM/Splat-SLAM/HI-SLAM2/VIGS의 online 비교는 final BA/refinement 전 상태를
  사용한다고 명시한다.
- VINGS-Mono는 final color refinement 자체가 없다.
- RPNG에서 HI-SLAM2가 table_05에 실패하므로 Table 3의 HI-SLAM2 평균은 나머지 sequence만
  사용한다.
- 논문에서 전사한 tracking baseline은 동일 machine에서 runtime을 다시 재지 않았다.
- 같은-machine runtime Table 9는 RPNG의 ORB-SLAM3, HI-SLAM2, VIGS 중심이며, ORB-SLAM3에는
  GS mapping FPS가 없다.

따라서 우리 논문에서는 실패 sequence를 조용히 평균에서 제외하지 말고 `F`, 성공률,
유효 scene 수를 함께 보고해야 한다.

---

## 5. 공개 VIGS artifact와 논문 사이의 재현 장애물

### 5.1 공개 commit 상태

**[PUBLIC CODE]** 현재 고정한 commit은
`22ffe24c6df81d0bf63bd20057565c00c51d2996`이다. Git history는 초기 commit,
대규모 code import, README 수정의 3개 commit뿐이라 paper-state 이전 commit을 선택할 수 없다.
공개 README도 대규모 refactor/cleanup/optimization, 환경, GPU에 따라 논문값과 달라질 수 있다고
명시한다.

### 5.2 UTMM 공식 runner가 mapping을 켜지 않는다

**[PUBLIC CODE]** `eval_utmm_mono.py:14`는 `gsmapping=False`다. 이 상태의 공식 batch
command는 `--gsmapping`을 붙이지 않으므로 Table 19 rendering map을 만들 수 없다.
우리 reproduction은 Table 19 진단을 위해 이 한 항목을 명시적으로 `True`에 해당하도록 실행했다.

### 5.3 논문 split을 만들 UID가 없다

논문의 all-method non-keyframe union이 공개되지 않았고, 공개 evaluator는 오히려 VIGS
keyframe을 포함한다. 정확한 paper PSNR split은 소스만으로 복구 불가능하다.

### 5.4 공개 종료 경로가 paper pre-final 설명과 맞지 않는다

공개 `terminate()`는 final BA와 color refinement를 수행한 뒤 평가한다. paper 기본 표는
둘 다 수행하기 전이라고 설명한다. 따라서 pre-final map을 저장·평가하려면 `terminate()` 전에
상태를 포착하는 외부 driver가 필요하다.

---

## 6. 이 프로젝트에서 vanilla를 재현하며 추가한 변경

이 절의 변경은 논문 저자의 baseline 수정과 구분한다. 모두 **우리의 reproduction/streaming
adapter 변경**이다.

### 6.1 RTX 5090 paper-native reproduction

관련 카드: [exp78 A](../5090branch/exp78/a_paper_reproduction/README.md),
[all-16 결과](../5090branch/exp78/a_paper_reproduction/vigs_all16_pytorch_reproduction.md)

| 항목 | 처리 |
|---|---|
| official source | `22ffe24c`, tracking/mapping module 자체는 수정하지 않음 |
| 종료 | `VIGS.terminate()` 전에 map/trajectory를 저장해 final BA/color refinement 제거 |
| full trajectory | 마지막 입력 뒤 metric pose 생성용 `PoseTrajectoryFiller`만 실행; map optimizer update 없음 |
| seed | Python/NumPy/PyTorch/CUDA seed 0 명시 |
| primary inference | PyTorch, top-level TRT engine이 있으면 runner가 거부 |
| TRT probe | README dynamic FP16 engine을 별도 runtime root에 구축하고 대표 4개 sequence만 비교 |
| UTMM | 공개 runner와 달리 mapping을 명시적으로 켬 |
| metric | official-public, self-non-KF, fixed-manifest post-hoc를 분리 |

결과:

- RPNG valid 8-scene PSNR `22.585dB`, paper `22.21dB`: +0.375dB로 qualified pass.
- UTMM PSNR `19.373dB`, paper `20.87dB`: -1.497dB로 미재현.
- TensorRT probe의 valid PyTorch 대비 PSNR 변화는 최대 0.061dB라 UTMM gap의 원인이 아니다.
- RPNG table_08 PyTorch seed0는 frame 7930 이후 trajectory가 붕괴했고 seed1 retry와 TRT seed0는
  정상 완료했다. 실패와 retry를 모두 보존했다.

이 arm은 **논문 pre-final 품질 재현용 causal/unbounded 실행**이지 1× strict streaming이 아니다.

### 6.2 RTX 5070 Ti synchronous/unbounded

관련 카드: [synchronous/unbounded](synchronous_unbounded/README.md)

- official commit `22ffe24c`, `--gsmapping --pure_online`.
- TensorRT engine 없이 PyTorch fallback.
- final BA와 color refinement 없음.
- 5070 Ti 빌드용 `<cstdint>` include 1줄, optimizer를 건드리지 않는 종료 후 rendering
  instrumentation, per-view index/keyframe 기록만 추가.
- dataset timestamp로 sleep하지 않으며 각 keyframe mapping 호출을 끝까지 기다린다.
- seed는 실제로 고정되지 않았다. 과거 output suffix의 `seed0`은 잘못된 label이다.

결과는 RPNG 22.4707dB, UTMM 19.2125dB다. 이는 품질 reference이지 runtime-constrained
baseline이 아니다.

### 6.3 RTX 5070 Ti 1.5× paced + drain

관련 카드: [1.5× paced streaming](5070ti_1.5x_streaming/README.md)

- 외부 producer가 source timestamp 간격을 1.5배로 늘려 frame을 방출한다.
- ingress queue가 차면 producer가 기다려 RGB frame은 모두 보존한다.
- `Training.parallel=true`, GS pending queue size 2를 켠다.
- GS queue가 차면 공개 parallel path처럼 oldest **mapping packet**을 버린다.
- 마지막 입력 뒤 이미 제출된 GS packet을 drain한다.
- lifecycle reset lock, producer tensor lifetime, worker exception propagation만 보완했다.
- final BA/color refinement는 없다.

결과는 synchronous 대비 전체 평균 -0.0687dB로 품질이 거의 같다. 그러나 16/16에서
tracking이 1.5× deadline보다 늦었고, 평균/최대 tracking lateness는 252.43/974.05초다.
mapper drain도 평균/최대 1.321/5.456초다. 따라서 이 arm은 **모든 입력을 보존한
paced-quality baseline**이지 strict 1.5× 성공이 아니다.

### 6.4 RTX 5070 Ti 1.5× hard-deadline/drop-oldest

관련 카드: [1.5× strict](5070ti_1.5x_strict/README.md),
[결과표](5070ti_1.5x_strict/summary.md)

- decode를 앞서 수행하고 1.5× source timestamp에 맞춰 방출한다.
- ingress queue가 차면 adapter가 oldest RGB frame을 버린다.
- fixed final-capture deadline 뒤 Adam, birth, densify/prune, opacity reset, rescale을 막는다.
- deadline 뒤 pending GS packet을 폐기하고 optimizer drain을 하지 않는다.
- 실제 완료된 `torch.optim.Adam.step()`을 센다.

현재 평가 완료 16개에서 입력 39,090장 중 11,828장만 처리하고 27,262장을 버렸다.
가중 처리율은 30.26%다. mapping zero-tail은 16개에서 성립했지만 end-to-end strict pass는
0/20이다.

이 arm은 **live drop stress diagnostic**으로는 의미가 있지만 다음 이유로 gsSLAM 품질의
유일한 vanilla baseline으로 쓰면 안 된다.

- drop이 VIGS algorithm의 선택이 아니라 harness ingress adapter의 선택이다.
- 두 방법이 서로 다른 RGB subset을 볼 수 있다.
- 낮은 PSNR이 mapper 차이인지 69.74% input loss 때문인지 분리되지 않는다.
- tracking deadline이 모든 완료 run에서 실패했다.

---

## 7. 실시간성이 핵심인 우리 논문의 비교 구조

### 7.1 본문 핵심 실험은 B와 C 두 축으로 충분하다

| 핵심 실험 | 답하는 질문 | 권장 조건 | delta의 기준 |
|---|---|---|---|
| **B. Mapping-only isolation** | 동일 online state와 계산 기회에서 gsSLAM mapper 자체가 더 좋은가? | causal frozen tracker packet, fixed held-out, 동일 mapping iteration 및 시간 계측 | local vanilla mapper vs gsSLAM mapper |
| **C. End-to-end live system** | 센서가 계속 들어올 때 deadline 안에서도 그 품질 향상이 유지되는가? | native timestamp producer, tracking+mapping 동시, zero-tail | 각 시스템의 strict pass·품질·drop·skip·lag |

B는 방법론의 mapping 기여를 분리하고, C는 그 개선이 실제 system deadline 안에서도
유효함을 검증한다. 이 두 결과가 각각 **품질 향상의 원인**과 **실시간성**을 담당하므로
논문 본문의 핵심 비교로 충분하다.

기존의 paper reproduction은 별도 핵심 축으로 승격하지 않는다. 공개 vanilla 환경이 정상인지
확인하는 sanity check로 implementation detail이나 appendix에 간단히 남긴다. unbounded quality
upper bound도 필수가 아니며, strict 품질 하락의 원인을 설명해야 할 때만 선택적 ablation으로
추가한다. paper PSNR은 B/C의 직접 delta 기준으로 사용하지 않는다.

### 7.2 B — Mapping-only isolation 계약

현재 [5090 exp78 Lane B](../5090branch/exp78/b_strict_fair_comparison/README.md)가 가장
가까운 구조다.

- official VIGS tracker packet을 한 번만 causal하게 생성하고 immutable archive로 고정
- 동일 packet timestamp, RGB preprocessing, pose, depth, calibration을 양 mapper에 전달
- fixed held-out UID는 archive 생성 전 고정하고 mapping supervision/birth에서 제외
- frozen packet이 미래 frame/미래 keyframe 정보를 포함하지 않는지 hash/causality audit
- VIGS paper-like 비교에서는 양쪽의 새 keyframe당 mapping iteration 수를 동일하게 고정
- iteration 수만 같아도 실제 비용은 다를 수 있으므로 wall-clock, GPU time, Adam step,
  rasterized view-update, unique supervision view, Gaussian 수, peak VRAM을 함께 보고
- 동일 iteration 결과와 동일 mapping deadline 결과를 구분해 기록
- final BA, color refinement, terminal replay는 양쪽 모두 0

고정 iteration 비교는 “gsSLAM이 단순히 update를 더 많이 받아 좋아졌다”는 반론을 막는다.
하지만 방법마다 iteration당 rasterization·densification 비용이 다르므로 이것만으로 실시간성을
증명하지 않는다. 동일 deadline 계측은 이 계산비 차이를 드러내는 보조 축이며, 최종 실시간
판정은 C가 담당한다.

### 7.3 C — End-to-end에서 frame drop을 어떻게 다룰지

실제 센서는 consumer가 늦다고 멈춰주지 않으므로 drop/skip 자체를 무조건 금지하는 것도
현실적이지 않다. 대신 다음을 구분해야 한다.

1. **Harness drop 금지:** 비교 wrapper가 임의로 oldest RGB를 버려 특정 방법을 deadline에
   맞추지 않는다.
2. **Method-owned skip 허용:** 방법이 명시적인 causal policy로 frame/KF를 선택하거나 skip하는
   것은 시스템 설계로 인정한다.
3. 모든 방법에 동일 sensor stream을 방출하고 `emitted / decoded / tracked / mapped / dropped /
   skipped`를 각각 기록한다.
4. dropped/skipped frame도 전체 sequence의 tracking Recall과 fixed held-out rendering 품질에
   간접적으로 책임을 진다.
5. queue가 늦어 deadline을 넘기면 backlog를 끝까지 처리해 diagnostic map을 만들 수는 있지만,
   strict 결과는 FAIL이며 deadline 이후 map을 성공 PSNR로 승격하지 않는다.

이 정의라면 frame drop은 숨겨진 편의가 아니라 정확도와 맞바꾸는 공개된 시스템 행동이 된다.

현재 논문의 범위를 localization까지 포함한 완전한 SLAM으로 잡으면 C는 각 방법의 tracker와
mapper를 함께 실행하고 decode+tracking+mapping 시간을 모두 포함해야 한다. 반대로 현재 단계처럼
mapping만 논문의 기여로 한정하면, 공통 causal online tracker service의 packet을 native timestamp로
공급할 수 있다. 이때 주장은 **“online tracking state가 주어졌을 때의 real-time incremental
3DGS mapping”**으로 제한하며 full end-to-end SLAM이라고 부르지 않는다.

### 7.4 1.0×와 1.5×의 논문 내 위치

- **1.0×:** source timestamp 그대로의 native-rate. “real-time”을 문자 그대로 주장하려면 최종
  system table의 primary gate가 되어야 한다.
- **1.5×:** sequence duration의 1.5배 안에 끝내는 bounded-streaming/near-real-time gate.
  현재 프로젝트의 재현 가능한 운영 milestone이며 알고리즘 개발 표의 primary budget으로
  유지할 수 있다.
- **unbounded:** 필수 본문 결과가 아니다. paper sanity check나 strict 실패 원인 분석이 필요할
  때만 appendix/ablation에서 사용한다.

우리 논문이 1.5×만 통과한다면 표현은 “strict real-time”보다 **“bounded streaming within
1.5× capture duration”**이 정확하다. 최종 real-time claim을 유지하려면 1.0× 결과를 별도
primary 또는 적어도 명시적 stress gate로 추가해야 한다.

B와 C 모두 동일 GPU와 명시적으로 고정한 TensorRT engine/hash/profile을 사용한다. B의
mapping-only 개선은 scheduling/mapping 기여의 인과성을 보여주지만 C의 real-time 통과를
대신하지 않으며, C의 통과만으로 mapper 자체의 품질 향상을 주장하지도 않는다.

---

## 8. 아직 결정해야 할 항목

아래를 결정한 뒤 versioned protocol manifest로 고정해야 한다.

| 결정 | 선택지 | 현재 권고 |
|---|---|---|
| 최종 real-time primary | 1.0× / 1.5× | **1.0× system primary, 1.5× development/secondary** |
| sensor ingress | backpressure / harness drop / uninterrupted emit | **uninterrupted emit, harness drop 금지** |
| method frame skip | 금지 / 허용 | **허용하되 policy와 모든 count 공개** |
| EOS | drain / immediate cutoff | **B/C strict 표는 immediate cutoff; drain은 필요할 때만 진단** |
| runtime 범위 | mapping only / end-to-end | **B는 mapper만, C는 claim 범위의 전체 경로** |
| vanilla baseline | paper number / local official | **B/C delta는 local official; paper number는 appendix sanity check만** |
| held-out | method별 non-KF / shared post-hoc / predeclared fixed | **predeclared fixed mapping-disjoint** |
| tracker | 각 방법 자체 / frozen common | **B는 frozen common; C는 논문 claim 범위에 따라 명시** |
| TRT | optional autodetect / explicit matched | **explicit matched engine/hash/profile** |
| failure 평균 | 성공 run만 평균 / 실패 포함 별도 | **성공률·F를 함께 보고 평균의 분모 명시** |
| seed | 1회 / 반복 | **전체 scene seed0 + 대표 dev/validation 최소 3 seeds; 가능하면 전부 3 seeds** |

---

## 9. 현재 evidence가 허용하는 주장과 금지하는 주장

### 허용

- 공개 VIGS pre-final RPNG는 RTX 5090 PyTorch arm에서 논문 평균 PSNR의 0.375dB 안으로
  qualified reproduction됐다.
- 공개 VIGS UTMM은 같은 방식에서 논문 평균보다 1.497dB 낮으며 정확한 paper state/split은
  공개 artifact로 복구되지 않는다.
- VIGS 논문의 rendering 평가는 final refinement 이전 online map을 대상으로 한다.
- 논문 저자도 baseline마다 source, stabilization, refinement 가능 여부가 다른 조건을
  투명하게 공개했다.
- 공개 VIGS는 5070 Ti에서 모든 frame을 보존하면 1.5× deadline을 넘겨도 synchronous와 거의
  같은 품질을 유지한다.

### 금지

- “VIGS 논문 22.21/20.87dB는 strict 1× streaming 결과다.”
- “우리 1.5× strict 결과가 논문의 동일 시간 계약에서 VIGS를 이겼다.”
- “5070 Ti strict vanilla는 모든 입력을 받은 공정 baseline이다.”
- “UTMM vanilla 논문값을 공식 코드로 복원했다.”
- “paper Table 18/19와 우리 fixed stride-5 held-out이 동일 split이다.”
- “VIGS 논문의 모든 baseline이 동일 hardware·code·seed·postprocessing으로 실행됐다.”

---

## 10. 다음 대화에서 잠글 최소 계약 초안

실시간성이 논문의 중심이라면 최소한 다음 문장을 실험 전에 고정해야 한다.

> 모든 방법은 동일한 timestamp 순 RGB+IMU sensor stream을 받는다. Harness는 frame을
> 삭제하거나 producer를 consumer 속도에 맞춰 멈추지 않는다. 방법 자체의 causal frame
> selection은 허용하되 emit/decode/track/map/skip/drop 수를 모두 보고한다. B에서는 동일한
> causal frozen tracker packet과 mapping iteration을 사용하고 실제 GPU time과 view-update도
> 함께 보고한다. C의 primary real-time 결과는 native 1.0× capture duration 안의 상태이며,
> 그 시점 이후 optimizer와 topology update는 0회다. 현재 1.5× 결과는 bounded-streaming
> milestone으로 별도 표기한다. Rendering 평가는 사전 고정한 mapping-disjoint UID에서
> 수행하고, metric 계산 자체의 시간은 runtime에서 제외하되 map/pose를 변경하는 후처리는
> 금지한다. Paper reproduction과 unbounded upper bound는 본문 핵심 비교가 아니라 각각
> appendix sanity check와 선택적 진단으로만 사용한다.

이 문장은 최종 결정 전 초안이다. 특히 1.0×를 당장 primary로 실행할지, 현재 1.5× milestone을
먼저 완성한 뒤 1.0×를 최종 gate로 둘지는 사용자 결정이 필요하다.
