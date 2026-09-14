# exp03 — RTX 5070 Ti exp77 budget interaction reproduction

날짜: 2026-09-15
상태: **실행 준비 완료; 결과 대기**

## 질문

RTX 3070 Laptop에서 관측한 exp77의 핵심 결과, 즉 interval relative-floor ERCB가
작은 mapping budget에서는 causal RR보다 높지만 budget이 커지면 이득이 감소하거나
역전되는 현상을 RTX 5070 Ti에서 재현할 수 있는가?

## 사전 고정 계약

- 원본 코드: `3dgs-custom@da1dbda` + 보존된 exp77 patch
- 별도 worktree: `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro`
- 데이터: corrected `ercb_vigs_replay_v2`의 UTMM `square-1`, RPNG `table_01`
- 비교: causal RR vs exp75 interval relative-floor ERCB
  (`K=8`, `rho=.5`, `gamma=log(3)`)
- budget: keyframe arrival event당 `15/30/60` update
- seed: budget15는 `0/1/2`, budget30/60은 `0`
- 총 20 run; 각 pair는 동일 RGB, arrival, pose, init, update, LR horizon, 평가 frame 사용
- resolution 4, RGB loss, fixed topology(`densify_until_iter=0`), llffhold-8
- 마지막 arrival과 마지막 optimizer update가 같고 이후 update는 0(zero-tail)
- primary metric: final held-out PSNR의 paired `ERCB - RR`

절대 수치는 GPU뿐 아니라 PyTorch/CUDA가 달라질 수 있다. 재현 판정은 budget15의 두
장면 3-seed 평균 delta가 모두 양수인지, 그리고 seed0에서 budget 증가에 따라 ERCB
delta가 감소하는지를 본다. 원 exp77처럼 budget30/60은 반복 seed를 일반화 근거로
사용하지 않는다.

## 결과

실행 후 기록한다.

## 한계

이 실험은 fixed final VIGS pose와 누적 geometry initialization을 쓰는
scheduler-isolation replay다. 실제 strict VIGS, online pose, live wall-clock 또는
현재 unified KF+dense mapping loop의 성공으로 해석하지 않는다.
