# gs_floaterLab Context

이 폴더는 raw result를 직접 뒤지지 않아도 현재 workspace의 상태와 실험 경과를 빠르게 파악하기 위한 agent handoff 문서이다.

## 현재 목적

- OpenMAVIS `301_1253` 결과를 입력으로 3D Gaussian Splatting을 학습한다.
- 목표는 render 품질을 유지하면서 floater를 줄이는 것이다.
- floater 원인을 density/pruning control, optimizer/LR, sparse point prior, camera/point-cloud source 관점에서 계속 가설 검증한다.

## 먼저 읽을 순서

1. [workspace_map.md](./workspace_map.md): repo, dataset, result, env 경로 지도.
2. [current_findings.md](./current_findings.md): 지금까지의 핵심 결론과 다음 실험 방향.
3. [experiment_timeline.md](./experiment_timeline.md): exp01부터 VGGT/EVO까지의 실험 흐름.
4. [repro_commands.md](./repro_commands.md): 주요 실험 재현 커맨드와 주의점.
5. [sparse_support_potential_field.md](./sparse_support_potential_field.md): photometric gradient 한계를 보완하기 위한 sparse support plateau / scalar potential field toy study.

## 가장 중요한 결론

- 현재 full 30k OpenMAVIS 기준 최고 후보는 `exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504`이다.
- exp08 설정은 `densification_interval=200`, `densify_grad_threshold=0.0004`, `densify_until_iter=7000`, `scaling_lr=0.0025`, `min_opacity_prune_threshold=0.01`, `optimizer_beta1=0.85`이다.
- 현재 구현한 sparse depth prior는 동작은 하지만 `0.01 -> 0.002` weight에서는 PSNR과 floater proxy가 악화됐다. 더 약하게 또는 더 늦게 켜야 한다.
- floater는 최소 두 종류로 보인다.
  - Pop1: SLAM sparse init outlier. camera-bound sparse point filtering으로 대부분 해결 가능.
  - Pop2: densification 이후 생기는 내부/근거리 floater. 아직 핵심 미해결 문제.
- VGGT 64 frame은 point cloud가 compact하지만 global camera trajectory가 OpenMAVIS보다 MPS 기준으로 나쁘고, 3DGS 7k render 품질도 OpenMAVIS64보다 낮았다.
- 새 연구축으로 sparse init map만 사용해 conservative support plateau와 single scalar potential field를 만드는 2D toy visualization을 추가했다.

## 최신 Toy 결과

Sparse support potential field 2D toy:

```text
script:  scripts/diagnostic/toy_sparse_support_potential.py
result:  results/diagnostic/toy_sparse_support_potential_20260704_182754
pdf:     results/diagnostic/toy_sparse_support_potential_20260704_182754/toy_sparse_support_potential_report.pdf
summary: results/diagnostic/toy_sparse_support_potential_20260704_182754/summary.json
```

기본 run에서는 synthetic sparse points 64개, camera ray segment 107개를 만들었다. Fixed `tau=0.28`의 plateau area fraction은 `0.1437`, adaptive `tau_j=0.82 h_j`의 plateau area fraction은 `0.2215`였고, ray coverage가 약하면서 potential이 active한 영역 비율은 `0.6772`였다.

## 관련 원본 문서

- W&B metric 설명: [`docs/wandb_metric_guide.md`](../docs/wandb_metric_guide.md)
- floater 실험 계획: [`docs/floater_experiment_plan.md`](../docs/floater_experiment_plan.md)
- Notion 정리용 실험 요약: [`docs/notion_experiment_summary_2026-06-16.md`](../docs/notion_experiment_summary_2026-06-16.md)
- diagnostic loop: [`docs/floater_diagnostic_loop.md`](../docs/floater_diagnostic_loop.md)
- round5 point-cloud filter 요약: [`docs/round5_findings_summary.md`](../docs/round5_findings_summary.md)
