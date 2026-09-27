# Online GS benchmark

이 폴더의 현재 공식 진입점은 **exp94 B-track** 하나다. 나머지 파일은
그 진입점이 호출하는 하네스이거나 exp77--93의 재현·진단 기록이다. 과거 결과의
`source_lock.json`이 파일 경로와 SHA-256을 참조하므로 기존 파일은 이동하지 않는다.

## 지금 무엇을 실행해야 하나

| 목적 | 진입점 |
|---|---|
| 새 결과 폴더에서 전체 17-scene 비교 | `./benchmarks/online_gs/run_exp94_repeat.sh run-all <run_tag>` |
| 한 scene만 비교 | `./benchmarks/online_gs/run_exp94_repeat.sh run-one <run_tag> <dataset> <scene>` |
| GPU 실행 전 입력·source 검사 | `./benchmarks/online_gs/run_exp94_repeat.sh preflight <run_tag>` |
| 이미 보존된 exp94 결과 감사 | `python benchmarks/online_gs/audit_exp94_normalized_panel.py --root results/experiments/exp94_normalized_metric_v2_fixed_eval --require-complete` |

`run_tag`에는 `/` 없는 새 이름을 사용한다. 예:

```bash
./benchmarks/online_gs/run_exp94_repeat.sh preflight exp94_repeat_20260923
nvidia-smi
./benchmarks/online_gs/run_exp94_repeat.sh run-one \
  exp94_repeat_20260923 aria aria1253
```

`run_exp94_repeat.sh`는 현재 재실행 편의 wrapper다. 2026-09-17의 보존 결과를
만들 때 별도 shell script가 사용된 것은 아니며, 당시 byte-exact Python runner와
mapper 버전은 아래 문서와 `source_lock.json`을 기준으로 한다.

- 실행·버전·새 dataset 추가 절차:
  `/home/intern/VIGS-SLAM-paper-full/docs/EXP94_NORMALIZED_ERCB_B_TRACK.md`
- 공식 결과:
  `context/experiments/benchmark_custom/metric_benchmark_v2_fixed_eval_20260917/summary.md`
- 실행 파일 hash:
  `results/experiments/exp94_normalized_metric_v2_fixed_eval/source_lock.json`

## 현재 파이프라인

코드를 읽지 않고 현재 mapper의 packet별 scheduling, keyframe/intermediate 비율,
FRONTIER/BALANCED 상태 의미와 17-scene 실측을 보려면
[CURRENT_MAPPING_BEHAVIOR.md](CURRENT_MAPPING_BEHAVIOR.md)를 먼저 본다.

```text
run_exp94_normalized_metric_v2_fixed_eval.py
  ├─ frozen causal tracker archive 검사
  ├─ exp78b_replay_gsslam_mapping.py        custom/normalized ERCB
  ├─ exp78_evaluate_vigs_ply.py             saved map 2회 평가
  ├─ exp78b_replay_vanilla_mapping.py       동일 physical render 예산
  ├─ exp78_evaluate_vigs_ply.py             saved map 2회 평가
  └─ verify_exp78b_d1_render_match.py       fairness/zero-tail 검증
```

이 비교는 `time_scale=unbounded`인 **mapping-only fixed-work B-track**이다.
동시에 tracker와 mapper가 경쟁하는 strict live-time C-track 결과로 해석하지 않는다.

## 파일 역할

### 활성 진입점

- `run_exp94_repeat.sh`: 사람이 실행할 단일 wrapper
- `run_exp94_normalized_metric_v2_fixed_eval.py`: 최종 17-scene orchestration
- `audit_exp94_normalized_panel.py`: 완료 panel 독립 감사
- `test_exp94_*.py`: evaluator 위임과 normalized Gibbs 회귀 테스트

### 공용 하네스

- `exp78b_replay_gsslam_mapping.py`: custom mapper replay
- `exp78b_replay_vanilla_mapping.py`: official vanilla render-matched replay
- `exp78b_frozen_archive.py`: 공통 tracker archive reader
- `exp78b_capture_frozen_tracker.py`: 새 frozen tracker 입력 생성
- `validate_exp78b_frozen_tracker.py`: archive 인과성·hash 검증
- `exp78_evaluate_vigs_ply.py`: fixed held-out 렌더 평가
- `verify_exp78b_d1_render_match.py`: candidate/vanilla pair 검증
- `config/`: dataset family별 candidate/vanilla adapter 설정

### 역사적 runner

| 범위 | 의미 |
|---|---|
| `run_exp77*`, `run_exp78_reserve*`, `run_vigs_*` | 초기 streaming·zero-tail·reserve 실험 |
| `run_exp78a*`, `analyze_exp78a*` | official VIGS 논문 재현 |
| `run_exp78b_stage5*`, `stage6*`, `stage6r*` | R4/ERCB 단계별 방법론·공정성 실험 |
| `run_exp87*`--`run_exp89*` | normalized selector와 family isolation |
| `run_exp90*`--`run_exp93*`, `diagnose_exp9*` | evaluator 급락 원인 진단 |

역사적 runner를 새 공식 결과의 출발점으로 사용하지 않는다. 결과 재현을 위해
경로만 보존하며, 새 실험은 exp94 wrapper에서 시작한다.

## 새 파일 추가 규칙

- 공식 후속 runner는 `run_expNN_<purpose>.py` 하나를 진입점으로 둔다.
- 실험별 임시 shell script를 이 폴더 최상단에 추가하지 않는다.
- 공용 reader/evaluator/verifier는 `exp78b_*` 이름을 유지한다.
- 결과·PLY·로그는 `results/experiments/<run_tag>/`에만 둔다.
- 사람이 읽는 결과는 `context/experiments/benchmark_custom/<run_tag>/`에 둔다.
- 기존 보존 결과 root나 `source_lock.json`을 덮어쓰지 않는다.

## Dataset 준비 코드

`prepare_datasets.py`와 `prepared_datasets.json`은 초기 RPNG/UTMM 다운로드·CRC
준비 도구다. 현재 exp94 실행은 이미 준비된 frozen archive를 사용하므로 일반적인
재실행에서는 호출하지 않는다.
