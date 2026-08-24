# exp65 실행 현황 보고 (읽기 쉬운 버전)

> 이 문서는 [exp65 메인 계획 카드](exp65_budget_constrained_gs_slam_plan.md)(방대하고
> 밀도 높음)와 별도로, **"지금까지 뭘 했고 지금 결과가 뭘 뜻하는지"만 빠르게 파악하기
> 위한 문서**다. 계획만 세우고 구현/실행 세부사항은 안 따라간 사람이 읽어도 이해되게
> 쓴다. **매 실행 사이클이 끝날 때마다 이 문서를 갱신한다.**
>
> 마지막 갱신: 2026-08-19

## 1. 계획 전체 구조 — 지금 어디까지 왔나

exp65 계획서(§3)는 이런 계단식 구조로 짜여 있다. **✅ 완료 / 🔶 부분·정정중 / ⬜ 착수 전.**

```
M0  계측 인프라                                          ⬜ 안 함
M1  init 품질 측정 (4단계)
    M1a  naive lift, 0-iter PSNR                          ✅ 1차 완료 (아래 §3)
    M1.5 prior 감사 (normal/depth 오차 실측)               ⬜ 다음 후보
    M1b  2D fit 후 3D lift                                 ⬜ 안 함
    M1c  multi-view 누적 열화                              ⬜ 안 함
M2  closed-form 색 풀이                                    ⬜ 설계만, 코드 없음
M3  topology anchor (Scaffold-GS류)                        ⬜ 설계만, 코드 없음
M3′ ray 1-DoF 제약                                          ⬜ 설계만, 코드 없음
M3″ confidence-adaptive DoF                                 ⬜ 설계만, 코드 없음
M4  carve loss 재해석                                       ⬜ 설계만, 코드 없음(기존 carve loss 코드 재사용 예정)
```

그리고 이 전체를 검증하는 별도 실험표가 있다(§4 E6 — "backpolish를 껐을 때 얼마나
품질이 빠지는가"를 재는 표):

```
E6 표 (S0~S5)
  S0 = 기존 그대로 (backpolish 켜짐)                        기존 값 재사용 (직접 안 돌림)
  S1 = backpolish만 끔                                       🔶 최초 측정에 결함 있어 정정함 (아래 §2)
  S2 = M1b init + backpolish 끔                              ⬜ M1b가 없어서 불가능
  S3 = 기존 init + M3′ 제약 + backpolish 끔                   ⬜ M3′가 없어서 불가능
  S4 = M1b + M3′ + backpolish 끔 (최종 목표)                  ⬜ 불가능
  S5 = M1b + M3′ + backpolish 켬                              ⬜ 불가능
```

**요약: 지금까지 만진 건 E6의 S0/S1, 그리고 M1 계단의 첫 칸(M1a)뿐이다.** 나머지는
전부 설계 문서만 있고 코드가 없다.

## 2. 지금까지 실행한 것들 — 시간순, 무엇을 껐고 켰는지

모든 실행은 같은 장면(**aria1253**, 1303프레임)·같은 실시간 배속(**1.5배속**, 옛날
논문/exp52 이후 계속 써온 것과 동일)으로 이뤄졌다. **1.5배속 사용은 직접 확인함
(2026-08-19, 사용자 질의로 재검증) — 1배속으로 잘못 돌린 적 없음.**

| 이름 | 뭘 껐고 켰나 (기존 대비) | PSNR (mean) | 상태 |
|---|---|---:|---|
| **S0** | 아무것도 안 건드림. 지금 채택된 레시피 그대로 | 27.81dB | 기존 값 |
| **S1** *(최초 측정, 결함 있음)* | backpolish만 끔. 그런데 **freeze(61.4% 지점 이후 map() 정지)는 그대로 둠** | 17.44dB | 🔶 **정정 대상** — 아래 참고 |
| **S1-nofreeze** *(정정판)* | backpolish 끔 + **freeze도 같이 제거**(map()이 끝까지 정상 작동) | **23.04dB** | ✅ 이게 진짜 "backpolish만 뺀" 공정한 비교 |
| S1b | backpolish도 끄고 map()도 0번 돌게 시도 | (측정 실패) | ❌ 폐기 — 코드가 0-iter를 막아놨고, 우회하니 실제 버그(`frozen_mask` 미정의)로 크래시. 버그만 기록 |
| **M1a control** | backpolish 끔 + map()도 아예 안 부름(안전한 다른 방법으로) + **기존 방식**으로 Gaussian 배치 | 16.45dB | ✅ 완료 |
| **M1a normalorient** | 위와 동일 + **새로 짠 코드**(표면 방향에 맞춰 Gaussian 배치) | 15.84dB | ✅ 완료, 아래 §4에서 더 분석 |

### 왜 S1을 정정했나 (요약)

과거(exp52~56 시절, "옛날 vanilla VIGS 22~23dB"라고 기억하시던 그 수치가 나온 시절)엔
**freeze라는 기능 자체가 코드에 없었다** — map()이 시퀀스 끝까지 정상적으로 계속
돌았다. freeze는 나중에(exp57) backpolish와 **같이** 도입됐고, "map()을 특정 지점에서
멈추는 대신 그 시간을 backpolish가 메운다"는 게 애초 설계 의도였다. 그래서 backpolish만
빼고 freeze는 냅두면, 시퀀스 뒤쪽 40%가 **아무 최적화도 못 받고 방치**되는 인위적으로
나쁜 상황이 된다. freeze까지 같이 빼서 재보니(S1-nofreeze) 23.04dB로, 기억하시던 옛
수치(22.73dB)와 거의 일치했다.

## 3. control / normalorient — 정확히 뭐가 다른가

둘 다 "M1a 조건"(backpolish 끔 + map() 안 돌림, **Gaussian이 태어난 그대로 아무 손질
없이 렌더링**) 위에서, **딱 하나만 다르게 실험한 것**이다: 새로 태어나는 Gaussian을
어떤 모양/방향으로 놓느냐.

| | **control** (원래 코드) | **normalorient** (이번에 새로 짠 코드) |
|---|---|---|
| 위치 | depth로 역투영한 3D 점 | 동일 |
| 색 | 그 픽셀의 RGB | 동일 |
| 회전 | 없음 (항상 똑같은 방향, "공"처럼 방향이 무의미) | 그 지점의 **표면 방향(normal)**에 맞춰 회전 |
| 모양 | 등방(모든 축으로 똑같이 둥근 공) | 표면 방향으로 얇게 눌린 원반(surfel) |

즉 control = "지금 실제 배포된 코드가 항상 해오던 방식", normalorient = "계획서 M1a가
원래 요구했던 방식(표면 방향 정보를 쓰기)을 이번에 처음 구현한 것". 이 둘을 비교하면
"표면 방향 정보를 추가하면 도움이 되는가?"라는 질문에 직접 답이 된다.

## 4. M1a 결과를 프레임별로 뜯어본 것 (2차 분석)

1차 결과(control 16.45 vs normalorient 15.84, -0.61dB)만 보면 "정보를 추가했는데 더
나쁘다"로 보이지만, 프레임 단위로 쪼개보니 신호가 두 개 겹쳐 있었다:

1. **IMU 초기화 전(frame 0~20) 구간에서만 재앙적으로 나쁨**(-2.7~-3.75dB). 이 구간은
   아직 SLAM 스케일이 안정되기 전이라 depth/pose 자체가 불안정한데, normal 방향
   정보는 그 불안정함을 그대로 지오메트리에 새겨버린다(반면 등방 공은 "방향"이라는
   개념이 없어서 틀릴 게 없음). → **이건 새로 짠 알고리즘의 결함이라기보다, 불안정한
   초기 구간이라는 조건에서 나온 부작용.**
2. **그 이후(frame≥30)에도 평균 -0.55dB 정도는 남지만**, PSNR/SSIM은 control이 이기고
   **LPIPS(사람이 보는 것과 더 비슷한 지표)는 normalorient가 계속 이긴다.** 프레임
   단위로도 normalorient가 이기는 경우가 27.7%(97/350)나 된다 — 균일하게 지는 게
   아니라 "선명하지만 살짝 어긋남(픽셀 지표엔 불리, 시각적 유사성엔 유리)"이라는
   진짜 트레이드오프.

## 5. 다음에 하기로 한 것 (이번 대화에서 확정)

1. **M1a를 nofreeze로 재실행** — S1과 마찬가지로, M1a도 "즉시 freeze"(map()을 아예
   0-iter로 만드는 방식) 대신 **freeze 없이 map()이 정상적으로 계속 작동하는 상태**에서
   control vs normalorient를 다시 비교한다. 목적: "표면 방향 정보로 만든 초기 배치가,
   그 뒤에 진짜 최적화가 붙었을 때도 여전히 차이를 만드는가, 아니면 최적화가 금방
   그 차이를 지워버리는가"를 확인. (원래 M1a의 "0-iter" 측정 자체는 계획서가 의도한
   설계라 폐기하지 않고 그대로 유지 — 이건 **추가** 확인.)
