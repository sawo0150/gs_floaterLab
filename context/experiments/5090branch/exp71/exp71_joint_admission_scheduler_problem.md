# exp71 — Growing-pool joint admission/scheduling problem

- 날짜: 2026-09-04
- 유형: scheduler-only synthetic simulation
- 상태: **NO FEASIBLE \((\kappa,\beta)\); 문제 전제 충돌 확인**

## 질문

1. 종료 시 초기 view와 stream 절반에 들어온 view가 비슷한 lifetime update count를 받는가?
2. GPU update rate가 일정할 때 pool 증가율이 pool 크기와 무관하게 일정한가?
3. 각 logical minibatch가 전체 pool의 uniform random shuffle처럼 높은 entropy와 낮은
   gradient mixing error를 갖는가?

## 변경

- 기존 age-adjusted quota simulator와 별도로 joint simulator를 작성했다.
- admission을 \(A(u)=\lfloor u/\kappa\rfloor\)인 GPU-token controller로 분리했다.
- 실제 admission timestamp를 기록해 초기 cohort와 \(T/2\) cohort를 직접 비교했다.
- full-pool ordered shuffle entropy, temporal Wasserstein, cohort entropy, 세 synthetic
  gradient field의 finite-population-normalized batch MSE를 추가했다.
- \(p(i)\propto\exp(-\beta n_i)\)인 ERCB family를 \(\beta=0\)부터 \(\infty\)까지 sweep했다.

## 실행

- 주 sweep: \(B=32\), 6k/12k/18k updates, 16 seeds, 15 kappas, 18 betas + controls
  = 15,120 scheduler trajectories
- sensitivity: \(B=8,16\), 각 8 seeds
- acceptance: fairness NRMSE≤0.10, Jain regret≤0.01, half/first 0.9–1.1,
  entropy≥0.95, gradient mean/worst≤2/3, temporal W1≤2

## 결과

- \(B=8,16,32\) 모두 feasible point 0개. 따라서 적절한 단일 \(\beta\)는 없다.
- \(B=32\) 최소 위반점조차 \((\kappa,\beta)=(768,1.0)\), half/first 0.549,
  entropy 0.643, gradient mean/worst 3.22/4.61로 채택 불가다.
- 빠른 admission에서는 causal oracle이 half/first≈1을 만들 수 있으나 그 서비스 편향이
  trajectory gradient를 크게 왜곡한다. 느린 admission에서는 pool이 batch에 비해 작아
  oracle 자체가 halfway cohort를 따라잡지 못한다.
- token admission은 모든 sweep에서 target tracking error=0, budget violation=0이었다.
- maturity gate는 \(B=32,T=18k,\kappa=32\)에서 uniform 18.9%, active-bonus 28.4%만
  목표 admission을 처리했다.

## 판정

- **채택:** maturity gate와 분리된 GPU-token admission 원리.
- **미채택:** ERCB의 특정 \(\beta\). 현 specification 아래 valid beta가 없다.
- **다음 결정:** (A) full-pool uniform objective + age-adjusted fairness, (B) raw lifetime
  equality + weighted objective, (C) bounded pool/admission stop/tail 중 하나를 먼저 선택한다.
- 실제 VIGS-SLAM/PSNR 주장은 하지 않는다.

상세: [`joint_admission_scheduler_sim_report.md`](../../research/joint_admission_scheduler_sim_report.md)

