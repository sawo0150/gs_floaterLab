# Online-GS benchmark code map

이 디렉터리는 과거 source lock 때문에 flat layout을 보존한다. 파일을 번호순으로
읽지 말고 아래 그룹에서 필요한 entry point만 찾는다.

## Core harness — 새 실험도 재사용

| 역할 | 파일 |
|---|---|
| frozen tracker archive | `exp78b_frozen_archive.py`, `exp78b_capture_frozen_tracker.py` |
| causal scheduler | `exp78b_timeline_scheduler.py` |
| custom mapper replay | `exp78b_replay_gsslam_mapping.py` |
| official vanilla replay | `exp78b_replay_vanilla_mapping.py` |
| fixed held-out evaluator | `exp78_evaluate_vigs_ply.py` |
| fairness verification | `verify_exp78b_d1_render_match.py` and `verify_exp78b_*` |

## Campaign entry points

| Campaign | Runner 범위 | 대표 entry point |
|---|---|---|
| BENCH | `run_exp78*`, `run_exp87*`–`run_exp94*` | `run_exp94_normalized_metric_v2_fixed_eval.py` |
| TOPO | `run_exp95*`–`run_exp110*`, `run_exp121*` | `run_exp109_first_persistence_panel.py` |
| DENSE | `run_exp111*`–`run_exp123*` | 각각 diagnostic 전용; final runner 없음 |
| ATTR | 이후 신규 코드 | `campaigns/gain_attribution/` 아래에 작성 |

## 활성/보존 구분

- **공식 main result 재현:** Exp94 runner와 그 source-locked dependency chain.
- **source-backed topology composition:** Exp109 runner.
- **진단 보존:** Exp95–108, 110–123. 다음 방법의 기본 runner로 복사하지 않는다.
- `run_exp94_repeat.sh` 등 untracked/local convenience 파일은 공식 entry point가
  아니며 source lock 근거로 사용하지 않는다.

앞으로 새 runner와 verifier는 `benchmarks/online_gs/campaigns/<campaign>/`에
두고, flat root에는 공용 harness만 둔다. 기존 파일은 import chain과 source hash를
보존하기 위해 이동하지 않는다.
