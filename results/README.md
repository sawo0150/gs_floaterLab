# results/

| 폴더 | 내용 |
|---|---|
| `experiments/` | ★ 실험 결과 (expNN_이름_타임스탬프/ + 같은 이름 .log). 새 실험 출력은 반드시 여기 |
| `rounds/` | 진단 라운드 실행 결과 (round2 gradient, round5 pcd filter 등) |
| `diagnostic/` | 진단/시각화 산출물 (figures, PDF, plateau 앵커 .npy). **3dgs-custom configs가 anchor_path로 직접 참조하므로 경로 이동 금지** |
| `datasets/` | 파생 3DGS scene (vggt64/openmavis64 64-frame 비교용) |
| `logs/` | 배치 러너 로그 (run_seq, plateau_exps 등 여러 실험 묶음 로그) |
| `archive/` | 닫힌 축: VGGT smoke, EVO report, 64-frame 비교(exp13_vggt64/exp14), 초기 smoke, `failed_runs/`(중단·실패 run) |

## 규칙

- 실험 1개 = `experiments/` 아래 dir 1개 (+ 옆에 .log). W&B run name과 dir 이름을 맞춘다.
- 실패/중단된 run은 `archive/failed_runs/`로 옮긴다 (같은 이름 재실행과 혼동 방지 — read_psnr.py가 최신 dir를 집기 때문).
- 각 실험의 의미/결론은 여기가 아니라 `context/experiments/INDEX.md`에 기록한다.
