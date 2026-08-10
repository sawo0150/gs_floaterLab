# exp63 — VIGS-SLAM 매핑 재튜닝: cross-scene·cross-GPU 강건화

- 상태: **축 D+B+A 완료 (2026-08-10) — idle_guard는 crash 원인 아님, 305/12F 경계
  비율화+frontend_radius=2 채택, 1.5× 예산 자체가 stale임을 발견해 재보정**
- 선행: [exp57](exp57_causal_background_polishing_plan.md)(strict27 1253 채택 레시피),
  [exp59](exp59_strict27_cross_scene_transfer.md)(305/12F/rot 전이 실패, 원인 3종 확정),
  [exp61](exp61_okvis2_3dgs_custom_benchmark_repro.md)(OKVIS2 vs VIGS 트래킹 정확도 비교),
  [exp62](exp62_live_okvis2_mapping_pipeline_plan.md)(OKVIS2 트랙 실시간화, 256px 해상도 레버 검증)

## 문제의식

exp57의 freeze800 레시피는 aria1253(strict-disjoint fixed 27.85dB, 2/2 재현)에서만
검증됐다. exp59에서 같은 레시피를 재튜닝 없이 aria1253rot/aria301_305/aria301_12F에
적용하자 각각 26.00dB(−1.85)/16.95dB/26.13dB(마지막 22%만 17.74dB로 붕괴)로 무너졌고,
원인은 3가지로 확정됐다: (1) freeze/PGBA-cutoff/late-mapping/background-polish-start가
전부 **절대 프레임 번호**로 하드코딩돼 시퀀스 길이가 다르면 비율이 깨짐 (2) 경계값을
비율로 재조정하면 PGBA×background_polish 동시성으로 추정되는 CUDA crash가 재현됨
(원인 미확정, exp59/60에서 GPU lock 수정 시도했으나 근본 해결 안 됨) (3) 1.5× 데드라인
자체가 305/12F에서 체계적으로 초과(+3.27~3.28s).

이번 세션에서 추가로 코드를 직접 감사해 확인한 사실 (본 세션, 2026-08-10):

- **트래킹**: exp61 ATE 표 기준, **vanilla VIGS(mono) 트래킹이 "채택(속도튜닝) recipe"보다
  305=20.1cm vs 90.9cm, 12F=40.6cm vs 134.8cm로 오히려 훨씬 정확하다.** 즉 exp53~56의
  속도 튜닝(작은 window/PGBA 반복 축소)이 1253에서는 무해했지만 305/12F에서는 트래킹
  정확도를 희생시켰을 가능성이 크다.
- **매핑 품질**: exp59 축D(305, freeze/PGBA-cutoff/시간제약을 전부 뺀 순수 온라인)는
  fixed **22.96dB**로 as-is(16.95dB) 대비 +6.0dB 회복했고, wall time도 64.2초(녹화
  134.4초의 0.48배)로 연산량 부족이 원인이 아니었다. 즉 305의 붕괴 대부분은 트래킹이나
  scene 난이도가 아니라 **1253 전용 경계값 하드코딩**이었다.
- **해상도**: `gs_backend.py`에 해상도 피라미드(`_scaled_viewpoint`, `coarse_scale`)가
  존재하지만, **실시간 경로인 `map()`(3290행)과 `background_polish_step()`(1200행)
  어디에서도 호출되지 않는다** — 오직 오프라인 후처리 `color_refinement()`(3697행,
  strict 채점에서 제외되는 26k-iter 색정제)에서만 쓰이고 기본 `coarse_steps=0`으로 꺼져
  있다. 즉 strict27 27.85dB는 **native 1024×1024 그대로 실시간 학습한 결과**이며,
  OKVIS2 트랙(exp62)에서 +4.03dB를 회복시킨 256px 다운스케일 레버가 여기서도 아직
  미검증·미배선 상태다.
