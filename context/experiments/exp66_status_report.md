# exp66 실행 현황 보고 (읽기 쉬운 버전)

> [exp66 메인 계획 카드](exp66_gsslam_optimizer_survey_plan.md)와 별도로, 지금까지
> 뭘 했고 결과가 뭘 뜻하는지만 빠르게 파악하기 위한 문서. 매 축 완료 시 갱신.
>
> 마지막 갱신: 2026-08-22

## 축 진행 상황

```
축 1  LM-RS(2차 최적화, vanilla Adam 대비 실측)          ✅ 완료 — 강한 긍정 신호 + 원인 특정된 치명적 발산, 실사용 불가
축 2  CaRtGS(공식 Replica 벤치마크 재현)                  ✅ 완료 — 재현 불가(환경 문제, 판정 보류)
축 3  Taming-3DGS(budget-constrained densification)      ✅ 완료 — PSNR은 근소 열세, Gaussian 수는 7배 절감
축 4  LM-RS → VIGS-SLAM backpolish 통합(스케줄링)         ✅ 완료 — NO-GO(batch/CG 축소하면 발산 악화)
축 5  LM-RS → VIGS-SLAM 실제 이식(dual-rasterizer)        🔶 부분 완료 — rasterizer 이식 검증 성공, CG solve 로직 이식은 미착수
```

## 실험 환경 (세 축 공통/차이 정리)

- **scene**: `gs_floaterLab/data/03_rgb_3dgs_full` — Aria 원본 캡처 `0416_301-1253`("1253호")에서
  파생, 1303장 RGB(OpenMAVIS pose 보간 + ORB map points init), COLMAP 포맷. 세 축 전부 이
  scene 하나만 사용, 원본은 읽기 전용으로만 참조(수정 없음).
- **train/test split**: 세 축 공통 — COLMAP `--eval` 표준 방식, `image_name` 정렬 후
  `idx % 8 == 0`을 test(163장), 나머지 1140장을 train.
- **GPU**: RTX 5070 Ti 1장, compute capability sm_120(Blackwell, 2025년 출시), VRAM 16303MiB.
  이 GPU 세대가 세 축 전부에서 핵심 변수였음 — 각 저장소가 원래 고정한 구버전 PyTorch/CUDA
  조합이 sm_120 커널을 아예 안 가지고 있어서, 축마다 새로 맞는 조합을 찾아야 했음.

| 축 | conda env | Python | PyTorch | CUDA | 비고 |
|---|---|---|---|---|---|
| LM-RS | `lm-rs-exp66`(13GB) | 3.9 | 2.7.1+cu128 | nvcc 12.8, `TORCH_CUDA_ARCH_LIST=12.0` | 저자 권장은 PyTorch 1.13+CUDA 11.7(이 GPU에서 불가) |
| CaRtGS | `cartgs-env`(빌드실패로 삭제) | 3.10.12 | 2.3.1+cu121(저자 고정) | nvcc 12.8 격리 시도했지만 libtorch 링크 실패 | sm_120 근본 비호환으로 빌드 자체가 안 됨 |
| Taming-3DGS | `taming3dgs-exp66`(6.7GB) | 3.9 | 2.7.1+cu128 | nvcc 12.8, `TORCH_CUDA_ARCH_LIST=12.0` | LM-RS와 동일 조합으로 바로 성공 |

디스크: 세 축 다 거친 지금 루트 파티션 여유 26GB(시작 시 47GB) — CaRtGS의 실패한 빌드 환경
(8.6GB)은 축 종료 후 정리함. LM-RS/Taming-3DGS의 conda env는 후속 검증 가능성 때문에 보존 중.

## 축 1: LM-RS — 1차 결과 (세션 전체에서 첫 긍정 신호)

같은 `03_rgb_3dgs_full` scene, 같은 저장소(lm-rs) 안에서 vanilla Adam 경로와
LM-RS의 matrix-free CG optimizer 경로를 비교.

| iter | vanilla Adam | LM-RS |
|---:|---:|---:|
| 500  | 21.43 | **27.13** |
| 1000 | 22.70 | **27.53** |
| 2000 | 23.70 | **27.68** |
| 3000 | 24.38 | **27.61** |
| 4000 | 24.78 | **27.69** |
| 5000 | 25.19 | **27.75** |
| 6000 | 25.25 | 9.77 (붕괴) |
| 7000 | 25.65 | 9.77 (붕괴) |

