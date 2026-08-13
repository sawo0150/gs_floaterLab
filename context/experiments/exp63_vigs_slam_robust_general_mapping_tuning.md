# exp63 — VIGS-SLAM 매핑 재튜닝: cross-scene·cross-GPU 강건화

- 상태: **crash 근본 원인 규명·수정 완료 (2026-08-10, 사용자 요청으로 Claude 직접 수행)** —
  `factor_graph.py::update_pgba`의 TOCTOU 버그 확정·수정. 305가 오늘 처음으로 crash 없이
  완주(22.82dB). 축 D+B+A+E도 완료(경계 비율화+frontend_radius=2 채택, 예산 재보정)
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

## 실행 결과 — crash 근본 원인 규명·수정 (2026-08-10, Claude 직접 수행)

사용자가 명시적으로 "Codex 말고 네가 직접 하라"고 요청. `vigs/geom/projective_ops.py`에
env var(`VIGS_DEBUG_PGBA_INDEX`, 평소엔 no-op)로 가드된 bounds-check 프로브를 심어
비동기 CUDA assert 대신 동기 Python 예외로 정확한 잘못된 인덱스 값을 잡아냄. 305에서
직접 재현해 `buffer_n=123(=t1) vs ii_max=131` 확보.

**근본 원인**: `factor_graph.py::update_pgba`가 `t1 = self.video.counter.value`를
`for step in range(steps):`(6회) 루프 **시작 전 딱 한 번만** 고정하는데, 루프 안의
`ii = torch.cat([self.ii_inac, self.ii], 0)`는 **매 step마다 새로 계산**됨 —
트래킹 프론트엔드가 동시에 새 keyframe/factor를 추가하면 `ii`가 `t1`보다 큰 인덱스를
참조하게 되고, `cuda_pgba`가 `t1` 기준으로 슬라이스한 `disps`/`poses`를 그 인덱스로
gather하면서 out-of-bounds. exp60이 고친 PGBA↔background_polish 동시성과는 별개의,
**PGBA↔트래킹 프론트엔드 자체의 TOCTOU 버그**. 305가 유독 잘 걸리는 이유는 keyframe
비율이 낮아(5.5%, exp59) 6-step 루프 도중 새 keyframe이 끼어들 타이밍이 더 잦았을
가능성.

**수정**: `cuda_pgba` 호출 직전 `ii`/`jj`를 `[0, t1)` 범위로 필터링(최소 침습). 걸러진
edge는 다음 PGBA 라운드에서 자연스럽게 처리되므로 정보 손실 없음.

**검증(둘 다 직접 실행)**: 305 — **오늘 처음으로 crash 없이 완주, 22.82dB, 205.05초**
(기존 축B의 21.09dB보다도 나음). 1253 — 27.80dB(채택 baseline 28.04dB 대비 -0.24dB,
0.3dB 게이트 통과), 101.37초. **트레이드오프 관측 안 됨.** commit `cdc699d0`.

**이걸로 축 D/A/E가 오늘 반복적으로 겪었던 "305만 유독 자주 죽는다"는 문제의 근본
원인이 해소됐다 — 이제부터의 305 실험은 이 crash에 막히지 않고 진행 가능.**

## 실행 결과 — 축 A2 (2026-08-10, 트래킹 파라미터 재상향 — 채택, 305 +7.00dB)

우선순위 재조정(1253 게이트 해제) 이후 `motion_filter.thresh`/`iters1`을 다시 스캔.
`frontend_radius=2`(축A) + 경계 비율화(축B) 위에서, `motion_filter.thresh=2.6`+
`frontend_iters1=2`(frontend_window=15/radius=2/iters2=0 유지) 조합이 305에서
**29.8154dB** — crash-fix 직후 기준(22.8154dB) 대비 **+7.00dB**, 최초 시작점(16.95dB)
대비 **+12.87dB**. 1253은 트렌드로만 봄(27.8059dB, 기존 대비 -0.04dB, 무시 가능).
onboard 타이밍/메모리 모두 기존 밴드 내. **채택**, `run_flags_current.sh` 갱신.
핵심 시사점: 305의 병목은 매핑 알고리즘이 아니라 **프론트엔드 트래킹 품질/keyframe
밀도**였다 — threshold를 낮춰 keyframe을 더 촘촘히 뽑고 iters1을 올리는 것만으로
거의 전체 격차가 좁혀짐.