2. **map() 프레임당 처리시간이 시간이 갈수록 느려지는지 확인** — `VIGS_TIMING_LOG`라는
   기존에 이미 있던 계측 스위치(코드 수정 없이 환경변수만 켜면 map() 호출마다
   소요시간·반복횟수·카메라 수·gaussian 수를 기록)를 켜서 1번 항목의 재실행과
   동시에 확인한다. (참고: exp56에서 예전에 이미 "반복횟수×카메라 수가 지배적이고
   gaussian 수는 부차적"이라는 결론을 낸 적 있음 — 이번엔 그게 지금도 유지되는지
   재확인하는 것)

## 6. §5의 두 확인 결과 (2026-08-19, 같은 사이클)

### 6-1. M1a를 nofreeze로 재실행한 결과

| | control-nofreeze | normalorient-nofreeze | delta |
|---|---:|---:|---:|
| mean PSNR | 22.941dB | 22.881dB | **-0.060dB** |
| fixed-eval PSNR | 22.733dB | 22.666dB | -0.067dB |
| 최종 gaussian 수 | 68,887 | 79,093 | +15% (normalorient가 더 많이 만듦) |

**0-iter 조건(원래 M1a, -0.607dB)과 비교하면 갭이 약 1/10로 줄었다(-0.607 → -0.06).**
즉 **초기 배치를 어떻게 하든(공 모양이든 표면방향 원반이든), 진짜 map() 최적화가
붙으면 그 차이는 거의 다 지워진다.** 이건 두 가지를 뜻한다:
- M1a의 "normal 방향이 오히려 나쁘다"는 1차 결과는 **0-iter라는 극단적 조건에서만
  크게 나타나는 현상**이었지, 실제 운영 조건(map()이 정상 작동)에서는 거의 무관하다.
- 반대로 이건 **M3′/M3″(자유도 제약)의 존재 이유에 대한 경고이기도 하다** — map()이
  몇 번만 돌아도 초기화 방식의 차이를 금방 지워버린다면, "자유도를 줄여서 수렴을
  가속한다"는 계획의 핵심 주장이 성립하려면 정말 **극도로 적은 iteration
  예산**(0에 가까운) 구간에서만 의미가 있을 가능성이 있다 — M3′/M3″ 검증 시 iteration
  예산을 촘촘하게 스윕해서 "몇 iter부터 차이가 사라지는지" 확인이 필요.

### 6-2. map() 프레임당(호출당) 처리시간이 늘어나는가

`VIGS_TIMING_LOG`로 84회 map() 호출 전부를 기록해서 분석함(코드 수정 없이 기존
계측 스위치만 사용).

- **iters(반복횟수)가 여전히 압도적 지배 요인**: 초반 iters=54(첫 호출, gaussian
  2.1만개)는 호출당 ~2,000~3,000ms인데, 후반 iters=3(gaussian 8~9만개)는 호출당
  ~250~350ms로 오히려 **더 빠르다** — gaussian 수가 4배 늘어도 반복횟수가 줄면
  전체 시간은 줄어든다. (exp56이 예전에 "반복×카메라 수가 지배적"이라 낸 결론과
  일치)