wall-clock: vanilla 88.48s(7000 iter 전체) vs LM-RS 610.87s(7000 iter 전체, iter당
샘플 수가 16~32배 많아 단순 iter 비교는 불공정). **wall-clock 매칭 비교**: LM-RS
iter 1000(누적 84.3s)=27.53dB vs vanilla 7000 iter(88.48s)=25.65dB — **같은
wall-clock 예산에서도 LM-RS가 +1.9dB 우위**. 이 세션에서 처음으로 나온, 노이즈
폭(±0.24~0.33dB)을 확실히 넘는 순이득.

### 치명적 문제: iter 5500~6000 사이 발산

`run.log` 직접 대조 확인: iter 5500(27.41dB, LR=0.2 정상) → iter 6000(9.77dB로
붕괴, 이후 로그에 `Learning Rate is nan` 지속). 코드 원인을 코드 레벨로 특정함
(`scene/optim_strategy/cgOptimizer.py` step(), 약 118~121줄):
```python
color_update = torch.abs(self.solution[slices[1]])
lr = 1 / color_update.max()          # 가드 없음 — color_update.max()가 0에 가까우면 inf/nan
lr = torch.minimum(max_lr, lr)
```
`color_update.max()`가 0 근처로 붕괴하면 `lr`이 inf/nan이 되고, nan 가드 없이
`param_list[i] += p * lr`로 모든 Gaussian 파라미터에 그대로 곱해져 전체가 깨짐.
저자 논문 코드 자체의 결함으로 보이며, 우리가 강제로 쓴 비권장 툴체인
(CUDA 12.8+PyTorch 2.7.1, 이 GPU가 sm_120/Blackwell이라 저자 권장 CUDA 11.8/
PyTorch 1.13이 애초에 안 돌아감 — 위 §축 2 CaRtGS와 같은 GPU 세대 문제)의
영향인지는 아직 완전히 배제 못함.

### 가드 추가 검증(1회) — 가설 기각, 원인은 더 깊음

`lr` 스칼라에 nan/0-division 가드(`torch.isfinite` 체크 + `nan_to_num`)를 추가해서
동일 커맨드로 재실행. **결과: 붕괴가 그대로 재현됨** — 오히려 더 일찍(iter
2000~3000 사이) 무너짐. 로그 확인: `optim_iter=2430`부터 매 스텝 가드가 발동했는데,
발동 시점에 `denom`(=`color_update.max()`)이 이미 `nan`이었고, `lr` 스칼라 자체는
가드 덕에 끝까지 finite(`max_lr`)로 유지됐는데도 파라미터는 계속 깨짐(`p`, 즉 CG
solve의 해 자체가 이미 non-finite라서 `lr`을 아무리 방어해도 `param += p * lr`에서
nan이 전파됨). **즉 진짜 원인은 `lr` 계산이 아니라 그 앞 단계, CG 선형 solve
자체가 non-finite 해를 내놓는 것 — 훨씬 깊은 문제.** 한 줄짜리 가드로 고쳐지는
버그가 아님. codex는 지시대로 추가 튜닝·재시도 없이 여기서 정직하게 보고를 멈춤.

흥미로운 점: 두 번의 "동일 커맨드" 실행에서 붕괴 시점이 달랐음(1차 iter
5500~6000, 가드판 iter 2000~2500) — 완전한 결정론이 아니라는 뜻이라 이 수치
자체도 불안정성의 방증.

### 판정

**"채택"도 "기각"도 아님 — 원리 검증은 성공, 실사용은 아직 불가.** 같은 저장소·
같은 scene 안에서 wall-clock까지 매칭해도 LM-RS가 노이즈 폭을 확실히 넘는 이득을
내는 건 실측으로 확인됨(이 세션 최초의 진짜 순이득). 그러나 CG solve 자체가
비결정적으로 non-finite에 빠지는 깊은 수치 안정성 문제가 있고, 이게 (a) 이 scene
Hessian 조건 자체의 취약성인지 (b) 저자 비권장 CUDA 12.8/PyTorch 2.7.1 툴체인
때문인지 구분이 안 됨(이 GPU에서는 저자 권장 스택 자체를 못 돌림). 채택하려면
CG solver 내부에 residual/nan 체크를 넣는 수준의 추가 엔지니어링이 필요 — 다음
단계 진행 여부는 사용자 판단 필요.

## 축 2: CaRtGS — 결과

**재현 불가.** 논문/코드 문제가 아니라 **이 머신의 GPU 세대와 CaRtGS가 고정한
PyTorch 버전이 근본적으로 안 맞음.**

