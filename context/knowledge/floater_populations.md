# Floater는 두 집단이다 (프로젝트 핵심 프레임)

> 근거: Round 1-5 진단 루프 + exp13. 마지막 갱신 2026-07-07.

| | Pop 1 | Pop 2 |
|---|---|---|
| 원인 | SLAM 삼각화 실패 sparse init outlier | densification이 ambiguity 높은 영역에 생성 |
| 위치 | FOV 밖, \|Z\| 최대 907,582m → pruning 후 \|Z\|≈42m frozen | **FOV 안**, \|Z\| = 3-6m |
| loss 가시성 | gradient ≈ 0 (perturbation 민감도 surface의 1/53) | ambiguity 원인 (픽셀 33-35%) |
| 해결책 | **camera-bound init filtering (해결됨, exp13)** | **미해결** — plateau loss 검증 중 (Round 6-7) |
| 대응 결과 | Z-outlier -99% @500, -74% @30k, PSNR -0.16dB | exp25가 PSNR 회복까지, floater 개선 미확인 |

## 왜 이 구분이 중요한가

- opacity 기반 pruning은 둘 다 못 잡음: low-opacity 126,330개는 대부분 표면 위에 있고 (floater 아님), high-opacity Z-outlier가 오히려 더 멀리 drift. 표준 pruning(threshold 0.01)은 Z-outlier의 86.8%를 통과시킴.
- Pop1은 gradient로 못 고침 (loss에 안 보임) → 학습 중 개입이 아니라 **초기화 전 필터링**이 정답.
- Pop2는 필터링으로 못 막음 (densification이 학습 중 생성) → **학습 중 제어**가 필요.
- 하나의 기법으로 "floater 제거"를 주장하는 기존 논문들과 달리, 원인별로 다른 도구가 필요함을 정량 확인 — 논문 contribution의 축.

## 관련 수치 출처

- Pop1 메커니즘/시계열: `rounds/round2-3_gradient_perturbation.md`
- Pop1 해결: `experiments/exp13_pcd_filter.md`
- Pop2 시도: `rounds/round6_plateau_orb.md`, `rounds/round7_plateau_mps.md`
- Key figures: `results/diagnostic/round1c_z_outlier_analysis.png`, `round2_gradient_analysis.png`, `exp13_final_comparison.png`

## SLAM 특유 novel 관점 (논문용 아이디어 뱅크)

기존 16편 floater 논문이 안 다룬 것 (상세: `knowledge/perspective_bank.md`):

1. Camera ray density void — SLAM trajectory에서 ray가 드문 구간이 floater 온상
2. Compositing depth rank — floater가 surface 뒤에서 T_k≈0으로 loss에 invisible
3. Densification seed 경로 — densification 직후 Gaussian이 즉시 empty space에 있는지
4. Ray direction ambiguity — photometric loss는 ray 방향 depth를 구분 못함 (P04: X가 depth 축)
5. SH DOF 보상 — floater가 고차 SH로 잘못된 위치를 color로 보상
