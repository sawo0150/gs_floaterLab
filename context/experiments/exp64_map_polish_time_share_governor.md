# exp64 — map()↔background_polish 시간-비율 거버너 (적응형 스케줄링)

- 상태: **1차 구현 완료, 12F scale=1.5 검증 실행 중 (2026-08-17)**
- 선행: [exp63](exp63_vigs_slam_robust_general_mapping_tuning.md) — A2의 12F 회귀(frontend가
  바빠질수록 polish 기회가 우선순위 밀림으로 붕괴, 772/6586)와 freeze 스펙트럼 3지점(즉시
  freeze는 densify_and_prune을 영구히 못 받는 구간이 생겨 -10.46dB) 두 발견에서 직접 이어짐

## 문제의식

exp63에서 확정된 두 실패 모드:

1. 지금 `_gs_worker`는 **우선순위 기반**이다 — `_gs_queue`에 map() 패킷이 있으면 무조건 먼저
   처리하고, 큐가 비고 tracking도 idle일 때만 `background_polish_step`이 낀다. tracking이
   바빠지면(A2의 촘촘한 keyframe) polish 몫이 설계와 무관하게 우연히 붕괴한다(12F 6,586→772).
2. `freeze`는 **영구·비가역** 컷오프다 — 너무 이르면(축C2, 즉시freeze) 그 이후 구간은
   `densify_and_prune()`을 다시는 못 받아 파국적으로 나빠지고(-10.46dB), 아예 없으면(축C)
   가우시안이 무한히 늘어 OOM.

사용자 제안: 고정 비율이 아니라 **"최소 보장선 + 얼마나 방치됐는가"를 실측 기반으로 관리하는
적응형 스케줄러**를 만들어보자. OOM 문제는 이번 축에서 범위 밖으로 미룬다(5090에서 돌릴
예정이라 여유 있음 — 메모리 안전판은 후속 축으로).

## 설계

### 이미 있던 것 vs 새로 만든 것

- **뷰 선택의 staleness 회피는 이미 있었다.** `--background_polish_shuffle_epoch`가 후보
  풀을 셔플된 큐로 순회하며 전부 소진해야 재셔플한다 — 균등 랜덤보다 훨씬 "방치 방지"에
  가깝고, 이미 우리 채택 레시피에 켜져 있다. 이번 축에서 새로 만들 필요 없음(확인만 함).
- **map()↔polish 시간-비율 거버너는 없었다.** `--late_mapping_adaptive_background_target_steps`라는
  비슷한 이름의 기존(미사용) 메커니즘이 있었지만, 읽어보니 인과 방향이 반대다 — polish가
  목표 궤적보다 뒤처지면 map() iters를 **늘리는**(7) 쪽이고, 앞서 있으면 **줄이는**(3) 쪽이다.
  왜 이렇게 설계됐는지 exp63/이전 세션 어디에도 문서가 없고, 우리가 원하는 "polish가
  뒤처지면 map()을 줄여서 양보"와 방향이 달라 재사용하지 않고 새로 만들었다.

### 새 메커니즘 (`vigs/gs_backend.py`, `demo.py`)

- `background_polish_step()`/`map()` 각각에 **`VIGS_TIMING_LOG`와 무관하게 항상 켜진** 벽시계
  타이머를 추가(`_exp64_t0`/`_exp64_map_t0`) — 기존 `_Sect`/`_timing_fh` 계측은 env var가
  없으면 아예 기록을 안 해서 라이브 제어에는 못 쓴다.
- `self._polish_time_log`/`self._map_time_log`: 최근 `--polish_share_window_s`(기본 5초)
  구간의 (timestamp, ms) deque. 매 호출마다 오래된 항목을 pruning.
- `_throttle_map_iters(base_iters)`: 최근 구간의 실측 `polish_ms/(polish_ms+map_ms)`가
  `--polish_share_target_frac` 밑이면, 부족분에 비례해 `base_iters`를 줄인다. **절대
  `--polish_share_min_map_iters`(기본 2) 밑으로는 안 내려간다** — 축C2의 "영구 0"을 반복하지
  않기 위한 바닥.
- 기존 `late_mapping_*` 로직으로 정해진 `mapping_iters` 위에 **곱셈적으로 얹는다** — 기존
  메커니즘을 대체하지 않고 그 결과값을 추가로 조정.
