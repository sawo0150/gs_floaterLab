# gs_floaterLab

OpenMAVIS 301_1253 trajectory 기반 3DGS에서 render 품질을 유지하며 floater를 줄이는 실험 워크스페이스.

## 시작하기

1. **`context/STATUS.md`를 먼저 읽는다** — 현재 best, 열린 질문, 다음 할 일이 여기에만 있다.
2. 전체 실험 이력은 `context/experiments/INDEX.md`.
3. 문서 구조와 갱신 규칙은 `context/README.md`. **실험 완료 시 exp 카드 + INDEX 한 줄 + STATUS 갱신, 이 3개는 필수.**
4. 실험 전 `context/knowledge/pitfalls.md` 필독.

## 주요 경로

- 메인 3DGS repo: `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom` (**dirty worktree — revert 금지**)
- 학습 데이터/결과 지도: `context/reference/workspace_map.md`
- 실행 커맨드: `context/reference/repro_commands.md`, `scripts/experiments/run_exp*.sh`
- conda env: `3dgs`
- W&B: `geekseek/3dgs-keyframe`
