# Stage 6R-X4 source-neutral frozen-archive geometry-cache OOM repair

- 날짜: 2026-09-15
- 판정: **infrastructure repair PASS; X4 quality gate는 계속 OPEN**
- 영향 arm: R4 candidate와 native vanilla가 공통으로 사용하는 frozen archive reader
- method/config/gate 변경: **없음**

## 관측된 실패

Frozen R4 그대로 RPNG `table_03` candidate를 실행하던 중 causal dense RGB
415장 등록 뒤 mapper subprocess가 `SIGKILL(9)`로 끝났다. Python/CUDA 예외가
아니었으며 같은 시각의 kernel journal이 다음을 기록했다.

- OOM victim: `python`, PID 331414
- anonymous RSS: `25,640,424 kB`
- total virtual memory: `91,582,868 kB`
- kill 시각: `2026-09-15 11:19:35 KST`

실패 artifact는 덮어쓰지 않고 다음 위치로 이동해 보존했다.

`results/experiments/exp78/paper_full_staged_v1/stage6rx4_cross_sequence_confirmation/rpng/table_03/stage6rx4_r4_full_s0.failed_host_oom_20260915_111935/`

## 원인

`table_03` frozen tracker archive는 디스크에서 23 GB이며 614개 mapping/control
event에 geometry reference 29,900개, 서로 다른 reference 26,996개를 가진다.
PGBA는 같은 과거 keyframe에도 새 depth/normal snapshot을 만든다.

공통 `FrozenTrackerArchive` reader는 각 reference를 `_geometry_cache`에 영구
보존했다. 현재 mapping packet과 현재 `Camera`가 이미 필요한 tensor ownership을
가지는데도, 더 이상 쓰지 않는 과거 PGBA geometry까지 archive reader가 추가로
붙잡았다. 따라서 method의 causal dense pool보다 archive replay infrastructure의
구버전 geometry cache가 event history에 따라 무제한 성장한 것이 직접 원인이다.

## 수리와 비개입성

archive geometry cache만 32-entry LRU로 제한했다.

- cache eviction은 archive reader의 추가 reference만 해제한다.
- active mapping packet과 `Camera`가 가진 tensor는 그대로 유지된다.
- evicted item은 같은 immutable `.pt`에서 다시 읽으므로 tensor 값이 bit-exact다.
- causal arrival, mapping event, tracker pose/depth/normal, candidate pool, selection,
  Adam/render 수, RNG, R4 method flag와 vanilla work-matching rule은 바꾸지 않았다.
- candidate와 vanilla 모두 같은 reader를 사용한다.

단위 테스트는 LRU cardinality bound, active owner 생존, eviction 후 bit-exact
reload를 확인했고 2/2 통과했다. X4 runner test 9/9와 hash-pinned preflight도
통과했다. 이제 reader 자체 SHA-256도 runner provenance에 기록한다.

## Git checkpoints

1. `c0d79f4`: 실패 당시 untracked legacy reader를 byte-exact하게 먼저 보존
2. `03426c6`: 32-entry geometry LRU와 regression test
3. `5a210f8`: repaired reader hash를 X4 preflight/manifest에 pin

## X4 판정 영향

X4 계약은 source-neutral infrastructure repair가 실패 artifact를 모두 보존하고
별도 commit으로 이뤄질 때 실행을 재개하도록 허용한다. 이 수리는 quality를
보지 않고 OOM evidence만으로 결정했으며 frozen R4 값, cohort, threshold,
sequence role은 바꾸지 않았다. 따라서 기존 완료 pair는 보존하고 `table_03`
candidate를 canonical output에 처음부터 재실행한다. X4의 UTMM quality gate
미달과 `slow-straight-1` tracker-ineligible 실패도 그대로 유지한다.