- **다만 같은 반복횟수(iters=3) 구간 안에서만 보면, gaussian 수가 늘수록 호출당
  시간도 완만하게 늘어난다**: gaussian 수가 약 4.2만→8.6만(control)/4.6만→9.3만
  (normalorient)으로 2배 늘 때, 호출당 시간은 약 240ms→330~350ms로 **35~40% 증가**.
  단 상관관계는 약함(r=0.22~0.31) — GPU 경합 등 다른 잡음이 더 크게 낀다.
- **시퀀스 맨 끝(마지막 2회 호출)에서 큰 스파이크**: 시간이 600~1,060ms로 급증하고
  gaussian 수는 오히려 줄어듦(대규모 prune/정리 이벤트로 추정, 별도 현상).

**결론**: "map() 호출당 시간이 프레임이 갈수록 늘어나느냐"는 질문에 대한 답은
**"반복횟수가 같다면 완만하게 늘어난다(gaussian 수 2배당 +35~40%), 하지만 그보다
반복횟수(iters) 자체가 시간에 훨씬 더 큰 영향을 준다"**이다. 순수하게 "시간이 갈수록
느려지나"만 보면 늘어나는 게 맞지만, 그 증가폭보다 iters 스케줄(late_mapping이
반복횟수를 7→3으로 줄이는 것)의 효과가 훨씬 커서 실제 총 호출시간은 후반부가 더
짧다.

## 7. map() iters 정정 + late_mapping도 꺼본 결과 (2026-08-19, 같은 사이클)

§6-2에서 "54→7→3 세 단계"라고 보고했는데, 다시 보니 **PGBA(루프클로저) 보정 패킷이
들어올 때마다 프레임 위치와 무관하게 iters=20으로 튀는 4번째 경우**가 있었음(이번
run에서 2회 발생). 정정: **54(최초 1~2회) → 7(frame 650 전) → 3(frame 650 후,
`late_mapping_iters`) → PGBA 보정마다 20(위치 무관)**.

이어서 `late_mapping_start_frac`/`late_mapping_iters`까지 제거(iters가 시퀀스 끝까지
7로 고정, PGBA 스파이크만 여전히 20)하고 재실행:

| | nofreeze(iters 7→3) | **nofreeze+nolate(iters 계속 7)** | delta |
|---|---:|---:|---:|
| control PSNR | 22.941dB | **24.292dB** | **+1.351dB** |
| normalorient PSNR | 22.881dB | **24.193dB** | +1.312dB |
| control-normalorient 갭 | -0.060dB | -0.099dB | (비슷한 수준 유지) |
| wall time | 140.6~140.8s | **140.6~140.7s (거의 동일)** | +0.0~0.1s |
| gaussian 수(control) | 68,887 | 85,419 | +24% |
| CUDA peak allocated | ~7.83~7.85GB | ~8.37~8.44GB(+7~8%) | |
| CUDA peak reserved | ~9.2~10.3GB | ~10.28~10.34GB | GPU 16GB 중 64%, 여유 큼 |
| OOM/traceback | 없음 | 없음 | |

### 경쟁(GPU 자원 경쟁) 측면 판정: **충분히 괜찮다, 오히려 공짜로 이득**

`late_mapping_iters`(map()을 frame 650 이후 7→3으로 줄이는 것)는 원래 exp57/63
시절 **backpolish에게 GPU 시간을 양보하려고** 만든 장치인데, 지금 우리 레시피는
**backpolish가 이미 꺼져 있어서 양보할 대상이 없다.** 그래서 이 스로틀을 완전히
꺼도(iters를 계속 7로 유지해도):

- **wall time이 전혀 안 늘어남**(140.6s로 사실상 동일) — 1.5배속 예산과 무관하게
  GPU 시간이 남아돌고 있었다는 뜻.
- CUDA 메모리도 16GB 중 10.3GB(64%)로 여유 충분, OOM 위험 없음.
- **PSNR은 오히려 +1.3dB 공짜로 개선**(control 22.94→24.29, normalorient
  22.88→24.19).

**즉 지금 레시피(backpolish off) 조건에서는 `late_mapping_iters` 스로틀이 아무 실익
없이 품질만 깎아먹고 있었다.** 단, 이건 backpolish가 켜진 원래(S0) 조건에서도
그런지는 별개 확인 필요(그때는 진짜로 GPU를 backpolish와 나눠 써야 하니 결과가
다를 수 있음) — 아직 안 함.

control-normalorient 갭은 이 조건에서도 -0.06~-0.10dB 수준으로 여전히 작다(0-iter
때의 -0.61dB에 비하면).

## 8. M1.5는 보류, M1b/M1c로 직행 → M1b가 kill criterion에 걸림 (2026-08-19, 같은 사이클)

**M1.5(prior 감사)는 사용자 판단으로 보류.** MPS 포인트클라우드를 GT로 쓸 수 있긴
했지만(`/home/wosas/Desktop/26-1_RPM/Datas/CustomData/0416_Data/0416_301-1253/mps_0416_301-1253_vrs/slam/`에
실존 확인), MPS 자체도 proprietary SLAM 산출물이라 "진짜 GT"가 아니고 좌표계 정렬
리스크(이 프로젝트가 exp27에서 한 번 겪은 문제)까지 얹히는 게 부담스럽다는 판단 →
M1b/M1c로 바로 진행.

### M1b 구현 (3단계, 전부 검증 완료)

1. **순수 PyTorch 2D Gaussian 렌더러**(`exp65_axes/m1b/gaussian2d.py`) — GaussianImage
   방식(정렬 없는 가중평균 블렌딩, 3D CUDA rasterizer와 무관). **gradcheck 통과**(codex
   1회 + Claude가 다른 seed/크기로 독립 재검증 1회, 둘 다 True). 합성 이미지 재구성
   41dB로 렌더러 자체 작동 확인.
2. **실제 keyframe 데이터 덤프**(`gaussian_model.py`에 opt-in env-var 덤프 추가,
   `VIGS_M1B_DUMP_FRAME`/`VIGS_M1B_DUMP_DIR`, 꺼져 있으면 기존 동작 100% 동일) —
   frame 114(IMU 초기화 이후) RGB+depth+normal+카메라파라미터 실제로 저장됨,
   shape/값범위 직접 로드해서 확인함. depth 유효 비율 99.8%(대부분 픽셀에 깊이 있음,
   나중에 "깊이 데이터가 부족해서"라는 설명을 배제하는 데 씀).