## 실행 결과 — 축 C / C2 (2026-08-10, freeze 스펙트럼 양극단 테스트 — 둘 다 기각)

사용자 제안으로 "map()/PGBA를 끝까지 켜두기" 방향을 스펙트럼 양극단에서 테스트.

**축 C (map() 절대 freeze 안 함 + PGBA 계속 켬 + background_polish frame 700부터 +
polish_viewpoints 고정 크기 FIFO 2000)**: 305 24.896dB(축A2 대비 **-4.92dB**),
12F는 **CUDA OOM**(14.11GiB), 1253 24.804dB. **기각.**

12F OOM을 Claude가 직접 근본원인 추적(Codex에 위임하지 않음): 크래시 지점 자체는
작은(48-factor bound) frontend correlation graph의 `torch.cat`이지만, 진짜 원인은
**freeze가 유일한 학습 비용 상한선이었다는 것** — `map()`이 매 keyframe마다 현재
window+global view를 rasterizer로 forward/backward하는데, freeze 없이 시퀀스
끝까지(2201프레임) 이게 계속되고 가우시안 개수도 계속 커지면서 이 호출 자체의
순간 최대 메모리가 계속 늘어남. PyTorch 캐싱 allocator가 reserved 메모리를 반환
안 하니 하이워터마크가 계속 쌓여 15.46GiB를 넘김(크래시 시 7.05GiB allocated /
3.62GiB reserved-but-unallocated — 전형적 fragmentation 패턴). 축A/A2의 12F는
동일 가우시안 개수(~127k)에서도 freeze가 61% 지점에서 이 호출을 완전히 멈추므로
7.97GiB에 그침 — 즉 가우시안 개수 자체가 아니라 "freeze 없이 이 호출이 끝까지
반복된다"는 것이 원인.