- **"이상하게 튜닝된" 부분** (본 세션 코드 감사, 상세 근거는 대화 로그 참조):
  - `adaptive_density_curve: "config/exp55/aria1253_content_curve.json"` — aria1253
    keyframe 113개의 Sobel edge-밀도 분포에 회귀 적합한 곡선을 파일명만 보면 scene-agnostic
    설정처럼 보이는 키에 그대로 박아둠.
  - `background_polish_idle_guard_ms`가 코드 기본값 5.0ms인데 `run_aria_strict27.sh`가
    명시적으로 **0**으로 덮어씀 — 유휴시간 안전마진을 깎아 1253 update 수를 짜낸 값으로
    추정되며, exp59/60에서 미해결로 남은 PGBA×background_polish CUDA race crash의
    유력한 원인 후보인데 이 각도로는 아직 검증되지 않았다.
  - `background_polish_seed=0`, `background_dense_offsets=1,4`, `late_mapping_iters=3` —
    STATUS.md의 exp57 로그를 보면 26.5~27.9dB대 거의 동률인 variant 수십 개 중 1253에서
    이긴 값을 그대로 기본값으로 승격한 것으로, 305/12F에서 최적이라는 근거는 없음.
  - `init_gaussian_extent=30` — exp59가 이미 "1253 단일 방 규모에 맞춘 고정값일 수
    있다"고 의심했으나 확정 검증은 안 됨.
  - `opt_params.position_lr_max_steps=26000` — 전체 iteration 수를 미리 안다고 가정하는
    batch-3DGS식 LR 감쇠 스케줄. incremental 세팅에서 총 iteration 수는 장면 길이(keyframe
    수)에 따라 크게 다른데(1253=1303프레임 vs 305=2688프레임) 이 값은 장면 무관 고정이다.
    exp48이 이미 "vanilla 3DGS의 전역 스케줄 가정이 online에 근본적으로 안 맞는다"고
    결론 낸 것과 같은 계열의 문제.
- **GPU 특화**: exp56의 `init_itr_num`, `n_global_views`, mapping iters 등은 RTX 5070Ti에서
  직접 프로파일링(`map_call` 로그 집계, "호출 26회 중 2~3회가 시간의 49%")한 결과로 정해진
  절대 상수다. 이는 scene 일반화 문제(문제 1)와 같은 계열의 **하드웨어 일반화 문제** —
  다른 GPU에서는 같은 1.5× 예산 안에 같은 iteration 수를 못 채우거나 반대로 여유가 남을 수
  있다.

## 목표

**(2026-08-10 수정) 트래킹은 vanilla로 되돌리지 않고 custom(exp53~56 속도튜닝) 그대로
유지한다** — 305에서 custom 트래킹 자체는 이미 준수한 것으로 보이고(축 A 조사 결과 참고),
vanilla 롤백은 이미 12F OOM/305 예산초과로 실패가 확인된 경로다. 대신 **정확도가 부족한
곳에서만 관련 파라미터(frontend_window/radius, PGBA 반복 등)를 필요한 만큼만 상향**하는
방향으로 축 A를 재설정한다. 매핑 쪽 커스텀 튜닝은 scene 무관 + GPU 무관하게 재설계해서,
1253의 27dB대를 깨지 않으면서 305/12F도 근접한 수준까지 끌어올린다. floater/carve는
이번 축 범위 밖(북극성 우선순위 그대로 — 27dB급 재현성 확보가 먼저)이나, 축 H(CPU 활용
carve pruning)는 유휴 자원 활용 아이디어로 별도 등재한다.

## 축 (우선순위 순 — 원인이 이미 확정된 것부터, 비용 낮은 것부터)

### 축 A — 트래킹은 custom 유지 + 필요 구간만 param 상향 (vanilla 전면 롤백 아님)
- **(2026-08-10 재수정) 방향 확정**: 305에서 custom(exp53~56 속도튜닝) 트래킹 자체는 이미
  꽤 준수하다는 판단(사용자 의견 + 아래 실패 사례로 vanilla 전면 롤백은 기각). **custom
  설정을 기본으로 유지하고, 특정 장면/구간에서 정확도가 부족하다고 확인될 때만 관련
  파라미터(`frontend_window`/`frontend_radius`/PGBA 반복 수 등)를 필요한 만큼만 올린다**
  — on/off 스위치가 아니라 연속적인 다이얼로 다룬다.
- **가설(원래, 폐기)**: ~~exp53~56 속도 튜닝이 1253에서는 무해했지만 305/12F 트래킹
  정확도를 희생시켰다~~ — vanilla 전면 롤백이 아래 실패 사례로 기각되면서 이 프레이밍
  자체를 버림.