- 이 머신 GPU: RTX 5070 Ti, compute capability **sm_120**(Blackwell, 2025년 출시)
- CaRtGS 요구: PyTorch 2.3.1 + CUDA 12.1(README에 고정) — 이 조합은 **sm_50~sm_90만
  지원**, sm_120 커널이 아예 없음
- 직접 검증: `torch.ones(1, device="cuda")` 같은 가장 기본적인 텐서 생성조차
  `RuntimeError: CUDA error: no kernel image is available for execution on the
  device`로 실패(`exp66_axes/cartgs/env_gpu_check.log`, 직접 확인함)
- 빌드도 2회 시도 — 1차는 CUDA toolkit(`nvcc`) 자체가 없어서 실패, 2차는 CUDA 12.8로
  isolate했지만 CaRtGS의 CMake가 libtorch 2.3.1과 nvToolsExt 링크에서 실패
- 헤드리스 렌더링은 문제 아니었음 — `DISPLAY=:1`에 실제 X 서버가 떠 있고, 코드에
  `no_viewer` 옵션도 있어 뷰어 없이 평가 가능함을 확인
- Replica 데이터셋은 다운로드하지 않음(전체 zip 12.4GB, 디스크 47GB 여유 중 안전하게
  건너뜀 — 빌드가 이미 불가능했으므로)
- 참고용 논문 수치만 확보: room0 RGB-D(Photo-SLAM backend) **29.38 ± 3.70dB**
  (재현치 아님, 논문 Table I 값)

### 판정

**"기각"이 아니라 "이 GPU/툴체인 조합에서는 검증 불가".** CaRtGS를 이 머신에서
쓰려면 PyTorch를 Blackwell 지원 버전(2.4+/nightly, cu124 이상)으로 올리고 CMake
빌드도 그에 맞게 다시 맞춰야 하는데, 이건 논문 자체의 가치 판단과 무관한 순수
인프라 작업이라 이번 축에서는 여기서 멈춤. splat-centric backward parallelism
기법 이식 평가는 재현 성공을 전제로 했으므로 미수행.

## 축 3: Taming-3DGS — PSNR은 근소 열세, 대신 Gaussian 7배 절감

CaRtGS README가 "fast splat-wise backpropagation"(3배 iteration 증가) 출처로 명시
인용한 저장소. vanilla 3DGS의 단독 fork라 LM-RS와 완전히 같은 방법론(같은 저장소
안에서 vanilla 경로 vs Taming 경로, 같은 scene, 같은 split)으로 비교.

| iter | vanilla | Taming |
|---:|---:|---:|
| 500  | 21.36 | 21.36 |
| 1000 | 22.41 | **22.52**(+0.11, 유일하게 Taming 우세) |
| 2000 | **24.37** | 24.08 |
| 3000 | **25.72** | 25.30 |
| 5000 | **28.14** | 27.39 |
| 7000 | **29.04** | 28.45 |

같은 wall-clock(약 96초, 두 run 다 iter7000 평가 시점) 기준으로도 결과는 동일 —
**Taming이 vanilla를 이기지 못함**(LM-RS와 다른 결과). 순수 연산시간(forward+backward
누적)은 Taming이 iter7000에서 10.66초 적게 씀(vanilla 37.63s vs Taming 26.97s,
~28% 절감)에도 최종 PSNR은 -0.59dB 낮음.

**단, 진짜 주목할 결과는 Gaussian 개수**: vanilla는 727,213개, Taming은 102,428개
— **약 7.1배 적은 Gaussian으로 -0.59dB 손해만 봄.** 이게 이 축의 핵심 가치다 —
`budget=20, mode=multiplier`처럼 명시적으로 목표 개수를 지정하는 score-based
densification이 실제로 통제 가능한 예산으로 동작함을 우리 scene에서 직접 확인.

방법론 참고: 이 저장소에서는 "빠른 backward" 커널을 끄는 옵션이 없음(Taming 알고리즘
병합 이전 커밋 자체가 이미 고속 rasterizer라서 vanilla 조건도 같은 커널을 씀) —
그래서 이번 비교는 "backward parallelism의 속도 효과"가 아니라 순수하게
**densification 전략(budget-constrained vs 표준 split/clone+opacity pruning)의
차이만** 격리해서 본 것.

### 판정