3. **fit_and_lift.py** — 2D fit(GaussianImage 렌더러) → depth+normal로 3D lift
   (M1a에서 이미 검증한 quaternion 공식 그대로 재사용) → 실제 3D rasterizer로 렌더 →
   Δ_lift 측정. `Camera`/`GaussianModel` 생성 코드는 기존 코드베이스의
   `init_from_tracking`/`init_from_gui` 패턴을 직접 읽어서 그대로 재현(추측 안 함).
   좌표변환·normal변환·quaternion 공식도 기존 검증된 M1a 코드를 그대로 복사(재발명
   안 함). **코드 라인 단위로 직접 검토 완료.**

### 시행착오: 해상도 OOM

첫 시도(2000 gaussian, 원본 해상도 464×464)는 **`torch.OutOfMemoryError`**로 실패
(순수 PyTorch dense broadcast 방식이라 중간 텐서가 O(H·W·N)로 커짐, 15.46GB GPU에서
한 중간 텐서만 3.21GB 요구). fit은 저해상도(128×128)로, 그 다음 depth/normal 조회와
최종 렌더는 원본 해상도로 되돌리는 방식으로 수정(공식도 직접 검증: log-scale
재조정이 `log_scales += log(scale_factor)`로 정확한지 확인). 수정 후 재실행 성공.

### 결과 — Δ_lift가 kill criterion을 크게 초과

| | 값 |
|---|---:|
| 2D fit PSNR(128×128, 2000 gaussian, 800 iter) | **36.95dB** |
| lift 후 3D 렌더 PSNR(같은 128×128 기준 비교) | **17.56dB** |
| lift 후 3D 렌더 PSNR(원본 464×464, 참고용) | 17.15dB |
| **Δ_lift** | **19.39dB** |
| 유효하지 않은 depth로 버려진 gaussian | 4/2000(0.2%, 무시할 수준) |
| 실행 시간 | 14.77초, 크래시 없음 |

**계획서 자체가 정한 kill criterion은 "Δ_lift ≤ 3dB"** — 19.39dB는 그 6배가 넘습니다.
depth 커버리지(99.8% 유효)는 원인에서 배제됨.

**가장 유력한 원인(진단, 추가 검증 안 함)**: 2D fit에 쓴 렌더러(GaussianImage식
정렬없는 가중평균 블렌딩)와 3D lift 후 실제로 쓰는 렌더러(occlusion을 고려하는
alpha-compositing)가 **근본적으로 다른 렌더링 알고리즘**이라는 점. 2D 블렌딩은
모든 Gaussian이 모든 픽셀에 거리 기반으로 기여해서 빈틈이 생기기 어려운데, 3D
alpha-compositing은 실제 불투명도 누적이 1에 도달해야 픽셀을 완전히 설명하므로,
같은 파라미터라도 sparse하게 배치되면 훨씬 취약합니다. 즉 순수 "기하학적 lift
오차"만이 아니라 **"렌더링 방식 자체의 불일치"가 상당 부분을 차지할 가능성**.

### 판정 — 계획서의 kill criteria 그대로 따르면

> "M1b Δ_lift > 3dB → 2D→3D 변환 손실이 지배 → **M1b 폐기**, M1a + M3′로 축소하고
> C0 대신 C1로 후퇴"

즉 계획서 자체의 규칙대로면 **M1b는 여기서 접고, M1c(M1b에 의존)도 자동 보류**,
남은 방향은 **M1a(이미 완료) + M3′(ray 제약)** 으로 좁혀집니다.

## 9. flat_lift 대조실험 — Δ_lift의 92%는 기하 오차가 아니라 렌더러 불일치였음 (2026-08-19, 같은 사이클)

§8의 Δ_lift(19.39dB)가 "진짜 depth/normal lift 오차"인지 "2D fit에 쓴 렌더러(정렬
없는 가중평균 블렌딩)와 실제 3D 렌더러(occlusion 고려 alpha-compositing)가 아예
다른 알고리즘이라 생기는 불일치"인지 분리하는 대조실험을 추가로 돌렸다.

**설계**: 같은 2000개 2D-fit Gaussian을 depth/normal 없이 **전부 동일한 고정
depth(유효 depth의 중앙값) + 항등회전 + isotropic scale**로만 3D에 배치(기하 정보
전혀 안 씀)하고, 그래도 실제 3D rasterizer로 렌더링해서 비교(`--flat_lift`).

| | psnr_after_lift | Δ_lift |
|---|---:|---:|
| **real_lift**(실제 depth+normal 사용) | 17.56dB | 19.39dB |
| **flat_lift**(기하 정보 전혀 안 씀) | **19.10dB** | **17.85dB** |

**결론이 뒤집힘**: flat_lift(기하 정보 0)도 이미 17.85dB(92%)가 떨어진다. 즉
**진짜 depth/normal geometry가 기여하는 손실은 ~1.5dB뿐**(19.39−17.85) — 계획서
kill criterion(≤3dB)을 사실 통과하는 수준. 문제는 depth/normal lift가 아니라,
**GaussianImage식 2D 렌더러(정렬 없는 블렌딩)로 완벽히 맞춘 파라미터가, 같은 공간
배치라도 실제 3D alpha-compositing 렌더러에 넘기면 기하 정보와 무관하게 이미
크게 어긋난다는 것** — 두 렌더링 알고리즘 자체의 근본적 불일치.

**시사점**: M1b를 살리려면 2D fit 단계 자체를 GaussianImage 공식이 아니라 "실제
3D 렌더러를 평면(고정 depth)에 제약해서 쓰는 버전"으로 다시 설계해야 함 —
계획서 원안(GaussianImage 인용)과는 다른 접근이 필요.

