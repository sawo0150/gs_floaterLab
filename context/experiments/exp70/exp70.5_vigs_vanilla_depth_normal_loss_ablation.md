# exp70.5 — VIGS-SLAM vanilla depth/normal loss ablation (aria1253)

- 날짜: 2026-09-01
- 코드: `VIGS-SLAM-vanilla-check` (detached HEAD `22ffe24c` == `cvg/VIGS-SLAM` origin/main,
  **알고리즘 완전 무수정** — rasterizer `#include <cstdint>` 빌드호환 패치 1줄만 있음, exp52와
  동일 원칙). `repos/main/VIGS-SLAM`(exp53~69가 누적 수정한 실험용 fork)과는 별개 체크아웃.
- 데이터: `data/aria1253` (RGB 1303장·IMU 65,425샘플), exp52와 동일
- 산출물: Google Drive `gs_floaterLab/exp70_depth_normal_ablation_aria1253/`(기존
  exp68/69 convention대로 ply+json+config만 개별 업로드, README는
  [`exp70.5_drive_README.md`](exp70.5_drive_README.md)에 로컬 복제본). 렌더 이미지·전체 로그 등 원본은
  로컬 `VIGS-SLAM-vanilla-check/exp_depth_normal_ablation/outputs/`에만 있다.

## 목적

VIGS-SLAM 소스 정독(exp52)에서 발견한 두 감독 항 — depth L1(`get_loss_mapping_rgbd`의
`(1-alpha)*l1_depth*5` 항)과 Omnidata normal 일관성(`get_loss_normal`,
`lambda_dnormal` 가중) — 이 vanilla 알고리즘 자체의 순수 온라인 매핑 품질에 각각/함께
어떤 영향을 주는지 2x2 요인 설계로 직접 측정한다. carve loss/causal carve 논의(research/
carveloss_academic)와는 별개로, "VIGS 최신 버전이 실제로 어떻게 동작하는가"를 확인하는
과정에서 나온 후속 확인 실험이다.

## 설정 — baseline 대비 diff만

토글은 전부 **config 값만 변경**(코드 수정 없음):

- `Training.alpha` — `get_loss_mapping_rgbd`의 depth 항 계수. `1.0`=depth 항 계수 0(OFF),
  `0.95`(vanilla 기본)=ON
- `Training.lambda_dnormal` — `get_loss_normal` 계수. `0.0`=OFF, `0.5`(vanilla 기본)=ON
- 나머지는 전부 `config/aria301_305_vanilla.yaml`(=`config/vigs.yaml` 템플릿 + Aria
  IMU/Tcb만 대입한 순수 vanilla 기본값) 그대로, aria1253 calib(`calib/aria1253.txt`,
  500/500/512/512)만 aria301_305 대신 사용
- 실행: `--gsmapping --pure_online`(최종 backend BA·26,000-iter 오프라인 색 정제 생략)
  + `VIGS_EVAL_PURE_ONLINE=1`(VIGS 자체 opt-in eval 훅, `demo.py`) — 순수 온라인 궤적만으로
  held-out/keyframe PSNR-SSIM-LPIPS를 채점
- 4개 config: `config/exp_depth_normal_ablation/aria1253_{both_off,depth_only,normal_only,both_on}.yaml`
- 실행 스크립트: `exp_depth_normal_ablation/run_all.sh`(4개 순차 실행) +
  `collect_results.py`(결과 취합)

### 셋업 중 발견·해결한 이슈 (알고리즘과 무관, 환경 문제)

1. 공유 conda env(`vigs-slam-5090`)의 site-packages에 **다른 VIGS fork의
   `diff_gaussian_rasterization`가 전역 설치**돼 있어 vanilla 코드(5-값 unpack)와 충돌
   (`ValueError: too many values to unpack (expected 5)`) — exp69 러너 스크립트가 이미
   쓰던 방식대로 `PYTHONPATH`로 이 체크아웃의 로컬 thirdparty 빌드를 앞세워 해결.
2. 첫 실패 시도의 리더 서브프로세스가 GPU 메모리 11GB를 쥔 채 좀비로 남아 재시도가
   OOM — 프로세스 정리 후 재시도로 해결.

## 결과 — held-out / keyframe (pure-online, 오프라인 정제 없음)

| variant | held PSNR | held SSIM | held LPIPS | kf PSNR | kf SSIM | kf LPIPS | wall time |
|---|---:|---:|---:|---:|---:|---:|---:|
| depth OFF / normal OFF | **23.1369** | 0.7550 | 0.4107 | 23.3514 | 0.7618 | 0.4010 | 234s |
| depth ON / normal OFF | 22.4328 | 0.7425 | 0.4240 | 22.6212 | 0.7476 | 0.4157 | 231s |
| depth OFF / normal ON | 21.9624 | 0.7360 | 0.4570 | 21.9503 | 0.7368 | 0.4524 | 232s |
| depth ON / normal ON (vanilla 기본값) | 22.1378 | 0.7407 | 0.4487 | 22.3361 | 0.7448 | 0.4409 | 233s |

4개 런 시간이 231~234s로 사실상 동일(로스 함수 자체는 파이프라인 시간에 거의 영향 없음,
즉 시간-품질 트레이드오프가 아니라 순수 손실함수 효과).

**두 감독 항 모두 이 순수-온라인 조건에서는 개별적으로도 손해였다**: depth OFF/normal
OFF가 4개 중 최고(23.14dB)이고, normal ON 두 조합이 최저(21.96/22.14dB)로 SSIM/LPIPS도
같은 순서로 일관되게 나빴다. depth 단독 ON(22.43dB)도 둘 다 OFF보다 −0.70dB.

⚠ **exp52 원 vanilla 베이스라인(kf 30.90dB, held-out 26.85dB)과 직접 비교 불가** — 그
수치는 오프라인 26k-iter 색 정제 포함값이고, 이번 4개는 `--pure_online`으로 그 단계를
전부 생략한 순수 온라인 수치다. 이 실험의 목적은 절대 성능이 아니라 두 손실 항의
**온라인 단계 자체에서의 상대 효과**를 노이즈 없이 분리하는 것이었다.

## Verdict

**측정 완료, 해석 잠정.** n=1(seed 1개)이라 이 프로젝트 기존 run-to-run 노이즈 실측치
(±0.24~0.33dB, exp30/43)를 감안하면 depth ON/OFF의 개별 효과(−0.70dB)는 노이즈 폭을
넘지만, normal 단독 효과(21.96 vs 23.14 = −1.17dB)와 둘 다 켠 조합(22.14dB, OFF/OFF보다
−1.00dB이지만 normal 단독보다는 +0.18dB 회복)의 상호작용 방향은 반복 없이는 확정하기
이르다. **hard 채택/기각 판단은 보류** — 배치·carve 트랙(exp38~44d2)에 있는 것과 유사하게
"단일 run 비교 금지"([exp43](exp43_cross_scene_plan.md) 교훈)가 그대로 적용된다.
반복 검증하려면 seed 고정 여부 확인 후 동일 config로 2회 이상 재실행.
