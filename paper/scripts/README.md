# scripts/

| 스크립트 | 무엇 | 상태 |
|---|---|---|
| `newver.sh` | 버전 문서 폴더에 새 버전 생성 + CURRENT 심링크 재지정 + README 이력 추가 | ✅ 동작 |
| `make_tables.py` | `results/tables/*.csv` → `latex/tab/*.tex` | ✅ 동작 |
| `run_remote.sh` | 원격 GPU 디스패치 + run_id/manifest 생성 | ⚠ manifest만. RUN_CMD는 P01 후 |
| `collect_metrics.py` | 원격 로그 → `results/runs/<run_id>/metrics.csv` | ❌ 미작성 (P01 후) |
| `sync_overleaf.sh` | `latex/` ↔ Overleaf | ❌ 미작성 (동기화 방식 미정) |