**축 C2 (freeze를 초기화 직후로 최대한 당김 + PGBA 계속 켬 + background_polish
frame 0부터)**: 첫 `map()` init이 실제로 발동하는 프레임을 실측(305에서 **297**,
11-view window) — 애초에 IMU_poseinit_after=20 근처일 거라 추정했던 것보다 훨씬
늦음(사전 추정만으로 값을 정했으면 깨진 런이 나올 뻔함, 실측 검증 절차가 유효했음).
freeze=350/525/700 스윕 결과 305 PSNR이 17.88/18.88/**19.35dB**로 단조 증가하지만
최선값(700)도 축A2(29.815dB) 대비 **-10.46dB**의 심각한 회귀. background_polish는
frame 0부터 10000 step 풀가동(view_updates=10000 확인, 조용히 안 돈 게 아님)했지만
구조적 학습(densify/prune) 중단을 보완하지 못함. 12F는 OOM 없이 완주(24.996dB) —
메모리 가설은 맞았음. **기각.**

**종합**: freeze 시점 스펙트럼에서 세 지점을 확보 — 즉시 freeze(700, 19.35dB) <
never freeze(24.896dB) < **축A2의 61% freeze(29.815dB, 현재 채택 상태)**. 즉
**이미 채택된 A2 레시피의 freeze 지점이 이미 근처 최적**이고, 두 극단(즉시/영구
안 함) 모두 이보다 나쁨. 12F OOM은 "map()을 절대 freeze 안 함" 극단에서만 발생하는
문제였고 그 극단은 이미 기각됐으므로, **현재 채택된 레시피(A2)에는 이 OOM이 존재하지
않는다** — 축A의 12F 실측(7.97GiB, no OOM)이 이를 뒷받침. freeze 시점 축은 더 이상
파고들 이유가 없어 보임(A2가 이미 좋은 지점을 찾음); PGBA-always-on 자체는 305/1253
양쪽에서 문제를 일으키지 않았으므로 위험한 요소는 아니었던 것으로 보임.

## 실행 결과 — 축 PF (2026-08-10, 폴리시 후보에 일반 keyframe 추가 — 기각, 오히려 소폭 악화)

`background_polish_step`이 `--background_polish_dense_only`로 `sensor_type=="rgb_dense"`
(별도 stride-5 raw 프레임)만 보고, birth를 만든 그 keyframe 자체(`self.viewpoints`,
`sensor_type="rgb"`)는 window에서 밀려나도 절대 폴리시 대상이 안 된다는 걸 코드 추적으로
확인(Claude, 직접 조사) — 이게 축C2(즉시 freeze, 19.35dB)가 유독 나빴던 이유의 일부일
거라는 가설로, opt-in 플래그(`--background_polish_include_tracked_keyframes`, 기본
off)를 추가해 즉시freeze/기존스케줄 두 조건에서 대조 테스트.

**결과는 가설과 반대**: 즉시freeze+수정 **18.775dB**(수정 전 C2 19.354dB 대비
**-0.579dB**, gap_closed **-5.53%**), 기존스케줄(61%)+수정 **29.539dB**(A2 29.815dB
대비 **-0.276dB**). 둘 다 여전히 폴리시 10000-step 캡을 다 채웠음(=선택 기회 자체는
충분했음). 12F는 OOM 없이 완주(24.635dB, driver peak 15.07GiB — C2의 14.15GiB보다
약간 높지만 안전 마진 안).

**해석**: 후보 자격을 열어줬는데 선택은 여전히 균등 랜덤이라, 기존에 효과적이던
rgb_dense 뷰에 가던 관심이 새로 늘어난(수천 개) tracked keyframe 후보로 희석된 것으로
보임 — polish 전 세션에서 미리 예측했던 "dilution" 리스크가 실측으로 확인됨. **폴리시
후보를 무작정 넓히는 방향은 기각** — 대신 사용자가 제안한 "폴리시가 보는 후보를 아예
작은 trailing window로 제한"(균등 랜덤이어도 풀이 작으면 자연히 새 후보가 자주 뽑힘)이
다음 시도로 더 유망함. `--background_polish_include_tracked_keyframes` 플래그 자체는
opt-in으로 남겨둠(기본 off, `run_flags_current.sh` 불변).

## 다음 단계

1. ~~축 D~~ → **완료**, idle_guard는 기각(crash 원인 아니었음 — 진짜 원인은 위에서 규명·수정)
2. ~~축 B~~ → **완료·채택**, 305/12F 회복 확인, 예산 기준 재보정
3. ~~축 A~~ → **완료·부분 채택**(`frontend_radius=2`만) — 305 잔여 격차는 Gaussian 밀도
   부족으로 추정(1253 66.4개/프레임 vs 305 29.7개/프레임 vs 12F 58.7개/프레임)
4. ~~축 E~~ → **완료** — 해상도 다운샘플링(464→256) 메커니즘은 정상이지만 1253에서
   속도 이득 거의 없음(101.14→101.02초)·품질도 소폭 하락(-0.33dB) — OKVIS2 트랙(1024→256,
   16배 축소)과 달리 VIGS-SLAM은 native가 이미 464라 3.3배 축소뿐이고, exp56이 밝힌 대로
   커널 launch 고정비가 지배적이라 픽셀 수 감소 효과가 작음. 305는 crash 때문에 미검증 —
   지금 crash가 고쳐졌으니 재시도 가치 있음(우선순위는 낮음, 기대치 낮춰서)
5. ~~crash 근본 원인~~ → **완료**(위 참조)
6. **우선순위 재조정 (2026-08-10, 사용자 명시적 지시)**: **aria1253은 더 이상 회귀
   게이트가 아님.** 앞으로는 (a) 305 품질/강건성에 도움이 되는지 (b) 트래킹 품질/강건성을
   전반적으로 높이는지만 본다. 1253이 나빠지는 건 허용·예상된 일. zero-tail만 계속 필수
   (strict streaming 규약 자체라서). 이로 인해 축A의 `motion_filter.thresh=3.0`(305
   +1.91dB, 1253 회귀만으로 기각됐던 것)이 재검토 대상으로 부활. **축 A2로 착수**
   (`frontend_radius=2`와 결합 재테스트 + 추가 상향 스캔).
7. ~~축 A2~~ → **완료·채택**. `motion_filter.thresh=2.6`+`iters1=2` 스택으로 305
   **29.8154dB**(+7.00dB). 위 "실행 결과 — 축 A2" 참조.
8. ~~축 C~~ → **완료·기각**(305 -4.92dB, 12F OOM). ~~축 C2~~ → **완료·기각**(305
   -10.46dB, 12F는 완주). freeze-always-on/freeze-immediate 양극단 모두 A2보다 나쁨 —
   위 "실행 결과 — 축 C / C2" 참조. **이 freeze-시점 축은 여기서 종결**: A2가 이미 세
   지점 중 최선이고, `background_polish`의 `polish_viewpoints` FIFO(축C에서 구현,
   opt-in `--background_polish_max_pool_size`)는 남겨두되 기본 비활성 상태 유지.
9. 축 F, 축 G는 설계/문서화 우선, 실측은 후속 세션(다른 GPU 확보 시)
10. 축 H(CPU carve pruning)는 27dB 재현성 1차 목표 완료 후 순서
11. **다음 열린 질문**: A2가 305를 29.82dB까지 끌어올렸으니, strict streaming 27dB
    마일스톤 자체는 305/1253 양쪽에서 이미 재현 가능해 보임(1253 27.81dB, 305
    29.82dB) — 다음은 이 A2 레시피가 12F를 포함한 다른 장면에서도 안정적인지, 그리고
    STATUS.md의 27dB 마일스톤 수락 기준(고정 1.5x 라이브 예산 + zero-tail)을 A2
    레시피로 재확인하는 것.

## 실행 결과 — 축A2의 12F 미검증 회귀 발견 + 팀원 3090 재현 조사 (2026-08-11)

**A2가 12F에서 한 번도 검증 안 된 채로 방치돼 있었음을 발견.** HEAD 기준(`run_flags_current.sh`)
12F를 처음으로 실측: **23.153dB** — A2 이전(축A, thresh=3.6/iters1=1) 기준값 **27.993dB**
대비 **-4.84dB 회귀**. 원인은 `background_polish` step 수 붕괴: 6,586(축A) → **772(A2,
-88%)**. A2의 촘촘한 keyframe 설정(thresh 2.6, iters1=2)이 12F에서 298→352개로 keyframe을
늘리면서 tracking/mapping 스레드가 더 오래 바빠졌고, `_gs_queue`가 빌 때만 도는
`background_polish`가 돌 idle 시간 자체가 사라짐. **12F는 원래(sparse 설정) 이미 keyframe
밀도가 충분했던 장면(58.7개/프레임 vs 305의 29.7개/프레임)이라, 촘촘하게 뽑아주는 "이득"
없이 "polish 굶주림" 손해만 봄** — 같은 다이얼이 305(부족했던 장면)에는 크게 도움, 12F
(충분했던 장면)에는 순손해라는 게 핵심 패턴. `exp63_axes/recipe/README.md`/`DECISIONS.md`에
GPU 모델(RTX 5070 Ti, env 이름 `vigs-slam-5090`은 오해 소지 있음 — 실제 하드웨어 아님) 명기,
HEAD 기준 3장면 기대값을 `exp63_axes/verify/HEAD_reference_results/`에 작은 provenance
파일(run.log/input_provenance.json/final_result.json)로 고정.

**팀원(martian35) 3090 재현 시도 -5.2dB 격차 규명**: (1) `data/aria1253` 변환 규칙이
문서화 안 돼 있었음 — `scripts/incremental/build_vigs_aria_input.py`에 `--skip-head N`
인자 추가(1253=8프레임 skip, 305/12F=0, 전부 실측 검증). VIGS-SLAM repo에도
`scripts/build_vigs_aria_input.py`로 복사해 반영. (2) 최종 원인은 데이터가 아니라
**fixed 1.5x wall-clock 예산 + 3090의 낮은 처리 속도**(같은 정확 데이터로 132s vs 101s,
1.31배) — 느린 GPU는 같은 고정 예산 안에서 `background_polish` step을 덜 받음(같은
메커니즘, 12F 회귀와 동일 근본원인). `gaussian_reset`(opacity 주기 리셋)은
`config.yaml`에서 2e9로 사실상 비활성 확인(팀원이 제기한 "opacity reset phase" confound는
우리 쪽엔 해당 없음).

**부수 조사 — DROID-dense vs OKVIS2 init 수렴속도 비교** (`3dgs-custom`/`train_incremental.py`,
같은 학습 루프에 초기 point cloud만 교체): 단일 keyframe에서 DROID(5,981pt, correlation
depth)가 OKVIS2-sparse(184pt)보다 최대 16배 빠르게 수렴, OKVIS2+PPM(4,000pt, 단안 depth
network)은 초반엔 DROID급이지만 최종 수렴 상한이 더 낮음(-2.96dB). 141-keyframe 전체
시퀀스 확장은 PGBA pose 보정 미반영(방법론 결함, 단일 keyframe 실험은 이 결함에서 자유로움)
으로 후반부 신뢰도 낮음 — 초반 구간(drift 전)만 보면 DROID≈OKVIS+PPM(32.2 vs 32.1dB)
>> OKVIS-sparse(27.7dB) 패턴 유지. 이 실험은 별도 repo(`3dgs-custom`, `okvis2_bench_5070ti`)
에서 진행, 세부 방법론은 해당 세션 기록 참조 — VIGS-SLAM 쪽 결론에 직접 적용되진 않지만
"densify가 sparse init 격차를 결국 메운다"는 발견은 아래 다음 단계 설계에 참고됨.

## 다음 단계 (2026-08-11, 사용자 지정 4개 방향 + 계측 인프라 정비 우선)

사용자가 명시한 4개 방향, 근본은 전부 **"제한된 실시간 예산을 구조 생성(tracking/PGBA/map())과
정제(background_polish/carve)에 어떻게 나누는가"**라는 같은 문제의 다른 얼굴:

1. **Frontier freeze 기준 재정립** — 지금은 `mapping_freeze_after_frac` 고정 비율(0.6140),
   1253/305 튜닝값일 뿐 원리적 근거 없음. 12F 회귀가 직접 반례. 후보 신호: (a) 죽어있는
   `gs_backend.py:2778-2782`의 `render_for_mask`가 계산만 하고 안 쓰는 `transmittance`
   (coverage 신호) (b) `densify_and_prune`의 `xyz_gradient_accum` 추세(densify rate 감소)
   (c) view_loss plateau(단, online이라 새 데이터가 계속 들어와 완전 plateau는 안 될 수
   있음 — "느려짐" 기준으로 잡아야 함).
2. **Density/pruning을 carve loss로** — 배치 트랙에서 이미 검증(exp44d2, 33.8dB, floater
   억제 확정). CLAUDE.md 제약: "27dB 미달 지도에 hard carve를 먼저 넣지 않는다" — 지금
   1253/305는 넘겼지만 **12F는 재튜닝 필요라 아직 3장면 다 안정 전**. evidence field 입력은
   VIGS에 별도 sparse feature map이 없어 `_export_depth_anchors`(exp55에서 이미 "SLAM
   anchor 대체재"로 검증됨) 방식 재사용 후보. "carve loss로 한다"가 densify_and_prune을
   대체하는 건지 추가 항으로 얹는 건지(배치는 후자) 구체화 필요.
3. **Tracking/mapping 예산을 데이터셋 무관하게 robust히 확보** — 근본 메커니즘 확인 완료:
   `track_frontend.py`의 `for itr in range(self.iters1): ...`가 시간 체크 없는 고정 루프,
   `vigs.py`의 gs_worker는 `_gs_queue`가 빌 때만 polish 시도. A2(12F -4.84dB, polish
   6586→772 -88%)가 실측 증거. 설계 후보: (a) tracking에 soft 시간 캡(수렴 조건 결합,
   무작정 자르면 pose 정확도 자체가 훼손될 위험) (b) polish에 최소 하한(floor) 보장.
   1253+305+12F **세 장면 교차검증 필수**(A2가 정확히 두 장면만 보고 실패한 패턴 반복 금지).
4. **Map() freeze 스케줄 — iter 기준이 아닌 robust한 방법론** — 1번과 본질적으로 동일 문제.

**계측 인프라 우선 정비 (실험 전에 먼저 할 것)**: 기존에 이미 있지만 이번 세션 내내
한 번도 안 켠 `VIGS_TIMING_LOG` env var(`vigs.py::_timed`, `gs_backend.py::_Sect`)가
`motion_filter`/`frontend`/`pgba_run`/`pgba_call_gs`/`gs_mapping`/`map_call`(섹션별,
`iters=`/`n_view=`/`n_gauss=` 컨텍스트 포함)을 이미 CSV로 기록 가능. **없는 것**:
`background_polish_step`(`gs_backend.py:1216-2121`) 내부에 타이밍 계측이 전혀 없음 —
step당 wall time, gaussian 수/scope에 따른 스케일링을 전혀 모름(12F의 "폴리시 772 step이
idle 부족 때문인지 step 자체가 느려서인지" 구분 불가한 이유). 제안 순서: (1) 기존 로그
켜고 A2 전/후×3장면 재분석 (2) `background_polish_step`에 `_Sect` 계측 추가 (3) 타임라인
재구성 스크립트(어느 순간 GPU를 누가 쓰고 있었는지) (4) 통제된 파라미터 스윕으로 스케일링
법칙 확정(`frontend 시간 = a + b×iters1` 같은 실제 함수형). 시각 자료:
`context/ppt/ppt0812/`.

## 실행 결과 — 계측 인프라 정비 1·2단계 실측 완료 (2026-08-12)

**(1) 기존 `VIGS_TIMING_LOG` 재분석**: 4개 런(12F pre-A2 thresh3.6/iters1=1, 12F A2
thresh2.6/iters1=2 ×2회 재현, 305 A2) 실행. VIGS-SLAM repo
`exp63_axes/verify/timing_logs/{12F_preA2,12F_A2,12F_A2_v2,305_A2}.csv` +
`analyze_timing.py`(신규 분석 스크립트, 같은 폴더).

| | 12F pre-A2 | 12F A2 | 305 A2 |
|---|---:|---:|---:|
| frontend 총합/비중 | 41.49s (63.6%) | 88.9~90.2s (73.4%) | 45.43s (64.0%) |
| motion_filter 비중 | 32.2% | 24.6% | 30.1% |
| gs_mapping(디스패치) 비중 | 3.7% | 1.7% | 1.2% |
| background_polish 호출 수 | 5,683 | 772~822 | 9,866 |
| polish call당 평균 | 4.66ms | 6.37ms | 3.86ms |
| PSNR(참고) | 27.99dB | 23.15dB | 29.82dB |

**핵심 발견 1 — frontend가 프레임 단계 시간의 64~73%로 압도적 지배.** `map()` 디스패치
(`gs_mapping`) 자체는 1.2~3.7%뿐 — 트래킹 쪽이 실시간 예산의 대부분을 이미 쓰고 있음.
같은 A2 설정에서도 12F(88.9s)가 305(45.43s)보다 frontend 절대시간이 약 2배 — 12F가
같은 파라미터로도 keyframe을 훨씬 많이 뽑기 때문(축A 시절 실측 밀도 차이와 정합).
iters1 1→2(변경은 이거 하나지만 keyframe 수도 같이 늘어남, thresh도 동시에 바뀜)에서
12F frontend는 41.49→88.9s로 **×2.17** — 순수 iters1 배로만 설명 안 되는 초선형 증가로,
keyframe 수 증가(298→352)와 iters1 자체 효과가 섞여있다(분리하려면 통제 스윕 필요, 미완).

**핵심 발견 2 — background_polish는 "느려진 게" 아니라 "기회가 없었다".** call당 비용은
gaussian 수(40k~150k) 전체에 걸쳐 3.9~6.4ms로 거의 고정(약한 n_gauss 의존성은 있으나
1.5배 수준). 반면 실행 **횟수**는 772~9,866으로 **최대 13배** 차이 — 즉 12F의 폴리시
붕괴(6,586→772, 별도 기록된 축A2 대조)는 전적으로 idle 기회 부족이지 step 자체의 저하가
아님이 확정됨. **(2) `background_polish_step` 신규 계측**: `gs_backend.py`의 render 직전
(~line 1607 이후)/`return True` 직전(~line 2099)에 `_Sect`와 동일한 패턴으로 wall time을
`n_gauss`/`scope`/`batch_size`/`n_views` 컨텍스트와 함께 `background_polish_call,total,...`
로 기록하도록 추가(env var 게이트, 기존 `_timing_fh` 재사용이라 부작용 없음).

**핵심 발견 3(부수) — map() 내부 구성은 두 씬이 거의 동일.** `loss_compute`+`backward`가
12F/305 둘 다 ~90%(각각 50.3%/40.2%, 45.0%/45.2%), `rasterize`는 ~7~8%뿐. 즉 map()
호출 자체의 내부 비용 구조는 씬 무관하게 일정 — 12F 저하 원인은 map() **안**이 아니라
map()이 호출되기 **전** 단계(frontend가 얼마나 자주·오래 도는가)에 있다는 게 재확인됨.
(참고: 이 비중은 exp56/ppt0727에서 측정된 "rasterize 40%+backward 34%+loss 24%"와
다른 씬·config라 직접 비교 불가 — 그때는 rasterize가 더 컸는데 이번엔 loss_compute가
가장 크다. 씬/해상도/파이프라인 버전에 따라 구성비 자체가 달라질 수 있음을 보여주는
사례로 기록.)

**아직 안 된 것(3·4단계, 이후 절에서 3단계는 부분 완료)**: 3장면 동시 통제 파라미터
스윕(`frontend 시간 = a + b×iters1` 같은 함수형 확정)은 미완 — iters1 1↔2 한 쌍만
확보됨(1253은 이번 라운드에서 미측정).

## 실행 결과 — `replay_time_scale` 스윕 + polish "양자화" 근본원인 규명 (2026-08-12)

사용자 요청: (1) `--replay_time_scale`(현재 1.5)을 늘려가며 12F에서 실험 (2)
background_polish 실행 횟수가 "양자화된 느낌"이 드는 이유를 정밀 로깅으로 분석.

**신규 계측**: `vigs.py::_gs_worker`의 `process_track_data` 호출 직전/직후(`gs_worker_dispatch`
태그, wall-clock epoch 포함)와 `background_polish_call` 로그에 epoch timestamp를 추가해,
두 이벤트 스트림을 시간축으로 직접 상관분석할 수 있게 함. `--strict_aria_online`은
`replay_time_scale==1.5`를 강제하는 순수 검증(assertion)일 뿐 동작을 안 바꾸는 걸
`demo.py` 코드로 확인 후 이 스윕에서만 제외(`exp63_axes/verify/timing_logs/run_scale_sweep.sh`,
신규, 나머지 플래그는 `run_flags_current.sh`와 동일).

**스윕 결과 (aria301_12F, A2 파라미터 고정, scale만 변경)**:

| scale | polish 횟수 | zero-polish gap 비율 | gap 평균/최대(ms) | PSNR |
|---:|---:|---:|---:|---:|
| 1.5 (재현) | 806 | 43% | 211/526 | 23.84dB |
| **2.0** | 5,681 | 46% | 302/1582 | **28.10dB (최고, pre-A2 기준치 27.99dB 상회)** |
| 3.0 | 10,000(캡 도달) | 57% | 624/2478 | 25.97dB |

**발견 1 — scale을 1.5→2.0(+33%)만 늘려도 12F 회귀가 거의 완전히 회복된다**(23.84→28.10dB).
polish 횟수는 806→5,681로 7배. frontend 총 wall time은 scale과 무관하게 거의 고정
(88.9s대)이므로, scale이 늘어난 만큼 생기는 여유시간 전부가 사실상 polish 몫으로
돌아간다 — 예산 캡(tracking 예산 상한)을 굳이 새로 설계하지 않아도, 이 씬에 한해서는
"조금 더 느슨한 real-time 배수"만으로 문제가 해소됨을 보여주는 유용한 대안 데이터.

**발견 2 — 그러나 단조 증가가 아니다(역-U자형).** scale 3.0에서는 polish가 상한
(`--background_polish_max_steps 10000`)까지 가득 찼는데도 PSNR은 25.97dB로 오히려
scale 2.0보다 낮음. 유력한 설명(미확정 가설): polish가 학습하는 `rgb_dense` 후보 풀은
`--background_dense_stride 5`로 고정된 좁은 집합이라, 같은 풀에 과도하게(10,000회)
반복 학습하면 그 특정 뷰들에 과적합되어 held-out 일반화가 오히려 나빠질 수 있음 —
축PF에서 확인한 "후보를 넓혀도 균등랜덤 선택이라 도움 안 됨"과 같은 뿌리(다양성 문제)로
보임. 정밀 검증하려면 held-out 세트를 후보 풀과 완전히 분리해 다시 재는 게 필요(미완).

**발견 3 — "양자화 느낌"의 정확한 메커니즘.** `gs_worker_dispatch`(worker 스레드가
`process_track_data`를 처리 중이던 구간)와 `background_polish_call`의 epoch timestamp를
직접 상관분석: keyframe 디스패치 사이 gap이 266~321개 있는데, 이 중 **43~57%는 polish
step 하나(약 4~6ms)도 못 낄 만큼 짧다.** 총 polish 횟수는 "각 gap 길이 ÷ step 비용의
정수 몫"을 모든 gap에 대해 더한 값이라 **본질적으로 정수 나눗셈들의 합**이고, 이게
"양자화된 느낌"의 정체다. scale이 커질수록 gap **개수** 자체는 완만히 증가하지만(267→
300→322, dispatch 자체가 real-time 무관한 keyframe 선택 로직이라 크게 안 변함), gap
**길이**가 초선형으로 늘어나(최대 526→1582→2478ms) 소수의 긴 gap이 압도적으로 많은
step을 흡수 — 즉 "many small quantized contributions, dominated by a few long tails"
구조. 분석 코드: 이번 세션에서 임시로 작성한 인라인 스크립트(커밋 안 됨, 재현 시
`gs_worker_dispatch`/`background_polish_call` 태그를 epoch 기준으로 정렬해 인접
dispatch 쌍 사이 polish 개수를 세면 됨).

**시각화**: `context/ppt/ppt0812/`에 이 스윕·역-U자형·gap 분석 결과 반영(신규 슬라이드).

**시각화**: `context/ppt/ppt0812/vigs_budget_briefing_0812.pptx`(13슬라이드로 확장,
`fig_frontend_scaling`/`fig_polish_opportunity`/`fig_map_breakdown` 3개 신규 실측
차트 추가, 기존 계획 슬라이드는 "완료" 상태로 갱신).