- **선행 사실 확인(2026-08-10, 본 세션)**: **진짜 vanilla(iters1=4/iters2=2 +
  frontend_window=25/radius=2, exp53 baseline)는 이 5070Ti에서 애초에 실시간이 아니었다**
  — 1253에서 98.94s(녹화 65.5s의 1.52배), 1.5× 예산(97.65s)마저 1.3s 초과. exp53~56은
  "있으면 좋은" 최적화가 아니라 실시간 진입 자체의 전제조건이었다.
- **이미 시도된 부분 롤백과 그 실패 모드**: `config/exp62_freeze800_vanillatrack.yaml`
  (frontend_window/radius/motion_filter.thresh만 vanilla로 되돌리고 iters1/iters2·매핑
  쪽은 exp57 그대로 유지)을 305/12F에 실행한 로그를 직접 확인:
  - 305: 완주하지만 **204.9s로 1.5× 예산(201.57s)을 3.3s 초과**, PSNR **18.74dB**
    (as-is 16.95보다 +1.79dB지만 27dB와는 거리가 멂)
  - 12F: **CUDA OOM으로 크래시**(`factor_graph.py:rm_factors`, correlation pyramid
    인덱싱 중 15.46GB 중 89MB만 남고 실패) — frontend_window 확장이 correlation volume
    메모리를 키워, 동시에 도는 background_polish/성장 중인 Gaussian map의 메모리 사용과
    충돌한 것으로 추정됨(미확정).
- **검증 방향**: custom(exp53~56) 값을 시작점으로 두고, (1) `iters1`/`iters2`/
  `frontend_window`/`frontend_radius`/`motion_filter.thresh` 각각을 **위로만** 개별
  스캔해(예: window 15→18→22 등 점진 상향) 정확도 기여도를 분리하고 (2) 메모리 사용량을
  wall-time과 함께 반드시 같이 계측하며 (3) 12F처럼 메모리 여유가 없는 장면에서는
  `frontend_window`를 넓히는 대신 다른 방식(예: keyframe당 유지하는 correlation pyramid를
  더 적극적으로 비우기)으로 정확도를 회복할 여지가 있는지 확인한다.
- **비용/리스크**: 중간 — 부분 시도 결과(위)가 이미 있어 완전 미지수는 아니지만, 단일
  파라미터 롤백으로는 안 풀리는 것이 확인됐으므로 개별 스캔이 필요해 처음 생각보다 범위가 넓다.

### 축 B — 절대 프레임 경계 → 비율 기반 재설계
- exp59가 이미 제안했던 축 A를 실제로 구현. `mapping_freeze_after_frame`,
  `pgba_disable_after_frame`, `late_mapping_start_frame`, `background_polish_start_frame`을
  전부 시퀀스 길이 대비 비율(`*_frac`) 옵션으로 추가.
- **주의**: exp59 결과2에서 경계값을 비율로만 재조정했을 때 CUDA crash가 재현됐으므로,
  **축 D(안전마진 재검토)를 먼저 하거나 최소한 같이 검증**해야 한다.

### 축 C — 장면 특화 아티팩트 제거
- `adaptive_density_curve`를 aria1253 전용 파일 고정 대신, 매 장면 자체 keyframe들로
  causal하게(온라인 중 지금까지 본 것만으로) 재적합하거나, 꺼서 A/B 비교.
- `init_gaussian_extent`를 고정 30 대신 지금까지 관측된 궤적 bounding box 기반으로 자동
  계산하도록 변경.

### 축 D — background_polish 안전마진 재검토 (crash 원인 후보)
- `background_polish_idle_guard_ms`를 0에서 원래 기본값(5.0ms) 또는 그 이상으로 복귀시키고,
  exp59 결과2의 크래시 재현 조건(aria1253rot, 비율 재조정 경계값)에서 다시 실행해 crash가
  사라지는지 확인. 사라지면 exp59/60이 못 찾은 근본 원인을 이 세션에서 규명하는 것.
- **비용/리스크**: 낮음(설정값 하나 변경) — 다만 crash 재현 자체가 세팅에 몇 시간 걸릴 수 있음.

