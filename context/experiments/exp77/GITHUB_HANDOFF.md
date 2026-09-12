# exp77 GitHub handoff

2026-09-13. 구현 저장소 `sawo0150/3dgs-custom`의 `a1b0ea7`과 이 실험 폴더를 함께 사용한다.
52개 실제 run의 결과는 `FINAL_REPORT.md` 및 `evidence/final_ablation.json`에 있다.

## 포함 / 제외

- 포함: scheduler 구현·CPU 테스트(3dgs-custom), 실행/검증 스크립트, 결과 요약, 준비 기록.
- `context/research/*2026-09-12.md`는 초기 제안 기록이며 채택/검증된 방법을 뜻하지 않는다.
- 제외: 원본 데이터, 학습 PLY, 전체 outputs, CUDA 빌드 산출물, Python cache.
- 두 `local_changes_*.patch`는 당시 백업이다. 최신 구현 commit 위에 다시 apply하지 않는다.

## 서버에서 재사용할 때

1. 양쪽 repo를 pull하고 `3dgs-custom` 구현 commit을 확인한다.
2. Python/3dgs repo/데이터 절대경로를 서버 위치에 맞춘다. 현재 스크립트는 로컬
   `/home/wosasa/...` 및 `.codex-work/3dgs-custom-main`을 기준으로 작성됐다.
3. `prepare_run.py`로 복사 완료된 full v2 source/arrival/provenance를 검사하고
   **새 output 경로**에 명령을 생성한다. 초기 PLY가 필요하며 held-out은 llffhold8이다.
4. 생성된 명령을 `run_training.py`로 실행한다. 원본 데이터 수정/기존 결과 덮어쓰기 금지.

`run_*screen.py`, `run_*validation.py`, `run_budget_ablation.py`는 이 세션의 orchestration
기록이다. 일부는 당시 프로세스 PID와 기존 outputs manifest에 의존하므로 새 서버에서
그대로 실행하지 않는다. 재실행에는 새 manifest를 준비하고 개별 runner를 사용한다.
원래 outputs의 대용량 결과는 GitHub에 포함하지 않았다. 단일 JSON evidence는 검증 결과의
집계본이며 원본 per-view 로그나 모든 run manifest를 대체하는 완전한 원시 데이터셋은 아니다.

실제 시스템 성능은 아직 검증하지 않았다. 고정 final pose/누적 geometry replay 결과를
strict causal VIGS/Aria 성능으로 취급하지 않는다.