**최종 판정 — 두 갈래**:
- **계획서 문구 그대로 적용**: Δ_lift(19.39dB) > 3dB → M1b/M1c 폐기, M1a+M3′로 축소.
- **더 정밀한 진단 기준(렌더러 불일치 통제)**: 진짜 기하 비용은 ~1.5dB로 kill
  criterion 통과 — 단, 이건 계획서가 측정하려던 지표(Δ_lift)를 원안과 다르게
  재정의한 것이므로 그대로 "M1b 통과"로 볼 수는 없고, "M1b를 다른 방식(3D렌더러
  기반 2D fit)으로 재설계하면 승산 있다"는 근거로 취급하는 게 정확함.

## 10. M3′(ray+normal 제약, DoF 14→6) 구현·측정 완료 (2026-08-19, 같은 사이클)

사용자 지시("M1b 재설계보다 M3′로 바로")에 따라 M1b는 계획서 문구 그대로 폐기 처리하고
M3′(ray-constrained 1-DoF) 구현으로 진행.

### 설계 — DoF 14→6 그대로 구현

같은 frame 114 실제 keyframe 데이터를 재사용, `exp65_axes/m3prime/constrained_opt.py` 신규:

- **위치**: FREE=3-DoF 자유 xyz. CONSTRAINED=`xyz = camera_center + t·ray_dir`
  (camera_center/ray_dir는 픽셀별로 고정, `t`(ray를 따라간 거리)만 학습). 3→1.
- **회전**: FREE=4-DoF 자유 quaternion. CONSTRAINED=정체성 또는 normal 기반
  quaternion(M1a/M1b에서 이미 검증한 half-way-vector 공식 재사용)으로 **영구 고정**,
  옵티마이저가 절대 안 건드림. 4→0.
- **scale**: FREE=3-DoF anisotropic. CONSTRAINED=1개 학습 스칼라(in-plane) +
  flatten_ratio 고정 비율(thin axis). 3→1.
- opacity·SH0색은 두 모드 다 자유(계획서가 요구 안 함).

**구현 기법**: `GaussianModel`의 `_xyz`/`_scaling`/`_rotation`은 단순 속성 읽기라
leaf `nn.Parameter`일 필요가 없다는 점을 이용 — CONSTRAINED 모드는 진짜 leaf
파라미터(`t`, `log_inplane_scale`, opacity, color)만 옵티마이저에 넣고, 매 forward마다
`_xyz`/`_scaling`/`_rotation`을 그 leaf들로부터 미분 가능한 표현식으로 재계산해서
대입 — 실제 production CUDA rasterizer(`render()`)를 그대로 재사용(속도/정확성
둘 다 안전).

**착수 전 필수 자체검증**: ray 파라미터화(`t`, 정규화된 방향벡터)로 복원한 3D 좌표가
기존 depth 기반 unprojection(M1a/M1b에서 이미 검증)과 일치하는지 20개 실제 픽셀로
대조 — **최대 오차 9.5e-7로 통과**. 코드도 라인 단위로 직접 검토.

### 실험 — 4조건(free/constrained × normal/identity-고정) × iteration 스윕

같은 keyframe에서 1,500개 픽셀을 고정 샘플링(4조건 공통, 공정 비교), iters
{0,1,3,7,20,50}로 1차, {...,100,300,1000,3000}로 확장 실행.

**발견 1 — DoF 제약이 초기화 민감도를 만든다는 핵심 가설은 부분적으로 확인**:

| iter | free_gap(normal−identity) | constrained_gap |
|---:|---:|---:|
| 0 | -0.122dB | -0.122dB(동일 출발점, 정상) |
| 50 | **+0.041dB**(거의 0) | **-0.744dB**(최대) |
| 3000 | -0.155dB(잡음 수준) | -0.661dB |

free 모드는 격차가 항상 잡음 수준(±0.2dB 이내)에 머물지만, constrained 모드는
50 iter 시점 -0.744dB까지 벌어졌다가 이후 다소 출렁이면서도 3000 iter까지 계속
free보다 뚜렷하게 큰 격차(-0.66dB)를 유지 — **"자유 최적화는 초기화 차이를
지우지만 제약된 최적화는 못 지운다"는 계획서 핵심 주장과 방향이 일치.** 다만
normal이 identity보다 나은 게 아니라 오히려 계속 나쁜 채로 남는다는 점은 M1a
때와 같은 방향의 결과(normal prior 자체의 신뢰도 문제 재확인).

**발견 2 — 결정적: ceiling(수렴 상한) acceptance 기준 실패**:

| iter | free_identity | constrained_identity | 격차 |
|---:|---:|---:|---:|
| 50 | 24.19dB | 17.75dB | 6.44dB |
| 300 | 31.18dB | 24.57dB | 6.61dB |
| 1000 | 33.16dB | 25.43dB | 7.73dB |
| **3000** | **34.32dB** | **25.74dB** | **8.58dB** |