- `--polish_share_target_frac -1`(기본)이면 완전 no-op — 기존 동작과 100% 동일.

### 알려진 한계 (설계 시점에 이미 인지)

- 항상-켜진 타이머가 `torch.cuda.synchronize()`를 안 부른다 — map()/polish 둘 다 함수
  내부에서 `.item()`/`.tolist()` 같은 암묵적 동기화가 자연히 일어나므로 대략적으로는
  맞겠지만, 정밀한 GPU-only 시간은 아니다. 거친 제어용으로는 충분하다고 보고 우선 진행.
- `--polish_share_target_frac` 목표값 자체는 지난 세션 계산(scale 1.5→2.0 실측을 27dB로
  선형보간, ≈10.5%)에서 가져온 추정치다 — **정확한 임계값이 아니라 첫 시도값.**
- 메모리 안전판 없음(의도적으로 이번 축 범위 밖).

## 실행 계획

12F(`aria301_12F`, scale=1.5 — A2 레시피 그대로일 때 23.84dB로 27dB 미달이었던 바로 그
조건)에 `--polish_share_target_frac 0.15 --polish_share_window_s 5.0
--polish_share_min_map_iters 2`만 추가해서, **다른 파라미터 전부 동일하게** 재실행.
baseline(23.84dB, polish 806회)과 비교.

- 가설: 목표 15%를 강제하면 polish 호출 수가 806보다 늘고, PSNR이 27dB에 가까워지거나
  넘는다.
- 실패 조건: throttle이 map() 자체를 너무 죽여서 오히려 PSNR이 떨어지거나(구조 성장 부족),
  거버너가 거의 안 걸려서(polish_share_throttle_calls≈0) 변화가 없는 경우.
- 통과해도 **1253/305 교차검증 전엔 채택 아님** — exp63 내내 반복된 원칙 그대로.

## 실행 결과 — 1차 실행, 12F scale=1.5, target=0.15 (2026-08-17)

`--polish_share_target_frac 0.15 --polish_share_window_s 5.0 --polish_share_min_map_iters 2`
추가, 나머지 전부 baseline과 동일:

| | baseline (거버너 없음) | exp64 (target=0.15) |
|---|---:|---:|
| PSNR (mean) | 23.84dB | **26.13dB** |
| PSNR (kf mean) | — | 26.06dB |
| background_polish steps | 806 | **2,928** (3.6배) |
| polish 후보 풀 크기 | ~880(추정) | 732(실측) |
| 최종 gaussian 수 | ~144k대 | 144,121 |
| CUDA peak | — | 8.37GB allocated / 11.46GB reserved (OOM 없음) |
| wall time | ~156s | ~168s(2:48) |

**가설 부분 확인**: 같은 replay_time_scale(1.5, 예산 동일)에서 map()을 실측 기반으로
throttle하는 것만으로 polish 횟수가 3.6배(806→2,928) 늘었고, PSNR이 **+2.29dB**
개선됐다(23.84→26.13). 이건 scale을 2.0으로 올려서(예산 자체를 33% 늘려서) 얻은 회복
(+4.26dB, 28.10dB 도달)보다는 작지만, **예산을 전혀 안 늘리고 같은 1.5배 안에서 재배분만
으로** 얻은 개선이라는 점이 다르다.

**아직 27dB 미달**: target을 0.15로 잡은 건 지난 세션 선형보간 추정(~10.5%)에 안전마진만
더한 첫 시도값이라, 더 공격적인 target(0.20~0.25)이나 window_s 조정으로 27dB를 넘길 수
있는지는 다음 시도 대상. 스로틀이 실제로 몇 번 걸렸는지(`share_throttle_calls`)를 이번
런은 로깅하기 전이라 못 봤음 — 로그 추가 완료, 다음 런부터 확인 가능.

**미검증**: 1253/305 교차검증 아직 없음 — exp63 원칙상 이 결과만으로 채택 불가.
wall time이 baseline 대비 소폭 늘었는데(156→168s) throttle로 map() iters를 줄인 게 오히려
시간을 늘린 것처럼 보이는 부분도 원인 미확인(측정 노이즈일 수도, map()이 더 자주 얕게
불려서 오버헤드가 늘었을 수도 — 다음 런에서 확인 필요).
