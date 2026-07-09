# Round 7 — MPS Plateau Variants Sweep (완결, 2026-07-05)

Round 6의 DepthPro ellipsoidal plateau를 MPS full 1311장 (exp08 하이퍼파라미터)로 옮기고, loss 형태/스케줄/pruning 변형을 sweep. 개별 상세는 `experiments/exp19~26` 카드 참조.

## 결과 한눈에 (baseline exp08 = 33.012, exp13 filter = 32.855)

| Exp | 변형 | PSNR@7k | PSNR@30k | Δ vs exp08 |
|---|---|---:|---:|---:|
| exp19 | 기본형 (λ=0.01 고정) | 28.09 | 32.753 | -0.26 |
| exp20 | λ 0.10 조기 시작 스케줄 | 27.13 | 31.693 | -1.32 |
| exp21 | opacity_weight, λ=0.10 | 28.14 | 30.770 | -2.24 |
| exp22 | exp loss kernel, λ=0.05 | 28.00 | 29.917 | -3.10 |
| exp23 | adaptive prune (500 iter) | 28.30 | 26.655 | -6.36 |
| exp24 | exp loss + prune | 28.14 | 미완 (27k kill) | - |
| **exp25** | **enlarged tau + λ 0.10→0.03** | 28.23 | **32.969** | **-0.04** |
| exp26 | enlarged tau + λ=1.0→0.03 | 28.14/28.25 | 32.706/32.674 | -0.31 |

## 확정된 설계 원칙

1. **tau가 λ보다 중요** — plateau를 키워 표면 Gaussian을 안에 넣는 것(exp25)이 loss를 세게 거는 것(exp20/21/26)보다 훨씬 낫다. gradient 타게팅이 핵심.
2. **개입 강도의 상한**: λ ≤ 0.10, densification(7k) 이후 시작. λ=1.0(exp26)이나 조기 시작(exp20)은 photometric 최적화를 방해.
3. **opacity_weight / exp_loss / adaptive_prune 모두 역효과** — 특히 반복 hard pruning(exp23)은 후반 수렴 붕괴(-6.36dB).
4. 조합(exp24)은 구성 요소가 단독으로 나쁘면 돌릴 가치 없음.

## 미해결 (→ STATUS)

- **exp25의 floater 지표 검증이 안 됨** — PSNR 동급 회복이 "floater 감소 + 품질 유지"인지 "아무 효과 없음"인지 구분 필요.
- exp25 + exp13 filter 조합 미실험.