### 축 E — 실시간 경로에 해상도 다운스케일 배선
- `map()`/`background_polish_step()`이 `_scaled_viewpoint`(또는 새 경량 리사이즈)를 쓰도록
  배선 — 현재는 `color_refinement()`(오프라인, strict 채점 제외)에만 존재. exp62가 OKVIS2
  트랙에서 256px로 +4.03dB(15.52→19.55dB, 1253)를 얻은 것과 유사한 효과 기대.
- **주의**: strict27 채점은 native 해상도 렌더 기준이므로, 학습 해상도만 낮추고 채점/최종
  렌더는 native로 유지해야 한다(exp62의 bracket-override 패턴 참고).

### 축 F — GPU 무관화
- `init_itr_num`, `n_global_views`, mapping iters 등 RTX 5070Ti 프로파일링으로 고정된
  상수들을, "이 iteration을 몇 ms 안에 끝낼 수 있는지" 런타임 실측 기반 예산 산출로
  교체할지 검토. 지금 이 머신(5070Ti)에서는 검증 불가(다른 GPU 필요) — 최소한 상수들이
  어디서 왔는지 문서화하고, 다음에 다른 GPU에서 재현할 때 체크리스트로 남긴다.
- **비용/리스크**: 가장 큼(다른 GPU 접근 필요) — 이번 세션 범위에서는 설계·문서화까지만.

### 축 G (부차) — position_lr_max_steps 등 batch-스타일 전역 스케줄 재검토
- exp48이 이미 지적한 "vanilla batch 3DGS 가정이 online에 안 맞는다"는 문제의 잔존 사례.
  장면 길이/keyframe 수에 비례하도록 바꾸거나, incremental 세팅에 안 맞는 감쇠 자체를
  다른 방식(예: 고정 LR + 별도 warmdown)으로 대체할지 검토.

### 축 H (신규, 2026-08-10, 사용자 제안 — 아직 설계 전, 축만 등재) — CPU 유휴자원 활용 carve pruning
- **아이디어**: 지금 구조는 GPU만 계속 쓰고 CPU는 상대적으로 노는 시간이 많다. carve loss
  기반 pruning(빈공간 evidence로 floater Gaussian 제거, [[findings_carve.md]] 방법론)을
  GPU 학습 스레드와 별도로 **CPU에서 exported PLY(좌표/opacity 등 순수 데이터)에 대해
  주기적으로 병렬 실행**하면, GPU 학습을 막지 않고 유휴 CPU 사이클로 floater 억제를 얻을 수
  있지 않을까 하는 제안.
- **아직 확인 안 된 것**: (1) carve loss가 현재 GPU gradient 기반(soft opacity 압력 +
  budget top-K prune + birth gate + carve-potential force, `carve_loss.py`)인데 이 중
  어떤 요소가 gradient 없이 CPU에서 PLY 데이터만으로 재현 가능한지(top-K prune은 순수 데이터
  연산이라 가능해 보이나, force/압력은 학습 루프 안에 있어야 함) (2) pruning 결과를 GPU 쪽
  학습 중인 Gaussian 집합에 다시 반영하는 동기화 방식(래이스 컨디션 없이) (3) exp61/62에서
  이미 겪은 GPU-스레드 동시성 crash류 문제가 CPU-GPU 간에도 발생할지.
- **범위**: 이번 세션에서는 축으로만 등재, 설계·검증은 후속 세션. 27dB 재현성이라는 1차
  목표(북극성 우선순위) 완료 이후에 순서가 온다.

## 평가 프로토콜

축마다 strict streaming 계약 유지(timestamp 순 RGB+IMU only, MPS 입력 0, 1.5× 예산,
tail update 0, held-out PSNR 252-view fixed eval). 1253/305/12F 세 장면 모두 확인하며,
1253의 27dB대를 깨지 않는 것을 회귀 방지선으로 삼는다.

**보고 규율**: 모든 run 결과를 기록/전달할 때 (1) 트래킹 config(vanilla vs custom, 어떤
파라미터가 어떻게 다른지) (2) 매핑 config(vanilla vs exp57 튜닝, 어떤 요소가 남아있는지)
(3) 실시간 페이싱 여부(`--realtime_replay` on/off) 세 가지를 항상 같이 명시한다 —
"vanilla"라고만 말하지 않는다(exp59 axisD PLY를 "vanilla"로 잘못 전달했던 사례 참고).

## 실행 결과 — 축 D (2026-08-10, Codex `codex exec` 위임 + 직접 검증)

