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
- 공유 자료: `share/` (각 하위 폴더별 README 설명서 완비)
- 개별 배포용 압축 파일들:
  - `floater_share_01_labels.zip` (사용자 라벨 PLY 압축, 171MB)
  - `floater_share_02_region_gt.zip` (Delaunay 3D 영역 마스크 압축, 452KB)
  - `floater_share_03_results.zip` (기존 비교용 PLY 압축, 321MB)
  - `improved_results.zip` (최신 개선 12F 및 305호 결과 PLY 압축, 303MB)
- conda env: `3dgs`
- W&B: `geekseek/3dgs-keyframe`
