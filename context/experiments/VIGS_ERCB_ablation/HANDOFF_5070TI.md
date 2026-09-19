# 5070 Ti 에이전트 인계 — 2026-09-13

## 현재 요청 / 우선 읽기

사용자는 로컬3070 실험을 중단하고 GitHub를 통해5070 Ti에서 이어가도록 요청했다.
**지금3070에서 학습 중인 프로세스는 없다.** 실패 출력은 로컬에 보존했다.
다음 목표는 실제 VIGS-SLAM의 RPNG table_01에서 RR/기존 ERCB(relative_floor)/
coverage1을 같은 조건으로 비교하고 정상 조건에서3-seed 반복하는 것이다.

1. 이 repo의 context/STATUS.md와 LOCAL3070.md를 읽는다.
2. VIGS-SLAM-custom의 exp81_axes/HANDOFF_RPNG_5070TI.md를 읽는다.
   데이터/환경/실행 명령/검사 명령/실패 원인/제약이 모두 그 파일에 있다.
3. 실험 카드의 과거 "중단"과 "재개" 항목은 시간순 기록이다. 최신 사용자 요청은
   **이 컴퓨터에서는 중단,5070에서 재개 준비**다. 새로3070 학습을 시작하지 않는다.

## Git 위치

두 repo 모두 인계 브랜치: `handoff/ercb-rpng-20260913`.

- VIGS: https://github.com/sawo0150/VIGS-SLAM-custom
  인계 코드 commit `4b12a023`, 기반 `23adbfaf`.
- 실험 문서: https://github.com/sawo0150/gs_floaterLab
  이 문서가 포함된 인계 브랜치. 기반 `3b8cc82`.
  fetch 시 원격 main은 `d22c7d4`였다. 원격 main의 다른 작업을 덮어쓰지 않기 위해
  main으로 push/merge하지 않았다.

서버가 dirty하거나 더 최신이면 reset/checkout으로 덮어쓰지 말 것. 별도 worktree를
만들거나 인계 commit을 검토 후 cherry-pick한다. 예:

```bash
git fetch origin
git worktree add ../ercb-rpng-handoff origin/handoff/ercb-rpng-20260913
```

각 repo에서 별도로 수행한다. VIGS의 새 worktree에는 서버 환경에 맞는 submodule/
CUDA 확장 빌드와 pretrained_models 연결/준비가 필요하다.3070의.so를 복사하지 않는다.
실행 wrapper에 GS_FLOATER_LAB_ROOT, EXP69_CONDA_ENV, EXP81_HARDWARE_PROFILE=rtx5070ti를
명시하는 명령은 VIGS 인계 문서에 있다. wrapper 이름 run3070은 유지하지만 override 지원.

## 결과를 혼동하지 말 것

### UTMM square-1 — 실제 VIGS,3070 scale6, fixed324뷰

| arm | seed0 | seed1 | seed2 | 평균dB |
|---|---:|---:|---:|---:|
| RR |19.458044|19.390477|19.398387|19.415636|
| relative_floor |19.564295|19.448941|19.585773|19.533003|
| coverage1 |19.518942|19.619168|19.614576|19.584229|

기존-RR+0.117367dB(3/3), coverage1-RR+0.168593dB(3/3),
coverage1-기존+0.051226dB(2/3). 단일 개발 장면, 실제 pool/pose 차이가 있으므로
범용적 우위/논문 최종 ablation 완료가 아니다. 상세 근거는 LOCAL3070.md.

### RPNG table_01 — 유효한 비교 없음

| RR 실행 | 결과 | 처리 |
|---|---|---|
| 최초 | frame276 Rwg=None | gravity-ready guard 수정 |
| retry1 | frame839 correlation OOM | allocator128 검사 |
| retry2 | fixed15.397522dB, 완주 | parallel 누락으로 idle replay 미실행, **RR 기준값 제외** |
| retry3 | parallel 수정 후 frame1538 OOM | 최종PSNR 없음 |
| retry4 | cudaMallocAsync도 frame731 OOM | 최종PSNR 없음 |

RPNG에서 ERCB arm은 아직 실행하지 않았다. 기존 +1dB는 exp77 fixed-map의 관측이지
RPNG VIGS 결과가 아니다. CPU correlation staging은 **구현하지 않았다**.
5070 Ti에서는 메모리 우회 코드를 먼저 만들지 말고 현재 GPU 구현과 수정된 parallel
설정으로 RR부터 검증한다. 6×에서의 첫 실행은 재현 진단이며 strict1.5× 성능 주장이 아니다.

## 인계 검증 / 제외 파일

CPU 테스트27개 통과(interval/causal identity/audit/depth capacity), bash -n과
git diff --check 통과. 서버 GPU 완주를 증명하는 테스트는 아니다.
audit_local_pair.py는 이제 MAP_RR_DONE/draw_count/pool 없는 실행을 거부한다.
동일 seed의3-arm을 비교하고 fixed502뷰, zero-tail, eval updates0을 확인한다.

원본 outputs, 데이터, 약1GB Omnidata weights, CUDA 바이너리, conda 환경은 Git에
올리지 않았다. 관련 없는 repos/main 심볼릭 링크 삭제와 prepull-untracked 스크립트도
포함하지 않았다. LOCAL3070.md에 결과/실패 경로와 재현 정보가 기록되어 있다.
서버의 기본 Zenodo weights와3070 official_hf weights의 tensor 동등성은 미검증.
각 arm에 같은 weights를 고정하고 하드웨어 간 결과를 직접 paired 비교하지 않는다.

## 다음 에이전트에게 줄 요청

> 두 저장소의 handoff/ercb-rpng-20260913 브랜치를 확인하고, gs_floaterLab의
> context/experiments/VIGS_ERCB_ablation/HANDOFF_5070TI.md와 VIGS의
> exp81_axes/HANDOFF_RPNG_5070TI.md를 읽어줘.5070 Ti에서 수정된 RPNG
> RR부터 검증하고, 같은 조건으로 relative_floor/coverage1 및3-seed를 비교해줘.
> retry2의15.398dB는 replay가 꺼진 무효 기준값이니 사용하지 말고, 기존 서버의
> dirty 작업을 보존해줘. 응답은 한국어로 해줘.