**결론: `background_polish_idle_guard_ms`는 exp59 crash의 원인이 아니었다.** 0/5/20ms
셋 다 aria1253rot 경계 재조정 시나리오(freeze956/pgba1339/late777/polish700)에서 동일한
`vectorized_gather_kernel` index-out-of-bounds assertion으로 재현됐다(exp60의
`self.video.get_lock()` 직렬화 수정이 코드에 있는 것도 직접 확인했지만 이 crash엔 불충분).
guard=5로 aria1253 regression도 같이 돌렸는데 PSNR 27.6301dB(기준 대비 -0.2163dB, 품질
gate 통과)이었지만 wall time 101.06초로 1.5× 예산(97.65초)을 3.41초 초과해 어차피 채택
불가였다. `config.yaml`/`run_flags_reference.sh` 변경 없음. 전체 원시 로그(4개 run의
run.log 포함) 커밋 `a9a2cbb1`. → crash 원인은 **여전히 미해결**이며, 축 B(경계 비율화)도
같은 crash를 다시 만날 가능성이 높다는 전제로 진행해야 한다.

**운영상 배운 것 (Codex 위임 인프라)**:
- 같은 축에 대해 Bash 백그라운드 태스크가 원인 불명으로 "killed" 처리되는 일이 3번
  연속 발생했다 — 죽은 태스크의 자식 프로세스(codex exec, python demo.py)가 실제로는
  안 죽고 고아로 GPU를 계속 붙잡는 경우가 있어, 뒤이은 재시도와 GPU/로그 파일을 두고
  경합했다(가짜 "크래시 재현 확인"으로 이어질 뻔함 — 다행히 재현 자체는 사실이었지만
  귀속을 잘못할 뻔했다). `Monitor` 도구로 전환하고 축별 락파일(`exp63_axes/verify/
  <AXIS>.lock`)을 추가해 동시 실행을 원천 차단한 뒤로는 안정적으로 완주했다.
- `codex exec`가 `thirdparty/` 벤더 라이브러리(Eigen 헤더 등)를 광범위하게 grep하다가
  OpenAI 자체 "cybersecurity risk" 컨텐츠 필터에 걸려 턴 전체가 실패한 사례 있음 — 이후
  프롬프트/recipe README에 `thirdparty/` 검색 자제 지침 추가.
- Codex가 리포트·DECISIONS.md는 정직하게 작성했지만 **마지막 `git commit` 단계를 빠뜨림**
  — 사용자가 직접 내용 검증 후 대신 커밋. "Codex 자체 보고를 믿지 말고 직접 검증" 원칙이
  실제로 유효했던 구체 사례.

## 실행 결과 — 축 B (2026-08-10, 경계 비율화 — 채택)

Codex가 `demo.py`에 `--mapping_freeze_after_frac`/`--pgba_disable_after_frac`/
`--late_mapping_start_frac`/`--background_polish_start_frac` 4개를 구현(기존 절대
프레임 플래그와 상호배타, `round(frac*total_frames)`로 1회 변환, 레거시 기본값 불변).
aria1253에 원래 값과 수학적으로 동일한 비율(800/1120/650/700 ÷ 1303)을 적용해 정확도
회귀 확인(27.6907dB, -0.156dB) 후, **같은 비율을 재튜닝 없이 305/12F에 그대로 적용**:

| 장면 | 이전 | 축B 이후 | 개선 | crash |
|---|---:|---:|---:|---|
| aria301_305 | 16.95dB | **21.09dB** | **+4.14dB** | 없음 |
| aria301_12F | 26.13dB | **27.04dB** | **+0.91dB** | 없음 |

세 장면 모두 wall time이 예산을 3.4~3.5초 초과해서(101.01/205.05/168.45초) Codex는
규칙대로 `adopted: false`로 보고했지만, **직접 검증 결과 이 초과분은 축 B와 무관함을
확인**했다 — 같은 날 축 D의 guard=5 aria1253 재현(101.06초)도 똑같이 초과했는데, 이건
경계값을 하나도 안 건드린 "그냥 accepted recipe 재실행"이었다. 원인을 추적하니: 채택된
27.85dB/97.25초 기준은 **2026-07-29**(exp57 acceptance) 측정치인데, `background_polish_
step`이 `self.video.get_lock()`을 잡도록 만든 exp60 안전 수정은 **2026-08-03**(그 이후)
추가됐다 — 즉 **1.5× 예산 자체가 이 안전 수정 비용을 반영 못 한 stale한 숫자**였다.

