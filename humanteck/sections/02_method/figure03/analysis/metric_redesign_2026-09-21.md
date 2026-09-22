# Fig.3 평가 범위 재검토

사용자가 inset frame 1180을 선택했다. 기존 A/B/C 파일은 선택 이력으로 보존한다.
신규 학습·GPU 평가 없이 기존 checkpoint별 per-view PSNR을 재집계했다.
원본: `results/figure03_convergence_20260921/aria301_305/evaluation/`.
정확한 수치: [scope_diagnostic.csv](measured_curves/scope_diagnostic.csv).

## 발견

- 600/1000/1250/1300 step 전체 평균 Δ: +0.7125/+1.0190/+0.8680/+5.5433 dB.
- 같은 시점 frame1180 Δ: 약 +0.16/+0.10/+0.02/+15.53 dB(정확한 값은 CSV).
- frame1100–1300 고정 41뷰 역시 1300 이전 차이는 약 0.2–0.3 dB다.
- frame0–1400 고정 281뷰는 600/800/1000에서 약 +1.00/+1.79/+1.78 dB다.
  이는 진단용 사후 선택 범위이며 주 그림의 사전 고정 평가 프로토콜이 아니다.
- 따라서 미관측 영역이 평균을 희석하는 영향은 일부 있지만, 1180 inset의 후반 차이를
  설명하는 유일한 원인은 아니다. pose correction과 고정 post-EOS 평가 pose의 관계가 남는다.

## 제안 — 아직 실행하지 않은 추가 평가

수렴 주장은 공통 input event에서 관측 범위·pose 상태를 맞춘 local refinement 평가로 검증한다.
고정된 held-out view 집합, 공통 causal pose 기준, 동일 추가 optimizer iteration에서 비교한다.
전체 시스템 비교라면 각 방법의 KF/dense 관측 선택 정책은 보존하며 입력 prefix만 맞춘다.
여러 사전 지정 event에서 평가하여 전체 trajectory에 걸친 결과를 얻는다. 각 event 내에서
동일 cohort를 사용하고, 비교 horizon을 완주하는 공통 event 집합을 고정해 평균한다.

x: Additional mapping iterations; y: Mean held-out PSNR.
Pose와 추가 입력을 잠시 고정한 분기 실험이라면 controlled refinement 진단으로 명시하고,
원래 zero-tail streaming 실험의 결과로 간주하지 않는다. 새 실험도 큰 gap은 보장하지 않는다.
기존 전체 trajectory 곡선과 endpoint 표는 별도 online quality/coverage 근거로 유지한다.
1180은 inset 후보로 확정하되, 실제 측정에서 점진적인 개선이 있는지 확인한 뒤 checkpoint를 정한다.
