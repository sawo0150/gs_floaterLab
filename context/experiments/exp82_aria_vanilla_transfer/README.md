# exp82 — adopted strict recipe의 Aria 1253/305호 vanilla 전이

날짜: 2026-09-13
판정: **GO 2/2 — 두 장면 모두 original vanilla VIGS 대비 shared held-out +1dB 통과**

## 질문

UTMM 6-scene에서 채택한 동일 custom recipe가 추가 튜닝 없이 Aria `1253`과
`301_305`에서도 mapping 품질을 유지하는가? 사용자가 지정한 비교 기준은 과거 custom
freeze800이 아니라 **원본 vanilla VIGS-SLAM**이다.

## 비교 계약

- custom: `VIGS-SLAM-main-integration-20260828`, `main@8c094371`
  - `exp82_axes/run_aria_adopted_strict15x.sh`
  - `config/exp82_aria_adopted_rgb_only.yaml`
  - RGB-only loss(`alpha=1.0`, `lambda_dnormal=0`), frontend `15/1`, motion
    threshold `3.6`, replay 4-step/B1, `mapping_after_imu_init=0`, carve OFF.
  - `mapping_replay_keyframe_fraction=1.0`: RR optimizer가 뽑은 9,072/26,638
    view update는 전부 keyframe이었다. dense RGB는 causal pool에 등록됐지만 이 실험의
    optimizer supervision으로는 선택되지 않았다.
  - timestamp 순 RGB+IMU only, MPS 입력 0, fixed 1.5x, sensor EOS 뒤 update 0,
    후처리 최적화 0회. fixed evaluator view는 mapping supervision에서 제외했다.
- vanilla: 별도 worktree `VIGS-SLAM-vanilla-check`, `origin/main@22ffe24c`
  - 원본 Aria sensor 설정에 vanilla mapping/tracking 기본값(frontend `25/2`, motion
    threshold `2.4`, RGB+depth+normal)을 사용했다.
  - `--gsmapping --pure_online`; final BA와 26k color refinement는 실행하지 않았다.
  - vanilla에는 strict replay deadline이 없으므로 원본 synchronous/unbounded online
    loop를 끝까지 허용했다. 알고리즘에는 손대지 않고 종료 뒤 per-view metric을 남기는
    `VIGS_EVAL_PURE_ONLINE=1` 계측만 사용했다.
- 평가 집합: custom fixed `frame_idx % 5 == 0` + 마지막 frame에서 **vanilla가
  Gaussian mapping에 사용한 모든 keyframe을 양쪽에서 함께 제거**한 동일 frame 집합.
  PSNR은 per-view PSNR의 산술평균이다.
- seed: 각 조건 1회(`seed0`). GPU는 실행 직전 다른 compute process가 없음을 확인했다.

## 결과

| scene | frames | custom / vanilla KF | custom fixed PSNR | shared views | custom shared | vanilla shared | delta | +1dB |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `aria1253` | 1,303 | 114 / 128 | 23.8979 | 237 | **23.8940** | 22.1306 | **+1.7634** | PASS |
| `aria301_305` | 2,688 | 150 / 171 | 26.0532 | 501 | **26.0648** | 23.3254 | **+2.7395** | PASS |

두 장면 738-view 가중평균은 custom 25.3677dB, vanilla 22.9417dB,
**+2.4260dB**다. scene 평균 delta는 +2.2514dB다.

참고로 vanilla 자체 evaluator union(KF 포함)은 1253 22.1739dB, 305호
23.4245dB였다. 이 값은 학습 view가 섞여 있으므로 위 판정에는 사용하지 않았다.

## strict audit와 실행량

| scene | strict budget | custom Adam | map packet processed/dropped | after deadline | after EOS | vanilla wall incl. eval |
|---|---:|---:|---:|---:|---:|---:|
| `aria1253` | 97.6500s | 12,233 | 102 / 4 | 0 | 0 | 253.25s |
| `aria301_305` | 201.5250s | 34,578 | 142 / 0 | 0 | 0 | 362.47s |

305호에서 deadline guard가 Adam 호출 1회를 시작 전에 막았고, deadline/EOS 뒤 완료된
update는 없다. vanilla wall time에는 종료 뒤 렌더 평가가 포함되며 strict budget과 직접
동일한 정의는 아니다. 중요한 점은 비교상 더 많은 동기식 처리 시간을 허용한 vanilla보다도
custom shared held-out 품질이 높았다는 것이다.

## 해석과 한계

- 사용자 목표인 “대부분 scene에서 vanilla +1dB” 관점에서는 **두 추가 Aria scene 모두
  품질 유지/전이 성공**이다.
- 이 결과는 현재 채택 recipe의 Aria 전이를 지지하지만, **dense-frame scheduling의
  효과를 검증한 실험은 아니다**. 실제 RR draw는 dense 0회였다.
- 1253의 23.8979dB는 과거 scene-specific freeze800 strict 결과 27.84dB를 유지한 것이
  아니다. 비교 기준을 vanilla로 바꾼 현재 acceptance만 통과했다.
- 각 arm n=1이므로 작은 차이의 재현성을 말할 수는 없지만, 관측 margin
  +1.76/+2.74dB는 +1dB 기준을 모두 넘었다.

## 근거 파일

- 공통 held-out 집계:
  [`evidence/aria1253_shared.json`](evidence/aria1253_shared.json),
  [`evidence/aria301_305_shared.json`](evidence/aria301_305_shared.json),
  [`evidence/summary.json`](evidence/summary.json)
- custom outputs:
  `results/benchmarks/exp82_aria_adopted_strict15x/{aria1253,aria301_305}/seed0`
- vanilla outputs:
  `results/benchmarks/exp82_vigs_vanilla5070/{aria1253,aria301_305}/origin22ffe24_pytorch_seed0`
