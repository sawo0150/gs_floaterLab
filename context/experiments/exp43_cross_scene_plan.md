# exp43 (계획) — 교차 장면 일반화: 새 장소에서 carve 재현 + ORB confidence 재평가

- 상태: **계획** (2026-07-12 수립, 미실행)
- 목적: 1253호에서 확정한 방법론(carve exp40b 레시피 + region GT 지표 체계)이 **다른 장면에서 재현**되는지, 그리고 SLAM 품질이 나쁜 조건에서 **ORB confidence(observations/found_ratio)가 유효해지는지** 검증.
- 배경: 1253호 ORB 지도는 깨끗해서(terminal증거 0인 anchor 16/7,205, fr<0.25가 floater 근처에 안 몰림) confidence 필터가 무효과(AUC +0.0004). 지도가 지저분한 장면에서는 다를 수 있음 — MPS에서 outlier 7.6%가 실재했던 것처럼.

## 후보 장면 (전부 VRS+MPS 완비, `26-1_RPM/Datas/CustomData/0416_Data/`)

| 우선 | 장면 | 성격 | 노림수 |
|---|---|---|---|
| **1** | **0408_919C_418** | 다른 건물·다른 방 | 정통 일반화 시험 (실내 room-scale 유지) — **사용자 라벨링 대상 추천** |
| 2 | 0416_301-1253-2_rot | **같은 방, 다른 궤적(회전)** | 라벨 불필요 부가 시험 — 기존 region GT 스탬프·carve field의 궤적 독립성 검증 |
| 3 | 0227_snu_floor2_1 | 다른 건물 복도(추정) | 최강 스트레스 (복도 = SLAM 취약 + floater 온상) — 2차 |

## 절차

1. `scripts/pipeline/run_full_pipeline.sh`를 919C_418로 실행 (VRS→EuRoC→OpenMAVIS→RGB 3DGS 데이터셋)
2. ORB 지도 품질 진단 먼저: anchor terminal-증거 분포, obs/found_ratio 분포 — 1253 대비 얼마나 지저분한가
3. baseline 30k 학습 → **사용자가 SuperSplat으로 floater 라벨링** (이번엔 저op 먼지도 가능한 만큼 포함 권장 — 지난 라벨의 불완전성 교훈)
4. 라벨로 region GT v2 구축 + champion score AUC 재측정 — **confidence 유/무 A/B** (obs·fr 필터/가중)
5. carve(exp40b 레시피) 학습 → 사전 등록 기준: region 가시 먼지 -90%+, PSNR은 그 장면 baseline 재현 노이즈 내

## 사전 등록 판정

- 재현 성공: 새 장면에서 champion score AUC ≥ 0.95, carve 학습으로 가시 먼지 ≥90% 감소
- confidence 유효 판정: confidence 필터/가중이 AUC를 +0.01 이상 올리면 "지저분한 지도에서 유효" 채택
- 실패 시 1순위 의심: 장면 스케일/tau(0.25m)·voxel(0.1m) 하드코딩 값의 장면 의존성

## 결과 1: 301_1253_rot (07-13 새벽, 사용자 라벨 도착)

- 사용자 라벨 5,168개 (5.6%, op p50 0.045 — 원본 장면과 동일 패턴)
- **자동 pseudo-label: precision 100% (4,663/4,663), recall 90.2%** — 사람 추가분 505개뿐 (파일명 'pruningplus'로 보아 pseudo-cleaned에서 시작해 추가 삭제한 것으로 추정 = 자동 삭제 전부 승인)
- **champion score 교차 장면 AUC 0.9813** (원본 0.976 이상) — 다른 궤적·다른 SLAM맵에서 완전 일반화
- ORB confidence(obs≥5) A/B: 0.9807 — 무효과 재확인 (지도 깨끗)
- 진행: rot 장면 carve 학습(exp43rot, dynamic carve 포함) — 진짜 라벨로 채점 예정

## 결과 2: rot carve 학습 — dynamic carve의 자기강화 결함 발견 (07-13)

exp43rot(dynamic carve 포함, raw init): PSNR 30.53(baseline 동급), region_n 7,864→5,301(-33%) — 그러나 **가시 먼지 106→716 역증가.**
**가설: dynamic carve 자기강화** — 가시 먼지 무리가 자신을 terminal 증거로 등록 → rho↓ → score↓ → 자기 보호 되먹임. 1253에선 깨끗한 init이라 잠복(가시 63 유지), raw init+densify 조건에서 발현.
→ **반증 실험 결과 가설 기각**: exp43rot2(static) 도 가시 741 (dynamic 716과 동일) — dynamic 여부와 무관.
**재해석: carve의 설계상 사각지대.** champion score의 (1−maxop_5cm) 보호항이 '이미 불투명해진' 먼지 무리를 보호함 → carve는 저op 먼지 전담이고, **가시 floater는 예방(좋은 init)이 담당**이라는 기존 분업이 raw init 장면에서 그대로 드러난 것. 검증: in-region 가시 741점의 78%가 free space(d5>0.25m) = 진짜 부유물. 1253에서 가시 먼지가 적었던 건 hybrid init 덕분.
- 후속: ① rot에 hybrid init 이식(예방 경로 재현) ② densify 구간 한정 maxop 보호 해제 gate/prune variant (치료 경로 확장)

## 결과 3: 305·12F 라벨 도착 (07-13)

- 305: 9,059/111,596 (8.1%), op p50 0.053, **가시(op>0.3) 1,340** — 지금까지 가장 지저분한 장면. confidence 유효성 판정의 최적 시험대.
- 12F: 1,449/20,436 (7.1%), op p50 0.053, 가시 161 — 저품질(fog) 장면 거동 관찰용.
- 2F·snu(복도)는 기하 열화로 사용자 라벨링 불가 → 라벨 기반 검증 대상에서 제외 (파이프라인 한계 클래스 유지).
