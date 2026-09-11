# ERCB RPNG/UTMM handoff — 5070Ti

> 동기화/검증 시각: 2026-09-11 (Asia/Seoul)
>
> 이 문서는 새 exp 번호를 만들지 않는 `ERCB_ablation` 누적 트랙의 실행 handoff다.

## 동기화된 기준점

- `gs_floaterLab` 동기화 시작 기준 commit: `f178306` (이 handoff commit이 그 뒤에 추가됨)
- `3dgs-custom` GitHub/main 및 5070Ti main: `8568fd6`
- 5070Ti project root:
  `/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab`
- 5070Ti training repo:
  `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom`
- conda Python: `/home/wosas/miniconda3/envs/3dgs/bin/python`

`3dgs-custom/main`에는 기존의 `eval/carve_loss.py`, `train_incremental.py`,
submodule 및 config/output dirty 상태가 그대로 보존되어 있다. 이번 동기화는 이를
revert하거나 커밋하지 않고 main만 fast-forward했다. ERCB runner는 이 변경 파일들을
사용하지 않지만, 후속 agent도 임의로 정리하지 말아야 한다.

## 현재 판정 상태

기존 `evidence/runs/`의 12개 run은 미래 RGB ray로 만든 artificial colored scaffold를
쓴 1차 scheduler-isolation 결과다. compact 결과와 판정은 `README.md` 및
`evidence/representative_1000_summary.json`에 기록되어 있다.

그 뒤 Aria 1253/305와 같은 계열로 맞추기 위해 다음 고정 입력을 사용한 full replay를
준비했다.

- VIGS final-online full-frame pose
- 실제 VIGS keyframe timestamp interval
- VIGS cumulative geometry-only depth-anchor points
- gray `(128,128,128)` initialization, depth-anchor stride 40
- llffhold-8 held-out, 60 updates/event, zero-tail

이 replay도 최종 pose와 누적 point set을 처음부터 고정하므로 **strict incremental
mapping 결과는 아니다.** Scheduler만 causal growing-view pool에서 분리 비교하는
offline/noncausal fixed-pose/init ablation이다.

## 실패 기록과 수정

수정 전 RPNG replay의 첫 VIGS bootstrap keyframe은 RGB frame 0에 대응했는데, frame 0은
llffhold-8 held-out이었다. 그 결과 iteration 1에 eligible train view가 0개여서 RR run이
`IndexError: pop from empty list`로 즉시 종료됐다.

- 실패 산출물은 보존:
  `evidence/runs_vigs_replay/rpng_table01_full/`
- 수정 커밋 `8568fd6`: leading held-out-only keyframe boundary만 제거
- 수정 후 두 scene 모두 1-iteration RR smoke test 통과

수정 전 dataset은 덮어쓰지 않았다. 반드시 아래 `_v2` dataset을 사용한다.

| Scene | dataset | events | total updates | train/test | init points |
|---|---|---:|---:|---:|---:|
| RPNG table_01 | `data/benchmarks/ercb_vigs_replay_v2/rpng_table01_full` | 244 | 14,581 | 2,192 / 314 | 29,030 |
| UTMM square-1 | `data/benchmarks/ercb_vigs_replay_v2/utmm_square1_full` | 80 | 4,741 | 1,412 / 202 | 10,189 |

두 metadata 모두 `dropped_leading_heldout_only_boundaries: 1`이며, point/pose/KF SHA-256는
각 dataset의 `vigs_replay_metadata.json`에 있다.

## 다음 실행

GPU 사용 전 다른 compute process가 없는지 확인한다. 있으면 종료하지 말고 기다린다.
각 runner는 RR/normalized/relative-floor × seed 0/1의 6개 arm을 순차 실행하며 기존
경로가 있으면 덮어쓰지 않고 중단한다.

```bash
project=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
repo=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
python3dgs=/home/wosas/miniconda3/envs/3dgs/bin/python

cd "$repo"
nvidia-smi

PYTHON="$python3dgs" scripts/incremental/run_ercb_benchmark_ablation.sh \
  "$project/data/benchmarks/ercb_vigs_replay_v2/rpng_table01_full" \
  "$project/context/experiments/ERCB_ablation/evidence/runs_vigs_replay_v2/rpng_table01_full" \
  rpng_table01_full

PYTHON="$python3dgs" scripts/incremental/run_ercb_benchmark_ablation.sh \
  "$project/data/benchmarks/ercb_vigs_replay_v2/utmm_square1_full" \
  "$project/context/experiments/ERCB_ablation/evidence/runs_vigs_replay_v2/utmm_square1_full" \
  utmm_square1_full
```

완주 후 overall held-out PSNR뿐 아니라 worst-Q1, RR-hard-Q1, first/middle/late와 count CV를
함께 판정한다. 실패든 성공이든 `README.md`, `context/experiments/INDEX.md`,
`context/STATUS.md`에 append-only로 기록한다. 27dB 미만 결과에는 carve/pruning을 섞지
않는다.