**PSNR 경쟁에서는 vanilla 승, 그러나 "예측 가능한 Gaussian 예산" 메커니즘은 실증됨.**
LM-RS처럼 "더 빠르게 더 높은 PSNR"을 주는 축은 아니지만, "CaRtGS가 Taming의 budget
메커니즘을 썼는가"라는 질문의 답은 **"아니오"**였음(CaRtGS는 Taming에서 속도 기법만
빌리고, Gaussian 개수 관리는 opacity regularization이라는 더 약하고 비예측적인
별도 방식을 씀 — [CaRtGS 논문](https://arxiv.org/abs/2410.00486) VI절/Weak-constrained
Densification 직접 확인). Taming의 진짜 budget 메커니즘 자체는 이번 실측으로 "우리
scene에서도 실제로 동작하고, 7배 압축에 -0.59dB면 real-time incremental mapping의
예측 가능한 예산 설계에 쓸 만하다"는 근거가 생김 — 다만 Taming은 **오프라인/정적
학습 전체에 대해 목표 개수 하나를 고정**하는 설계라, keyframe이 계속 들어오는 온라인
세팅에 맞추려면 "롤링 예산 재분배" 같은 진짜 변형 설계가 필요(단순 이식 불가).

## 축 4: LM-RS를 VIGS-SLAM backpolish에 통합 — NO-GO

사용자 제안: map()은 기존 optimizer 유지, backpolish만 LM-RS로 교체. 조사 결과
backpolish는 map()과 **완전히 같은 단일 스레드**에서 협조적으로 도는 구조이고
(exp60 comment: PGBA 동시 CUDA 커널 실행이 실제 device-side-assert 크래시를
냈던 전례 때문에 `video.get_lock()`+`_gaussian_lock`을 공유하며 직렬화),
호출 하나가 view 1장·Adam 1 step·3.9~6.4ms인 아주 잘게 쪼개진 협조적 스케줄링
위에 세워져 있음(`vigs/gs_backend.py:1238` `background_polish_step`,
`vigs/vigs.py:320` `_gs_worker`). "진짜 병렬 스레드"(옵션 a)는 이 CUDA 동시성
크래시를 다시 불러올 위험이 커서 기각, 대신 "LM-RS를 아주 잘게 쪼개서 기존
협조적 스케줄링에 맞추기"(옵션 b) 방향으로 좁혀 실현 가능성부터 검증.

### 실험: batch/CG 축소 스윕

batch∈{1,2,4,8} × CG∈{1,2,4} 중 6개 조합(1/1, 2/1, 2/2, 4/2, 4/4, 8/4)을 같은
scene(`03_rgb_3dgs_full`, -r2/SH0)에서 vanilla Adam(iter당 4.96ms, iter7000
25.65dB)과 비교.

| 설정 | iter당 시간(ms) | 발산 시점 | iter500 vs vanilla(동일 wall-clock) |
|---|---:|---:|---:|
| batch1,cg1 | 1.87 | iter 3000 (nan) | +3.91dB(일시적) |
| batch2,cg1 | 3.14 | iter 2000 | +3.03dB(일시적) |
| batch2,cg2 | 3.67 | iter 1500 | +1.56dB(일시적) |
| batch4,cg2 | 6.32(vanilla와 가장 근접) | iter 1500 | +0.47dB |
| batch4,cg4 | 8.25 | iter 1000 | **-1.09dB(이미 열세)** |
| batch8,cg4 | 16.09 | iter 1500 | +0.24dB |

**6개 전부 발산했고**(batch1_cg1만 실제 NaN, 나머지는 3dB 이상 급락하는 동일한
붕괴 패턴), vanilla 수준 iter당 시간에 가장 가까운 batch4_cg2는 iter500부터
이득이 미미(+0.47dB)하다가 iter1000에 이미 역전(-1.67dB), iter1500에 완전
붕괴. `batch4_cg2/run.log` 직접 대조로 재확인 완료(iter500 21.98→iter1000
21.17→iter1500 16.37→iter2000 9.45dB, 이후 회복 없음).

### 판정

**NO-GO.** batch/CG를 backpolish가 요구하는 호출당 수 ms 수준까지 줄이면 LM-RS의
품질 이득이 사라질 뿐 아니라 **안정성까지 더 나빠진다**(원래 설정의 발산 시점은
iter 2430~5500이었는데, 축소판은 iter 1000~3000으로 오히려 더 일찍 무너짐 —
적은 표본/적은 CG 반복이 정규방정식을 더 badly-conditioned하게 만드는 것으로
추정). 이 방향(LM-RS를 backpolish의 기존 협조적 스케줄링 안에 끼워 넣기)은
근본적으로 성립하지 않음 — "더 잘게 쪼개면 언젠간 맞겠지"가 아니라 잘게 쪼갤수록
더 나빠지는 반비례 관계.

