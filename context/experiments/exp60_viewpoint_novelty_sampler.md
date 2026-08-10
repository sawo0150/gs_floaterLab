# exp60 — background polish에 viewpoint-novelty 기반 sampler 도입

- 상태: **완료 (2026-08-03) — novelty sampler 자체는 4장면 전부 중립~약간 부정적(기각),
  그러나 조사 과정에서 VIGS-SLAM의 진짜 pre-existing 버그 2개를 찾아 고쳤고, 그 결과
  4개 장면(aria1253/aria1253rot/aria301_305/aria301_12F) 전부에서 crash 없이 안정적으로
  완주하게 됐다.**
- 선행: [exp57](exp57_causal_background_polishing_plan.md)의 loss-priority/recent-newborn
  계열 targeting은 전부 uniform shuffled replay에 졌다. [exp59](exp59_strict27_cross_scene_transfer.md)
  진단 대화 중 사용자가 제기한 가설: **실패한 건 targeting 자체가 아니라 targeting 기준이
  잘못됐기 때문 아니냐** — PSNR/loss가 낮은 view를 우선하면 "어려운 view"만 반복 방문하게
  되어 실제 3D 기하 제약(삼각측량)에는 기여하지 못하고, 반면 새로운 baseline을 제공할 다른
  view의 기회비용만 커진다는 것.

## 근거 — 원래 계획엔 있었지만 한 번도 구현 안 된 항목

exp57 최초 계획(H2)의 sampler 공식:

```text
view_score = robust_residual × coverage_need × viewpoint_novelty × staleness × geometry_confidence
```

`viewpoint_novelty`/`geometry_confidence`는 문서 전체(4,100+줄)에서 이 최초 제안(H2) 한
곳에만 등장한다. 이후 실제로 시도된 loss-priority/recent5%/recent50% 계열은 전부
`robust_residual`/`staleness`류(현재 PSNR이 나쁜/최근에 태어난 곳)만 썼고, 기하학적
novelty 항목은 구현된 적이 없다.

## 가설

background dense view 선택을 "현재 PSNR이 나쁜 곳"이 아니라 "**현재 frontier window가
학습 중인 시점들과 카메라 중심 거리가 먼 곳**"으로 바꾸면, 매 step이 실제로 새로운
삼각측량 baseline을 제공하게 되어 uniform shuffled replay보다 더 효율적으로 품질을 올릴 수 있다.

## 구현

`vigs/gs_backend.py::background_polish_step`에 기존 `choose_priority`(loss-EMA 가중
샘플링)와 병렬한 `choose_novelty` 분기를 추가했다. `--background_polish_novelty_fraction`
확률로, 후보 view의 camera_center와 **현재 frontier window(`current_window`) 카메라
중심들 사이 최소 거리**를 점수로 써서 `background_rng.choices(candidates,
weights=novelty_scores)`로 하나를 뽑는다. `torch.cdist`로 후보×window 거리 행렬을 한 번에
계산해 추가 렌더/backward 없이 CPU 오버헤드만 든다. `choose_priority`와 상호 배타적(한
step에 하나만 적용)이며, `--background_polish_novelty_fraction 0`(기본값)이면 기존 동작과
완전히 동일하다.

- `demo.py`: `--background_polish_novelty_fraction`(0~1, 기본 0) 추가, `provenance.json`에
  기록, `--background_polish_random_sample` 필수 검증 추가.
- `gs_backend.py`: `_background_polish_novelty_fraction` 필드 + `background_polish_step`
  내부 `choose_novelty` 분기.
- 스모크 검증: aria1253 300-frame subset, `novelty_fraction=1.0`, `replay_time_scale=5.0`
  (유휴시간 강제 확보)로 background step 3,359회 정상 실행, 에러 없음.

## 계획된 A/B (aria1253, strict freeze800 recipe 그대로 + novelty_fraction만 추가)

| run | novelty_fraction | 비고 |
|---|---:|---|
| control | 0.0 | 기존 채택 recipe와 완전히 동일 (기준 27.8464dB, 2-run 평균) |
| treatment | 0.5 | exp57 loss-priority50(−0.0956dB)과 직접 비교 가능한 지점부터 시작 |

두 run 모두 나머지 플래그는 채택 recipe(freeze800/pre-IMU gate/append-birth/PGBA
cutoff1120/late-iters3/idle-guard0ms/shuffle-epoch)와 동일하게 유지한다.

## 결과

