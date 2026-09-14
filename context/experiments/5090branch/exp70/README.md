# exp70 — Surface-support preservation vs. detached floater

Detached floater의 문제 정의부터 score-free loss 구현, strict streaming과 manual-region
GT 결과까지 묶은 exp70 문서 모음이다.

- `exp70_detached_floater_problem_formulation.html`: 3DGS 연구자를 위한 논문식 문제 정의,
  ray termination distribution, surface inflation / recoverable misalignment / detached floater의
  구분, multi-view transit·terminal 3D memory의 역할과 현재 carve의 구조적 한계
- `exp70_score_free_detached_termination_loss.html`: terminal-conditioned density-valley detector,
  direct-alpha/NLL opacity action, strict 4-arm 실행, manual-region GT 결과와 현재 판정

## 현재 상태

- **1.5× baseline:** direct alpha/NLL 모두 held-out 27dB를 지켰고, direct alpha는
  erosion/nominal/dilation visible floater를 12.0/14.9/9.1% 줄였다.
- **교정된 final-v7 RTX 5090 original 1×:** legacy causal carve를 완전히 제거하고
  control/alpha/NLL을 재실행했다. PSNR은 28.148/27.706/27.792dB, region op&gt;.3은
  nominal 148/161/164, dilated 383/401/407로 두 loss 모두 악화했다.
- total replay 차이는 EOS rematuration 1,416/0/384회를 섞은 착시였다. 이를 제외한
  streaming update는 control/alpha/NLL 5,910/6,089/5,956이고 pre-EOS 시간도
  69.064/69.098/69.066초라 새 loss의 연산비는 병목이 아니다.
- 현재 final-v7 final-map 결과 자체는 **NO-GO**지만, 원인은 compute tax로 볼 수 없다.
  EOS rematuration을 끄고 update 수·view 순서를 고정한 A/B로 action 효과를 분리해야 한다.

## 연결 근거

- VIGS-SLAM causal field: `repos/main/VIGS-SLAM/vigs/gaussian/utils/causal_carve.py`
- 기존 carve 수렴 재평가: `context/experiments/exp65_status_report.md`
- incremental geometry 사후 감사: `context/experiments/exp68/exp68_geometry_postmortem_audit.html`
- detector/action 분리 결과: `context/experiments/exp69/exp69_result.html`
- raw manual-region evidence: `evidence/exp70_aria1253_manual_region.json`
- final-v7 1× corrected evidence: `evidence/exp70_v7_1x_legacyoff_seed0_summary.json`