constrained 모드는 iter 1000→3000 구간에서 거의 안 오름(+0.31dB, 사실상 정체)인
반면 free는 계속 상승 중(+1.16dB). **계획서 M3′ acceptance 기준 "6000 iter
지점에서 baseline 대비 -2dB 이내"를 3000 iter 시점에 이미 8.58dB 차이로 크게
실패** — 계획서가 스스로 예견한 리스크("DoF 축소는 상한을 낮출 수 있음 → A3
해제 단계 필수")가 그대로 재현됨.

### 판정

**M3′(R1+R2, 해제 단계 R3 없이)는 계획서 acceptance 기준을 실패한다.** 핵심
아이디어(제약이 초기화를 중요하게 만든다) 자체는 방향상 맞지만, R1+R2만으로는
수렴 상한이 너무 낮아서 이대로는 실용성이 없다. 계획서가 이미 이 실패 모드를
예상하고 R3(잔차 큰 영역만 자유 3D로 승격)를 대비책으로 설계해뒀는데, **R3는
아직 구현 안 됨** — 이게 M3′ 트랙의 다음(필수) 단계.

**미검증**: 단일 keyframe(114)·단일 픽셀샘플(1,500개, seed=65)만 테스트. 재현성,
다른 keyframe/scene 확인 전.

## 최종 요약 (이번 세션 exp65 M1/M3′ 트랙 전체)

| 단계 | 결과 | 판정 |
|---|---|---|
| E6 S1 | freeze confound로 최초 -10.37dB → 정정 -4.77dB | 완료, backpolish 순수 기여도 확정 |
| M1a(0-iter) | normal orient이 오히려 -0.61dB(pre-IMU 불안정+선명도/픽셀정합 트레이드오프) | 완료 |
| M1a(nofreeze, 실제 최적화) | 격차 -0.06dB로 1/10 축소 — 자유 최적화가 초기화 차이를 지움 | 완료, M3′ 착수 근거 |
| late_mapping 스로틀 발견 | backpolish-off에서 공짜 +1.3dB(S0 재확인 필요) | 미완(후속 필요) |
| M1b | Δ_lift=19.39dB(kill 기준 6배) → flat_lift 대조로 92%가 렌더러 불일치임을 규명, 진짜 기하비용은 ~1.5dB | 계획서 문구상 폐기, 재설계 시 승산 있음(안 함) |
| **M3′(R1+R2)** | 초기화 민감도 가설 확인(방향 일치), **그러나 ceiling이 8.58dB 낮아 acceptance 기준 실패** | **기각 — R3(선택적 해제) 없이는 불가** |

**다음 결정 필요(이후 §11에서 갱신됨)**: R3(잔차 기반 해제) 구현해서 M3′를 살릴지,
아니면 여기서 M1/M3′ 트랙을 접고 M2(closed-form 색) 또는 M4(carve loss)로 넘어갈지.

## 11. M3(mesh, A2) — 사용자가 원래 의도한 핵심 실험, 긍정적 결과 (2026-08-19, 같은 사이클)

M3′(개별 Gaussian의 자유도만 축소)가 ceiling 문제로 기각된 후, 사용자가 "원래 하려던
핵심 실험은 dense correspondence로 mesh를 만들어 그걸로 init·최적화해서 연산 부담을
줄이는 것"이라고 재확인 — 이게 계획서 §3 M3(topology anchor)의 **A2(surfel-on-patch)**
안이다. M3′와는 완전히 다른 축: M3′는 Gaussian 개수는 그대로 두고 개별 자유도만
줄였지만, M3(mesh)는 **여러 Gaussian이 mesh 정점을 공유**해서 진짜 파라미터 개수
자체를 줄인다.

### Reference 확인

- 이 프로젝트 자체엔 2D 픽셀 그리드 삼각화 재사용 코드 없음(기존 Delaunay 코드는
  `build_floater_region.py`의 3D 포인트클라우드 tetrahedralization뿐, floater
  region GT 마스크용이라 무관). `scipy.spatial.Delaunay`(이미 의존성)를 새로 적용.
- **SuGaR**(계획서가 지목한 참고 저장소)를 clone해서 실제 mesh-binding 공식을
  확인·포팅(`refs/SuGaR/sugar_scene/sugar_model.py` 186-500행): 위치=삼각형
  barycentric 보간, scale=삼각형 변 길이에서 유도(+면내 학습 가능 성분), 회전=
  **mesh face normal을 얇은 축으로 고정**(+면내 회전 1개만 학습).

### 구현 및 실행 (Stage A~D)

- **Stage A**: Sobel(기존 PPM 방식) + normal 변화량(곡률 대리 신호) 결합한 밀도 기반
  샘플링 → 1,500 정점 → Delaunay → **2,976개 삼각형**. 밀도 가중치가 실제로 작동함을
  확인(고텍스처 영역 삼각형이 저텍스처 대비 3배 촘촘함: 48.7 vs 147.2 px²).
- **Stage B**: SuGaR 공식 포팅(1 Gaussian/삼각형으로 단순화). quaternion 변환 자체
  gradcheck+기존 검증된 `build_rotation`과 왕복검증 통과(오차 3.6e-7).
  **첫 end-to-end 실행에서 실제 버그 발견**: SuGaR의 절대 두께 상수(1e-4)를 그대로
  가져왔는데, 이 장면은 실제 미터 단위라 in-plane scale(~0.055m) 대비 500배나 얇아서
  렌더러에서 수치적으로 붕괴 — PSNR이 5 iter까지 오르다(12.47→13.67) 급락(→9.64)한
  뒤 20 iter부터 소수점까지 완전히 똑같은 값 반복(그래디언트 완전히 죽음). **M1a/M3′에서
  이미 검증된 상대적 flatten_ratio(0.2) 방식으로 교체해 해결** — 이후 12.9dB→25.9dB로
  매끄럽게 단조 상승, flatline 없음.
- **Stage D**: mesh-bound(정점 공유) vs free(완전 독립) Gaussian을 **동일한 시작점**에서
  비교.

### 결과 — M3′와 대조적으로 안정적

| | 파라미터 수 | 비율 |
|---|---:|---:|
| mesh-bound(1,500 정점 + 2,976 face 속성) | **25,332** | **0.608** |
| free(2,976개 완전 독립 Gaussian) | 41,664 | 1.0 |

| iter | mesh PSNR | free PSNR | 격차 |
|---:|---:|---:|---:|
| 0 | 12.47 | 12.47 | 0(동일 시작) |
| 10 | 15.33 | 16.86 | 1.53 |
| 50 | 25.80 | 28.17 | 2.36 |
| 300 | 31.95 | 35.34 | 3.39 |
| 1000 | 34.16 | 37.51 | 3.35 |
| **3000** | **35.37** | **38.47** | **3.10** |

**M3′(같은 3000 iter 기준 격차 8.58dB, 계속 벌어지는 중)와 극명하게 대조적으로,
M3-mesh는 격차가 10~3000 iter 내내 1.5~3.4dB의 좁은 범위에서 안정적으로 유지된다
(발산도 정체도 아님).** 파라미터를 39% 줄이면서 품질 손실은 3dB 안팎으로 억제 —
사용자가 원래 의도한 "mesh로 연산 부담을 줄인다"는 목표가 실제로 작동함을 확인.

### 판정

✅ **M3(mesh, A2)는 유망하다.** M3′(개별 자유도 제약)는 기각됐지만, mesh 기반
파라미터 공유는 명확히 다른(더 나은) 결과를 낸다 — "자유도를 줄이는 방법"이
아니라 "무엇을 공유시켜서 줄이는가"가 관건이었다는 뜻.

**미검증/다음 단계**:
1. 색상 초기화를 M1b의 2D Gaussian fit으로 투영하는 방식(사용자가 원래 설계에
   포함시킨 부분)은 아직 안 함 — 지금은 단순 픽셀 평균색만 사용.
2. n_gaussians_per_triangle을 1보다 늘리면(SuGaR 기본값 6) 파라미터 절감 폭이
   더 커질 수 있음 — 미검증.
3. 단일 keyframe(114)·단일 mesh 크기(1,500 정점)만 테스트 — 재현성 미검증.
4. 실제 온라인 파이프라인(`map()`) 통합은 전혀 안 함 — 지금은 독립 진단 스크립트.

## 12. ⚠ 정정 — 속도 실측 및 "init에만 mesh" 재시도, 둘 다 뚜렷한 이득 없음 (2026-08-19, 같은 사이클)

§11의 "유망하다" 판정은 **속도를 재지 않고 파라미터 수·품질만 본 성급한 결론**이었다.
사용자 질문("속도 측면에서 이득이 있었냐")으로 재확인.

### 12-1. 속도 실측 — mesh를 최적화 내내 유지하면 4.46배 느림

| | iter당 시간 |
|---|---:|
| mesh-bound(매 iter마다 vertex→normal→quaternion 재계산) | **4.52ms** |
| free(파라미터 직접 읽기) | **1.01ms** |
| 비율 | **mesh가 4.46배 느림** |

렌더링(rasterization) 자체는 두 방식 다 같은 2,976개 Gaussian이라 동일 비용 — 차이는
전부 `reconstruct()`의 역산 오버헤드(face normal 재계산, quaternion 변환 등을 매
iteration마다 2,976개 face 전체에 대해 새로 함)에서 나온다. **파라미터 39% 절감이
실제 속도 이득으로 전혀 이어지지 않았다** — 오히려 벽시계 시간 기준 손해.

### 12-2. "init에만 mesh 쓰고 이후 자유 최적화" 재시도 — 이것도 이득 없음

사용자 제안: mesh+2D-fit은 **초기화 한 번에만** 쓰고, 그 결과를 일반 free Gaussian
파라미터로 "구워서"(bake) 이후엔 mesh 구조 없이 순수 free로 최적화 — 오버헤드
문제를 원천적으로 피함. 3조건 비교(전부 같은 xyz=삼각형 중심, 색/회전/scale만
다름, 이후 전부 동일 free 최적화):

- **A(baseline)**: 항등회전, 등방 scale, 단순 픽셀 평균색
- **B(mesh 기하)**: SuGaR 공식으로 회전(mesh normal 고정)+scale(비등방) 결정, 색은 A와 동일
- **C(mesh 기하+2D-fit 색)**: B와 동일 회전/scale + M1b의 2D Gaussian fit 결과를
  각 삼각형 중심에 `grid_sample`로 샘플링한 색(샘플링 정확도 자체검증: 오차 0)

| iter | A(baseline) | B(mesh 기하) | C(mesh+2D-fit 색) |
|---:|---:|---:|---:|
| 0 | **15.23** | 12.90 | 13.08 |
| 300 | **32.60** | 31.74 | 31.85 |
| 3000 | **36.23** | 35.91 | 36.00 |

**속도는 정상 회복**(1.04ms/iter, free와 동일 — bake 후 mesh 구조를 버려서 오버헤드
사라짐). 하지만 **품질은 거의 전 구간에서 단순 baseline(A)이 정교한 mesh 기하
init(B/C)보다 같거나 낫다.** 3000 iter 시점엔 거의 수렴해서 차이가 0.2~0.3dB로
줄지만, 시작부터 끝까지 A가 앞서거나 비슷하다. C가 B보다 색상 덕에 약간 나은
경우는 있지만(최대 +0.63dB) 미미하다.

**원인**: M1a에서 이미 반복 확인된 패턴과 동일 — normal 방향에 맞춘 얇은
(anisotropic) Gaussian은 방향이 조금만 어긋나도 커버리지가 크게 줄어드는데, 등방
Gaussian은 방향과 무관하게 어느 정도 덮는다. **이 세션에서 이 방향의 결과가 벌써
세 번째 재현**(M1a 0-iter normal orient 열세, M3′ constrained normal 열세, 지금
이 결과) — 우연이 아니라 이 파이프라인에서 일관되게 나타나는 현상으로 봐야 한다.

### 최종 판정 — mesh 접근 두 가지 다 순이득 없음

| 시도 | 속도 | 품질 | 결론 |
|---|---|---:|---|
| mesh를 최적화 내내 유지(제약) | ❌ 4.46배 느림 | 파라미터 39%↓, 격차 안정적(3dB대) | 속도 손해로 순부정 |
| mesh를 init에만 쓰고 bake | ✅ 정상 속도 | **baseline보다 오히려 낮음** | 품질 이득 없음으로 순부정 |

**mesh 기반 접근(M3, A2안) 전체를 이 구현으로는 채택할 근거가 없다.** 파라미터
공유든 초기화든, free 최적화가 그 차이를 지우거나(M1a부터 반복된 패턴) 오버헤드가
이득을 상쇄한다.

**아직 안 해본 것(향후 후보, 지금은 낮은 우선순위)**:
1. `reconstruct()` 자체를 벡터화/캐싱으로 최적화해서 mesh-유지 방식의 속도 손해를
   줄일 수 있는지(근본적으로 안 될 수도 있음, 미확인)
2. n_gaussians_per_triangle>1, 다른 keyframe 재현성 — 위 결론이 이미 부정적이라
   우선순위 낮음

## 13. M2(closed-form 색) — 기각, 정확한 원인 규명 (2026-08-19, 같은 사이클)

### 설계

기하(xyz/scale/rotation)를 고정하면 렌더링이 색상에 대해 거의 선형이라는 계획서
아이디어. 정규방정식(A_j=Σw_ij², b_j=Σw_ij·residual, c_j←c_j+b_j/(A_j+λ)) 시도.

**제약 확인**: 이 프로젝트의 rasterizer(`vigs/gaussian/renderer/__init__.py`)는
`rendered_image, radii, rendered_expected_depth, n_touched, alpha`만 노출 —
픽셀별-Gaussian별 blending weight는 Python으로 안 나옴. CUDA 커널 수정은 이
프로젝트가 계속 고위험으로 다뤄온 영역(exp56 사례)이라 범위 밖으로 유지.

**실제 구현**: `b_j`는 진짜 backward pass의 gradient(정확함), `A_j`는 이미 노출된
`n_touched`(픽셀 터치 개수)로 근사(부정확함을 명시하고 시작).

### 결과 — 1차 시도부터 명확히 기각

| | PSNR 궤적 |
|---|---|
| Adam(색만, 500 iter) | 12.81→13.06(1 iter)→...→**21.50**(500 iter) |
| closed-form(3 step) | 12.81→12.90→12.95→**13.00** |

**closed-form 3 step을 다 합쳐도 Adam의 단 1 iteration(13.06dB)보다도 못 미친다.**
속도는 훨씬 빠름(3 step에 0.0027초 vs Adam 20iter에 0.067초)이지만 품질이 너무
낮아 쓸모없음.

**원인 재확인(1회 진단, 추가 없음)**: damping(λ=1.0)이 문제인지 확인 — n_touched
실측 분포(평균 380, 중앙값 113, 최대 14456)가 충분히 커서 λ=1.0은 무시할 수준.
damping은 원인이 아님. **진짜 원인: n_touched가 Σw_ij²의 근사로 부적합** —
가장자리의 낮은 기여 픽셀까지 다 세어서 진짜 대각항을 과대평가, 스텝을 필요한
크기보다 훨씬 작게 만듦.

### 판정

**기각.** CUDA 커널 없이는 정확한 Σw_ij²을 못 구해서 이 근사로는 안 됨. 계획서
kill criterion("occlusion 비선형성 지배")과 결이 비슷하지만 더 구체적 원인
(n_touched 근사 부적합)까지 확인.

## 14. M4(carve loss) — 완료, 기각

계획서: 기존 carve loss(exp38~44d2, prune/gate/force)를 "floater 제거"가 아니라
"수렴 가속"으로 재평가. 코드는 대부분 재사용(`3dgs-custom/eval/carve_loss.py`),
지표만 "동일 iteration 예산에서 PSNR 우위"로 교체. 계획서의 핵심 가설:
B3(force/relocation, "삭제 대신 이동해서 이미 학습한 color/scale 재활용")가
B1(prune, 순수 삭제)보다 같은 예산에서 더 빨리 수렴해야 한다.

### 실험 설계

`gs_floaterLab/data/03_rgb_3dgs_full` 위에서 7000 iteration(축소 예산)으로
3개 config 순차 실행 — control(`exp65_m4_control_off.yaml`, carve 전체 off),
b1only(`exp65_m4_b1only.yaml`, prune+gate만, prune_start_iter 7000→1000·
prune_interval 1000→500으로 앞당겨 짧은 예산 안에서 실제로 여러 사이클 돌게
조정), b3only(`exp65_m4_b3only.yaml`, force만, exp40b 파라미터 그대로).
모두 exit_code 0, 25분 제한 내 완료.

### 결과 (PSNR, iteration별)

| iter | control | b1only(삭제) | b3only(이동) |
|---:|---:|---:|---:|
| 500  | 21.03 | 21.03 | 21.03 |
| 1000 | 22.69 | 22.67 | **22.81** |
| 2000 | **24.66** | 24.55 | 24.57 |
| 3000 | 25.27 | 25.46 | **25.60** |
| 4000 | 27.05 | 27.05 | **27.10** |
| 5000 | **28.42** | 28.03 | 28.24 |
| 6000 | 28.66 | **28.76** | 28.69 |
| 7000 | **28.93** | 28.86 | 28.65 |

wall-clock: control 137s, b1only 191s, b3only 211s — **b3only가 가장 느리면서
최종 PSNR도 가장 낮음**(추가 비용을 정당화하는 이득이 없음).

### 판정

**기각.** 계획서의 accept criterion("B3가 동일 예산에서 B1을 이김")이 이
실행에서 성립하지 않음(`b3_beats_b1_at_7000: false`) — 최종 checkpoint(7000)
기준 순위는 control > b1only > b3only로, carve loss 자체가 없는 baseline이
가장 높음. trajectory를 통째로 보면 순위가 checkpoint마다 뒤집힘(1000·3000·
4000에서는 b3가 앞서고, 2000·5000·7000에서는 control이 앞섬) — 이는 이
프로젝트에서 이미 실측된 run-to-run 노이즈(±0.24~0.33dB, exp30/43)와 같은
크기라 "수렴 가속 효과가 있다"는 신호로 보기 어려움. B3가 추가 wall-clock
비용까지 지불하면서 이 노이즈 수준의 변동만 만든다는 것 자체가 기각 근거.
단일 seed 실행이라 "B3가 확실히 더 나쁘다"고 단정할 근거는 아니지만, 계획서가
요구하는 "동일 예산 우위"를 뒷받침하는 증거는 전혀 없음.

## 최종 결정 필요

**M1/M3/M3′/M2/M4 전부 기각 — 이 세션에서 시도한 "예산 수요 자체를 줄인다"는
축이 전부 실패.** 공통 패턴: 자유 최적화가 초기화/구조 차이를 지우거나
(M1a·M3-mesh baked-init), 근사 오차가 이득을 상쇄하거나(M3′ ceiling, M2
n_touched), 오버헤드가 파라미터 절감분을 상쇄하거나(M3-mesh 속도), 노이즈
수준 이상의 효과가 안 보임(M4). exp65의 "budget-constrained GS-SLAM"
원래 계획(M0~M4로 iteration/파라미터 예산을 줄여서 실시간 예산 안에 맞춘다)을
이 형태로는 더 이상 밀어붙일 근거가 없음 — 다음 세션에서 축 자체를 재설계할지,
아니면 exp65를 종결하고 strict streaming 27dB 트랙(CLAUDE.md 최우선순위)으로
돌아갈지 사용자와 논의 필요.

진행 상황은 이 파일에 계속 갱신한다.