| run | novelty_fraction | fixed PSNR | SSIM/LPIPS | background step | 판정 |
|---|---:|---:|---|---:|---|
| control | 0.0 | **27.9499dB** | 0.8619/— | 6,237 | 기존 채택 recipe와 일치(기준 27.8464 평균 범위 내) |
| treatment | 0.5 | **27.6664dB** | 0.8576/0.2594 | 5,841 | **−0.2839dB** |

frame bin(fixed-eval만, 8구간):

| bin | control | treatment | Δ |
|---|---:|---:|---:|
| 0–156 | 29.329 | 28.546 | −0.78 |
| 156–313 | 30.524 | 30.328 | −0.20 |
| 313–469 | 29.934 | 30.288 | **+0.35** |
| 469–626 | 30.253 | 30.220 | −0.03 |
| 626–782 | 28.301 | 27.612 | −0.69 |
| 782–939 | 29.559 | 28.823 | −0.74 |
| 939–1095 | 24.922 | 24.754 | −0.17 |
| 1095–1252 | 21.045 | 21.056 | +0.01 |

두 run 모두 zero-tail/1.5× 계약을 통과했다(97.20s/97.25s 근방, 계측 별도 확인 생략).

### 해석

- **novelty_fraction=0.5도 exp57의 loss-priority50(−0.0956dB)과 같은 방향(악화)**이었고,
  악화 폭은 오히려 더 컸다(−0.284dB). 사용자 가설("targeting 기준이 잘못됐을 뿐, targeting
  자체는 유효할 것")을 이 구현으로는 지지하지 못했다.
- 가장 영향을 노렸던 마지막 bin(1095–1252, freeze 이후 구간)은 거의 무변화(+0.01dB)였다 —
  즉 이 novelty 정의는 freeze로 인한 post-freeze coverage 부족을 전혀 보완하지 못했다.
- background step 수가 6,237→5,841(−6.3%)로 줄었다 — candidate×window 거리행렬
  계산(`torch.cdist`) 오버헤드가 순수 처리량을 깎았을 가능성이 있고, 이 정도 step 손실은
  exp57에서도 대체로 비슷한 크기의 dB 손실과 연관됐었다. 즉 관측된 −0.284dB 중 일부는
  "novelty 기준이 나쁘다"보다 "오버헤드로 step이 줄었다"로 설명될 수 있다.
- **가능한 설계 결함**: 이번 점수는 "**현재 frontier window**와의 최소 거리"만 봤다.
  이건 순간적인 최근성 대비 novelty이지, 그 view가 **전체 시퀀스에 걸쳐 얼마나 적게
  관측/삼각측량됐는지**(누적 multi-view coverage)를 반영하지 않는다. 예를 들어 지도
  가장자리에 있는 한두 개의 "항상 frontier와 먼" view가 매 step 반복 선택돼 오히려
  shuffle_epoch의 "한 epoch에 한 번씩 전부 방문" 보장이 깨졌을 수 있다 — loss-priority가
  실패했던 것과 같은 coverage 희생 메커니즘일 가능성이 있다.

### 판정 (aria1253 1차)

1회 A/B로 유의미한 양성 신호는 없었다. 다만 결정적 반증도 아니다 — 특히 step 손실
confound를 제거하지 않았고, "window와의 순간 거리"가 아닌 "누적 관측 부족" 기준은 아직
테스트 안 됐다.

## 4장면 확장 중 발견한 2개의 pre-existing 버그

사용자 요청으로 같은 novelty sampler(0.5)를 aria1253rot/aria301_305/aria301_12F에도
그대로 적용했다. **aria1253rot에서 매번 재현되는 PGBA CUDA 크래시**
(`vectorized_gather_kernel index out of bounds`, exp59에서 이미 3회 목격)가 이번에도
났다 — 이번엔 근본 원인을 실제로 추적했다.

### 버그 1 — `update_pgba`가 `jj_inac` 하한 체크를 빠뜨림 (수정, 그러나 불충분)

`factor_graph.py`의 다른 두 call site(298, 352줄, 일반 local BA)는 inactive factor를
쓸 때 반드시 `m = (ii_inac >= t0-5) & (jj_inac >= t0-5)`로 **둘 다** 필터링한다. 그런데
`update_pgba`(467줄)는 필터 없이 `ii_inac`/`jj_inac`를 그대로 concat한다. `pgo_buffer.py`의
`_pgba()`도 `ii_inac`만 새 factor set(`kx`)에 속하는지 확인하고 `jj_inac`은 검사하지 않는다.
크래시 직전 계측(`CUDA_LAUNCH_BLOCKING=1` + `VIGS_PGBA_DEBUG=1`)으로 확인한 실제 값:

```text
ii_max=113 jj_max=113 ii_min=8 jj_min=8 t0=9 t1=113
disps_shape=(1200,58,58) intrinsics_shape=(1200,4)  <- 버퍼 자체는 안 넘침
lcii=[8,9,10,11,...] lcjj=[105,...,113]              <- 새 factor는 전부 정상
```

기존 코드베이스의 검증된 패턴을 그대로 `pgo_buffer.py::_pgba`에 적용해
`m = m & (jj_inac >= t0 - 5)`를 추가했다 — 실제 버그이고 합리적인 수정이지만,
**단독으로는 이 크래시를 해결하지 못했다**(재시도해도 거의 같은 지점에서 재현).

### 버그 2 — background_polish_step이 PGBA와 GPU 락을 공유하지 않음 (수정, 크래시 해결)

`self.video.get_lock()`(`multiprocessing.Value`의 락)은 PGBA의 `_pgba()`가 `update_pgba()`를
호출하는 동안 쥐고 있지만, `background_polish_step`은 이 락을 전혀 획득하지 않는다.
Python 객체 레벨(`_gaussian_lock`)은 각자 안전해도, **GPU 커널 자체는 두 스레드에서 동시에
큐잉/실행될 수 있다** — `mp_backend`(PGBA 전용 스레드, `vigs.py`에 "Run PGBA in a background
thread (same CUDA context)"라고 명시)와 `_gs_worker`(GS 매핑+background polish)가 같은
CUDA context를 공유하기 때문이다. `background_polish_step` 진입부에 `self.video.get_lock()`을
추가로 획득하도록 고쳐서(PGBA 실행 중엔 background polish가 대기) 두 GPU 작업을 직렬화했다.
**이 수정 이후 aria1253rot에서 동일 설정으로 크래시가 사라졌다.**

## 4장면 최종 결과 (두 버그 수정 반영, novelty_fraction=0.5 vs uniform)

| 장면 | control(uniform) | novelty=0.5 | Δ | 수정 전 상태 |
|---|---:|---:|---:|---|
| aria1253 | 27.9499 | 27.4875 | −0.462 | 크래시 없었음 |
| aria1253rot | 26.0001(exp59 기준) | 25.6480 | −0.352 | **3회 재현 크래시 → 수정 후 정상** |
| aria301_305 | 16.9497(exp59 기준) | 16.7798 | −0.170 | 크래시 없었음 |
| aria301_12F | 26.1338(exp59 기준) | 26.2155 | **+0.082** | 크래시 없었음 |

## 최종 판정

- **novelty sampler(현재 정의: frontier window와의 순간 거리) 자체는 4장면 평균
  약 −0.23dB로 uniform보다 낫지 않다.** aria1253/aria1253rot/aria301_305에서 소폭
  악화, aria301_12F에서만 미세하게 개선 — 명확한 양성 신호 없음. 사용자 가설
  ("targeting 기준이 잘못됐을 뿐 targeting 자체는 유효할 것")은 이 구현으로는
  검증되지 않았다. "누적 관측 부족" 기준으로 재정의하면 다를 수 있으나 미검증.
- **그러나 목표였던 "4장면에서 안정적으로 돌아가게 만들기"는 달성했다.** 이 과정에서
  찾은 GPU 락 버그(버그 2)는 novelty sampler와 무관하게 VIGS-SLAM의 background-polish
  아키텍처 전반에 존재하던 잠재적 위험이었을 가능성이 있다 — background_polish_step이
  뭔가 다른 이유로 GPU 작업 패턴이 달라지기만 해도(예: exp59 축 A의 rescale된 freeze
  경계) 같은 크래시가 재현됐던 것과 일치한다. 이 락 수정은 novelty sampler 없이도
  기본 freeze800 recipe의 안정성을 개선했을 가능성이 있으나, 그건 아직 별도로 검증하지
  않았다.

## 다음 후보

- 이 GPU 락 수정을 **novelty sampler 없이** exp59 축 A(경계값 rescale)에도 적용해서,
  그 크래시(축 C에서 미해결로 남았던 것)도 같이 해결되는지 확인 — 같은 근본 원인일
  가능성이 높다.
- novelty 점수를 "frontier window와의 순간 거리" 대신 "해당 view가 지금까지 얼마나
  적게 관측/사용됐는지"(누적 카운터) 기준으로 재정의해 재시도.
- 이 GPU 락이 background polish 처리량(step 수)에 미치는 영향을 정량화(PGBA가 자주
  도는 구간에서 처리량 저하가 있는지).