이후 사용자가 backpolish의 실제 latency 허용치를 "몇 초까지도 허용 가능"으로
명확히 하면서, 축 4의 전제(batch/CG를 ms 단위로 줄여야 한다)가 무효화되고 축 5로
이어짐 — 아래 참조.

## 축 5: LM-RS → VIGS-SLAM 실제 이식 시도 (dual-rasterizer) — 부분 완료

**배경**: 사용자가 "map()은 기존 optimizer, backpolish만 LM-RS로" 제안 → 조사
결과 진짜 병렬 스레드(옵션 a)는 exp60의 CUDA 동시성 크래시 재현 위험 때문에
기각, "LM-RS를 잘게 쪼개서 기존 협조적 스케줄링에 맞추기"(옵션 b, 축 4)로
좁혔으나 batch/CG 축소 스윕이 전부 발산 → NO-GO. 이후 사용자가 실제 latency
허용치("몇 초까지도 허용 가능")를 명확히 하면서 축소가 애초에 불필요했을 수
있다는 게 드러남 — `_gs_worker`의 기존 단일 호출 설계가 이미 "한 호출이 아무리
오래 걸려도 끝나면 큐를 재확인"하는 구조라, LM-RS의 검증된 원래 설정(batch
16~32, CG 5~8)을 그대로 한 호출 안에서 쓰는 것도 이미 가능했을 가능성.

이후 "복사만 하면 되나?" → "안 됨, VIGS-SLAM은 표준 rasterizer라 LM-RS의 CG
solve가 요구하는 픽셀별 Jacobian 정보를 애초에 노출 안 함(M2와 동일한 근본
원인)" → "교체 말고 이름 바꿔서 공존시키면?" 순서로 좁혀져, 실제로 시도.

작업 브랜치: VIGS-SLAM `exp66-lmrs-polish-preempt`(`exp65-backpolish-free`에서
분기). 아래 세 가지를 실제로 구현·검증함(전부 opt-in, 기본값 끄면 기존 동작과
100% 동일 — 회귀 없음을 smoke test로 확인).

### 5-1. burst 스케줄링 (`--background_polish_burst_budget_ms`)

`_gs_worker`의 idle 분기를 "폴리시 호출 1회 → 즉시 큐 재확인" 대신 "시간 예산
안에서 폴리시 호출을 몇 번이고 이어붙이고, 매 호출 뒤 큐/gate를 재확인"하는
구조로 확장(`vigs/vigs.py`). smoke test(aria1253, 600프레임, backpolish
켜진 recipe): control 27.76dB/1994회 호출 vs burst500(500ms 예산) 27.87dB/2098회
호출 — 회귀 없음.

**중요한 재발견**: 두 run의 폴리시 호출이 "연속 몇 번 이어지는지" 세어보니
**control(burst 꺼짐)도 이미 평균 90.6회, 최대 416회 연속**으로 이어짐(burst500은
95.4회/448회로 별 차이 없음) — 기존 `_gs_worker`가 poll 주기(0.2~2ms)로 이미
빠르게 재진입하는 구조라서, 유휴 시간이 길면 자연히 호출이 쭉 이어짐. 즉 **이
burst 코드 자체는 안전하게 동작하지만, "몇 초 허용" 전제에서는 애초에 필요
없었을 가능성이 높음** — 진짜 필요한 건 스케줄러가 아니라 optimizer 자체 교체.

### 5-2. Dual-rasterizer 빌드 (`thirdparty/diff-gaussian-rasterization-cg/`)

LM-RS의 `submodules/diff-gaussian-rasterization`를 복사해 패키지명을
`diff_gaussian_rasterization_cg`로 바꿔(원본은 VIGS-SLAM 자체 rasterizer와 이름이
똑같아서 충돌) VIGS-SLAM 자체 conda env(`vigs-slam-5090`)에서 빌드.

- VIGS-SLAM env는 이미 PyTorch 2.8.0+cu128로 이 GPU(sm_120)를 네이티브 지원 —
  LM-RS 때처럼 CUDA 버전 우회가 불필요.
- 빌드 중 실수 2건 발견·수정: CUDA_HOME PATH를 앞에 붙였다가 python3.9(다른 env
  것)가 잡혀서 잘못된 ABI로 컴파일됨(PATH 순서 수정으로 해결), `pip install -e .`가
  이 환경에서 editable install 등록에 실패(일반 `pip install .`로 해결).
