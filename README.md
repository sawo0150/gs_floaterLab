# gs_floaterLab

OpenMAVIS `301_1253` trajectory 기반 3DGS에서 render 품질을 유지하며 floater를 줄이는 실험 워크스페이스.

Scope: dataset `0416_301-1253`, SLAM은 OpenMAVIS, 재구성은 custom 3DGS. (2DGS, COLMAP baseline, 3-camera SLAM은 범위 밖)

## 시작점

- **현재 상태 / 다음 할 일**: `context/STATUS.md`
- 전체 실험 이력: `context/experiments/INDEX.md`
- 문서 규칙: `context/README.md`

## 폴더 구조 (2026-07 재편, 각 폴더 README 참조)

| 폴더 | 내용 |
|---|---|
| `context/` | knowledge base (STATUS, 실험 카드, 진단 라운드, 확정 결론, 참조 문서) |
| `data/` | 학습 데이터 파이프라인: 00_raw → 01_euroc → 02_openmavis_output → 03_rgb_3dgs_full |
| `scripts/` | pipeline / experiments / diagnostic / analysis / anchors |
| `results/` | experiments / rounds / diagnostic / datasets / logs / archive |
| `repos/` | 외부 repo 심링크 (3dgs-custom, OpenMAVIS, vggt) |
| `data_trash_20260707/` | (2026-07-15 삭제됨 — 구 depth_map 캐시, 용량 정리) |