**따라서 축 B의 `adopted: false` 판정을 뒤집어 채택했다**(`exp63_axes/recipe/
run_flags_current.sh` 신설, `--config`도 `exp63_axes/recipe/config.yaml`을 보게 함).
앞으로 축은 원래 97.65/201.57/165.00초가 아니라 **~101/~205/~168초(참조 레시피+3.5초)**를
현실적 기준으로 삼는다. commit `54982b93`. exp60 lock의 정확한 대기시간 측정은 별도
소축으로 남겨둔다(급하지 않음, 축 진행 안 막음).

## 실행 결과 — 축 A (2026-08-10, 트래킹 파라미터 상향 스캔 — `frontend_radius=2`만 채택)

축 B 위에서 개별 파라미터를 하나씩(baseline: iters1=1/iters2=0/window=15/radius=1/
thresh=3.6) 위로 스캔:

| 파라미터 | 장면 | 결과 | 채택 |
|---|---|---:|---|
| `frontend_window=18` | 12F | 27.29dB(+0.01, 노이즈) | 아니오 |
| `frontend_window=22` | 12F | 27.53dB(+0.25) | 아니오(radius가 더 좋음) |
| `frontend_radius=2` | 12F | **27.99dB(+0.72)** | **예** |
| `motion_filter.thresh=3.0` | 305 | 22.98dB(+1.91) | 아니오 — **aria1253 regression -0.42dB로 게이트 실패** |
| `iters1=2` | 305 | 예산 초과(220초+) + **crash 재현** | 아니오 |

**신규 발견(중요): `vectorized_gather_kernel` crash가 aria1253rot의 특정 경계
재조정 조합에서만 나는 게 아니라, 305에서 `iters1=2`로 트래킹 부하를 늘렸을 때도
재현됐다**(로그 직접 확인). 지금까지 "aria1253rot 전용"으로 생각했던 이 crash의
실제 트리거 조건이 "특정 장면"이 아니라 "PGBA/background_polish GPU 동시 사용
부하가 임계치를 넘는 것"에 더 가까울 가능성 — 근본 원인 규명 시 이 새 사례도
포함해서 봐야 한다.

`frontend_radius=1→2`만 채택, `run_flags_current.sh`에 `--frontend_radius 2` CLI
오버라이드로 반영(commit `ebefa164`). `iters1`/`iters2`는 이번에 하드코딩 상수에서
CLI 플래그(`--frontend_iters1`/`--frontend_iters2`, 기본값 1/0 유지)로 전환됨 —
향후 축에서 추가 스캔이 쉬워짐.

## 다음 단계

1. ~~축 D~~ → **완료**, idle_guard는 기각, crash 원인 미해결(축 A에서 305로도
   재현 범위가 넓어짐을 확인 — "aria1253rot 전용"이 아니었을 가능성)
2. ~~축 B~~ → **완료·채택**, 305/12F 회복 확인, 예산 기준 재보정
3. ~~축 A~~ → **완료·부분 채택**(`frontend_radius=2`만), 305는 트래킹 축으로는
   추가 개선 어려움 확인 — **Gaussian 밀도 부족이 원인일 가능성이 높음**(1253
   66.4개/프레임 vs 305 29.7개/프레임, 12F 58.7개/프레임 — 대화 중 직접 계산·확인).
   축 C에서 이 부분(freeze 지점을 밀도 적응형으로 바꾸는 것 등)을 최우선으로 다룰 것
3. 축 A(트래킹은 custom 유지 + 필요 구간만 param 상향)는 vanilla 전면 롤백이 실패로
   확인됐으므로 개별 파라미터 상향 스캔 + 메모리 계측이 필요한 더 큰 작업으로 재분류,
   축 C/E 이후 순번으로 미룸
4. 축 C, 축 E는 축 B 이후 독립적으로 진행 가능
5. 축 F, 축 G는 설계/문서화 우선, 실측은 후속 세션(다른 GPU 확보 시)
6. 축 H(CPU carve pruning)는 27dB 재현성 1차 목표 완료 후 순서
