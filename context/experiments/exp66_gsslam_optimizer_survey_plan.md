# exp66 — GS-SLAM 2차 최적화 논문 서베이 (LM-RS / CaRtGS 실측)

> 배경: exp65에서 M1~M4(초기화/제약/closed-form 색/carve loss 재해석) 다섯 축이
> 전부 기각됐다. 사용자가 외부에서 GS-SLAM 2차 최적화 계열 논문 4편을 조사해왔고,
> 그중 실제 실행 가능한 것부터 우리 인프라에 붙여보기로 함(2026-08-20).

## 조사한 4편과 실행 가능성

| 논문 | 공개 코드 | 판정 |
|---|---|---|
| **3DGS²** (arXiv 2501.13975, SIGGRAPH 2025) | ❌ 없음(프로젝트 페이지에 논문만) | 이번 축 제외 — 코드 없이 재구현은 고위험/고비용 |
| **LM-RS** (arXiv 2504.12905, "Matrix-free Second-order Optimization of Gaussian Splats with Residual Sampling", 3DV 2026) | ✅ [github.com/hamzapehlivan/lm-rs](https://github.com/hamzapehlivan/lm-rs) | **실행**. vanilla 3DGS(Kerbl) fork, optimizer만 교체. CUDA 11.8, `scripts/compile.sh`로 커스텀 커널 컴파일. static scene 전용(SLAM 아님) |
| **CaRtGS** (arXiv 2410.00486, RA-L 2025) | ✅ [github.com/DapengFeng/cartgs](https://github.com/DapengFeng/cartgs) | **실행**(사용자 명시 요청). Photo-SLAM 기반 완전 별도 C++/CUDA SLAM 시스템. Replica/TUM/VECtor 지원 |
| **FSGS**(monocular SLAM+Stochastic Local Newton, OpenReview wktBQXOtQS) | ❌ 없음, arXiv 미러도 없음, OpenReview 접근 자체가 봇체크로 제한 | 이번 축 보류 — 나중에 코드/논문이 더 공개되면 재검토 |

## 환경 제약 (실행 전 확인 완료, 2026-08-20)

- GPU: RTX 5070 Ti, VRAM 16303MiB, 현재 여유 15702MiB. LM-RS 권장 사양이 "최소 16GB, A40/A100에서 테스트"라 **타이트함** — OOM 가능성 있음, 발생 시 회피책 대신 findings로 기록.
- 디스크: `/` 파티션 915GB 중 47GB만 여유(95% 사용). Replica/TUM 데이터셋은 필요한 최소 scene만(예: Replica room0 1개) 받고, 다운로드 전후 여유 용량을 반드시 확인.
- apt 패키지: CaRtGS 요구 목록 중 `libeigen3-dev`/`libboost-all-dev`/`libglfw3-dev`/`libjsoncpp-dev`/`libopengl-dev`/`libgl1-mesa-dev`/`libglew-dev`는 이미 설치됨. `libglm-dev`/`mesa-utils`만 미설치 — codex는 sudo 불가(비밀번호 필요)이므로 사용자가 직접 설치 필요.
- 두 축 다 새 conda env 사용(`3dgs`/`vigs-slam-5090` 재사용 안 함 — 요구 CUDA/PyTorch 버전이 다름).
- 새 clone은 전부 `VIGS-SLAM/exp66_axes/` 아래에만 — `3dgs-custom`(dirty worktree, revert 금지) 손대지 않음.

## 축 1: LM-RS — 우리 scene에서 vanilla Adam 대비 실측

**방법론 주의(M1b 교훈 재적용)**: 서로 다른 repo의 PSNR을 직접 비교하면 렌더러/eval
불일치가 진짜 차이처럼 보일 위험이 있음(M1b에서 Δ_lift의 92%가 실제로 렌더러
불일치였던 전례). 따라서 **LM-RS 저장소 안에서** vanilla 3DGS 경로(원 코드 그대로,
optimizer 교체 전)와 LM-RS optimizer 둘 다 우리 scene(`gs_floaterLab/data/
03_rgb_3dgs_full`, 이미 COLMAP 포맷)에 돌려서 **같은 harness 안에서** 비교한다.
exp65 M4의 control 궤적(vanilla Adam, 같은 scene: 500~7000 iter PSNR 21.03~28.93dB)은
어디까지나 참고용 교차검증이지 1차 비교 대상이 아님.

- checkpoint: 500/1000/2000/3000/4000/5000/6000/7000 iter에서 held-out PSNR
- 판정 기준: 같은 iteration에서 LM-RS가 vanilla보다 유의하게(exp30/43 노이즈 폭
  ±0.24~0.33dB 밖) 높으면 채택 후보

## 축 2: CaRtGS — 공식 벤치마크 재현

CaRtGS는 SLAM 시스템 전체(추정+매핑)라 우리 임의 static scene에 바로 못 붙임.
1차 목표는 **Replica 중 가장 작은 1개 scene(예: room0)에서 논문 보고 수치 재현** —
빌드가 실제로 되는지, 우리 GPU/디스크 환경에서 돌아가는지 확인하는 것 자체가
1차 목적. 재현되면 "splat-centric backward parallelism" 등 이식 가능한 기법이
있는지 코드 레벨로 확인(전체 시스템 이식이 아니라 기법만).

## 종료 기준 / 리포트

각 축 완료 시 `exp66_status_report.md`(신설 예정)에 exp65 방식과 동일하게
축별 결과+판정 기록. `STATUS.md`/`INDEX.md`는 축 완료마다 갱신.