- 검증: 같은 프로세스 안에서 `diff_gaussian_rasterization`(기존)과
  `diff_gaussian_rasterization_cg`(신규)를 동시 import해도 충돌 없음(별개의 `.so`,
  `same _C object? False`). 합성 Gaussian으로 실제 forward+backward 성공.
- **파라미터/카메라 컨벤션은 호환되지만 완전 동일하진 않음**: scaling(log)/
  opacity(sigmoid)/rotation(normalize), FoVx/FoVy/world_view_transform/
  full_proj_transform/camera_center는 동일. 단 VIGS-SLAM 자체 rasterizer는 카메라
  pose delta 정제(`theta`/`rho`)와 `projmatrix_raw`를 자체 확장으로 갖고 있는데
  LM-RS rasterizer엔 없음(대신 `isbatched`/`end_transmittance`/CG 전용 인자가
  있음) — "gaussian" scope(pose 정제 없음)에서는 문제 안 됨, "full" scope는 아직
  검증 안 함.

### 5-3. 라이브 세션 통합 검증 (`--background_polish_use_cg_rasterizer`)

`vigs/gaussian/renderer/__init__.py`에 `render_cg()` 추가(theta/rho/
projmatrix_raw/filter_mask 없는 최소 버전, optimizer는 그대로 Adam — rasterizer만
교체), `background_polish_step`에 opt-in 인자로 배선. aria1253 600프레임 실제
세션(control과 동일 recipe, `--background_polish_use_cg_rasterizer`만 추가)에서
**크래시 없이 완주**: PSNR 27.66dB, 폴리시 호출 2032회 — control(27.76dB/1994회),
burst500(27.87dB/2098회)과 노이즈 범위 안에서 동일.

**의미**: 실제 VIGS-SLAM 라이브 세션의 실제 Gaussian 데이터·실제 카메라 궤적이
LM-RS 유래 rasterizer를 통해 정상적으로 렌더된다는 것을 실측으로 확인. 단
optimizer는 여전히 Adam — "그릇이 맞는다"는 것만 검증됐고 "LM-RS가 실제로 더 잘
최적화한다"는 아직 전혀 검증 안 됨.

### 5-4. CG solve 로직 이식 — 착수 전, 규모만 확인

`cgOptimizer.py`는 독립적이지 않고 `CGSolverState`(`cgState.py`)에 강하게
결합됨 — `TILE_SIZE=256`/`BLOCK_DIM=16` 등 CUDA 커널 내부 타일링 관례에 정확히
맞아야 하는 차원들(`width_blocks`/`height_blocks`/`total_blocks_sampled`/
`pixel_per_block`), `isbatched=True` 렌더 모드로 배치 내 view별 상태를 누적하는
`BatchState`, `pixel_sampler`/`camera_sampler`까지 전부 얽혀 있음. 이 중 하나라도
잘못되면 **크래시가 아니라 조용히 틀린 업데이트가 적용될 위험**(CUDA 커널이
잘못된 차원으로 접근해도 항상 바로 죽지는 않음).

**판단**: 서로 얽힌 5개 조각(CGSolverState 포팅, BatchState 포팅, sampler 어댑터,
`background_polish_step` 배선, "안 터짐" 이상의 실질 검증)을 다 정확히 하려면
최소 여러 시간, 현실적으로 세션 하나를 넘어갈 규모로 판단 — 사용자와 합의 하에
**여기서 중단**. 착수는 다음 세션 이후로 보류.

### 판정

**부분 완료.** LM-RS를 VIGS-SLAM에 "이식할 수 있는가"라는 질문의 앞부분(rasterizer
호환성, 공존 가능성, 실제 라이브 데이터 호환)은 실측으로 **예**로 확인됨. 뒷부분
(실제 CG 최적화가 VIGS-SLAM 데이터에서도 유효한가)은 미착수 — 다음 세션 후보.
git 변경사항(`demo.py`, `vigs/vigs.py`, `vigs/gs_backend.py`,
`vigs/gaussian/renderer/__init__.py`, `thirdparty/diff-gaussian-rasterization-cg/`
신규)은 브랜치 `exp66-lmrs-polish-preempt`에 uncommitted 상태로 남아있음(전부
opt-in, 기본 동작 변경 없음, smoke test로 회귀 없음 확인 완료 — 커밋 여부는
사용자 결정 대기).
