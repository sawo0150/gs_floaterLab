# Agent Handoff

## 현재 상태 한 줄 요약

OpenMAVIS full 1311-frame 3DGS에서 exp08이 현재 best이며, sparse init outlier는 상당히 진단됐지만 densification 이후 생기는 내부 floater가 아직 주 문제다.

## 다음 agent가 바로 해야 할 일

1. `context/README.md`부터 읽는다.
2. `3dgs-custom` worktree를 확인하되, dirty changes를 revert하지 않는다.
3. 새 실험을 시작하기 전에 `docs/round5_findings_summary.md`와 `docs/floater_diagnostic_loop.md`를 읽어 Pop1/Pop2 구분을 유지한다.
4. 실험은 W&B run name과 result dir 이름을 반드시 맞춘다.
5. raw result를 만들면 이 `context/` 문서 중 관련 파일을 업데이트한다.

## 우선순위 높은 다음 실험

### A0. Sparse support potential toy 확장

가설:

- photometric gradient가 약한 Gaussian에도 sparse init map 기반 scalar potential이 conservative한 spatial guidance를 줄 수 있다.
- 단, plateau 내부 gradient를 0으로 둬야 photometric optimization을 방해하지 않는다.

현재 시작점:

```text
context/sparse_support_potential_field.md
scripts/diagnostic/toy_sparse_support_potential.py
results/diagnostic/toy_sparse_support_potential_20260704_182754/toy_sparse_support_potential_report.pdf
```

다음 확장:

- synthetic 2D에서 outlier sparse point 제거 전/후 plateau 비교.
- 실제 OpenMAVIS sparse map을 2D plane으로 projection해서 same plot 생성.
- Gaussian center dynamics에 photometric gradient proxy를 섞어 potential이 언제 방해되는지 확인.
- adaptive `tau_j`를 local spacing뿐 아니라 observation count/ray angle로 조절.

### A. Pop2 densification floater 제어

가설:

- Pop1 sparse init outlier를 제거해도 densification이 ambiguity 높은 영역에서 새 floater를 만든다.

실험 방향:

- ambiguity positive region에서 densification score를 낮추거나 densification을 skip한다.
- large-scale/low-opacity Gaussian의 pruning threshold를 training phase별로 다르게 둔다.
- `densify_until_iter=7000`보다 더 짧은 schedule과 더 긴 schedule을 각각 비교한다.

판단 metric:

- PSNR/SSIM/LPIPS
- `ambiguity/positive_ratio`
- `gaussian/large_scale_ratio`
- `gaussian/low_opacity_ratio`
- visual render fixed view
- FOV 내부 Z/scale outlier count

### B. Sparse prior 재설계

가설:

- sparse prior 자체가 나쁜 것이 아니라, outlier가 섞인 sparse points와 너무 강한 early weight가 문제다.

실험 방향:

- camera-bound filtered sparse points만 사용.
- delayed start.
- 기존 `0.01 -> 0.002`보다 10배 이상 약한 weight.
- confidence 또는 nearest-camera consistency 기반 weighting.

### C. Optimizer/LR

주의:

- beta1을 낮춘 실험은 momentum을 높여 local minima를 탈출하는 실험이 아니었다.
- 의도는 early 잘못된 gradient/momentum 누적을 덜 따라가게 하는 것이었다.

더 타당한 방향:

- beta1 단독보다 `position_lr`, `scaling_lr`, densification schedule과 함께 본다.
- 초기 geometry 형성 구간과 후반 appearance fitting 구간을 분리한다.

## 피해야 할 함정

- `openmavis64_*` EVO 결과를 실제 OpenMAVIS camera 성능으로 해석하지 말 것. `openmavis_orb_64.*`가 올바른 파일이다.
- VGGT frame 수 증가는 RAM으로 해결되지 않는다. 현재 병목은 VRAM/attention memory다.
- sparse depth prior를 강하게 걸면 outlier sparse geometry를 고정할 수 있다.
- low opacity ratio만 낮다고 좋은 결과는 아니다. PSNR/visual과 같이 봐야 한다.
- large scale ratio가 낮아도 train/test PSNR이 낮으면 compact하지만 잘못된 geometry일 수 있다.

## 문서 업데이트 규칙

새 실험을 돌린 뒤 최소한 아래를 업데이트한다.

- `context/experiment_timeline.md`: 새 exp 번호, 목적, 설정, 결과.
- `context/current_findings.md`: 결론이 바뀌었는지.
- `context/repro_commands.md`: 재현 가능한 커맨드.
- 필요하면 `docs/notion_experiment_summary_YYYY-MM-DD.md`: Notion 정리용 표.
