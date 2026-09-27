# Visual dense pose — cross-scene transfer

## 2026-09-25 사전 등록

질문: Aria 고정지도에서 복원된 dense RGB 이득이 다른 공개 benchmark 장면에도 재현되는가?
RPNG `table_06`(논문 대표 장면), UTMM `square-1`, `ego-centric-1`(서로 다른 이동 유형)을
결과 확인 전에 선정한다. 단일 seed 0, 장면별 튜닝 없이 기존 visual pose 6회 설정을 유지한다.

- 고정지도: 장면별 native R4 EOS snapshot 하나에서 Gaussian/Adam/KF pose 고정.
  KF-only RGB, KF+dense RGB 원본 pose, KF+dense RGB visual pose를 각 5000 step 비교한다.
  같은 mixed 영상 순서, full Gaussian gradient, RGB L1+SSIM, 고정 topology.
  250 step도 기록. 실제 mapper 학습 RGB/pose/depth만 pose 보정에 사용한다.
  EOS 후 진단이며 보정 계산은 별도 추가된다. 총 계산량을 맞춘 실험이나 strict-live 결과가 아니다.
- Online: native RGB-D carrier를 유지한 full-scope dense 두 slot에서
  IMU refresh repair-only와 repair+visual을 비교한다. Frozen-tracker causal replay,
  동일 mapping render/Adam/선택순서, held-out 제외, zero-tail을 검증한다.
  현재 도착한 KF 두 장만 anchor로 사용하며 추가 pose 시간과 mapping 시간을 별도 기록한다.
- 성공 판정: fixed-map visual mixed가 원본 mixed뿐 아니라 KF-only도 넘는지 구분한다.
  Online 개선은 별도 판정한다. 음성 결과도 모두 남긴다. Floater/geometry 개선은 이 PSNR 실험으로 주장하지 않는다.
- Source lock, fixed manifest, checkpoint/selection hash, saved-map 재평가로 비교를 검증한다.
  Production 소스는 변경하지 않는다.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_visual_pose_transfer.py`

Artifacts: `results/campaigns/gain_attribution/visual_pose_transfer/`

## 결과

고정지도 3개 장면 및 online pair 3개 장면 완료. 단일 seed 탐색 결과이며 아래에 모든 결과와 실패 기록을 남긴다.

### RPNG table_06 — fixed-map 완료

KF-only **25.8155**, 원본 dense **24.5434**, visual dense **25.7577dB**.
Pose 보정 +1.2143dB, KF-only 대비 −0.0578dB로 대부분 회복하나 우위는 미재현.
250 step은 각각 24.5631/23.4748/24.4665dB. 244뷰 보정에 5.845초 추가.
동일 초기 map/Adam, mixed 선택순서, pose-only snapshot, held-out 555장 제외,
고정 topology 및 저장 후 재평가 검증 PASS. EOS 후 5000회 진단, strict 결과 아님.
Artifact: `comparisons/rpng/table_06/fixed.json`.

### UTMM square-1 — fixed-map 완료

KF-only **23.3274**, 원본 dense **23.0744**, visual dense **23.6112dB**.
Pose 보정 +0.5368dB, KF-only 대비 **+0.2838dB**로 dense 추가 이득 재현.
250 step은 각각 21.5164/21.4077/21.5871dB. 71뷰 보정에 2.024초 추가.
초기 map/Adam·mixed순서·pose-only snapshot·held-out324장·fixed topology·saved reload PASS.
EOS 후 5000회 진단이며 strict 결과 아님. Artifact: `comparisons/utmm/square-1/fixed.json`.

### UTMM ego-centric-1 — fixed-map 완료

KF-only **21.8008**, 원본 dense **21.8361**, visual dense **22.0963dB**.
Pose 보정 +0.2602dB, KF-only 대비 **+0.2955dB**.
250 step은 각각 19.3469/20.0220/20.3103dB. 40뷰 보정에 1.318초 추가.
초기 map/Adam·mixed순서·pose-only snapshot·held-out308장·fixed topology·saved reload PASS.
EOS 후 5000회 진단이며 strict 결과 아님. Artifact: `comparisons/utmm/ego-centric-1/fixed.json`.

### 고정지도 3-scene 판정

Visual pose는 원본 dense보다 3/3 개선, KF-only보다 2/3 개선. RPNG에서는
큰 dense 손실을 회복하지만 KF-only 우위까지는 재현하지 못했다. Online pair는 별도 진행.

### RPNG table_06 — online pair 완료

Repair-only **24.44525**, repair+visual **24.49613dB** (+0.05088).
동일 34,437 map renders / 2,714 Adam / dense 및 native history 선택순서.
Held-out555장, causal bracket/anchor depth·pose 불변, zero-tail, 독립 double-eval PASS.
420 pose calls(2520 motion graph updates), pose9.779초+load0.032초 추가.
Mapping143.223→155.765초(+8.76%). 고정지도 회복폭과 달리 온라인 이득은 작음.
Frozen tracker mapping-only, 총 계산량 불일치, strict live 이득으로 미해석.
Artifact: `comparisons/rpng/table_06/online.json`.

### UTMM online 첫 시도 — harness 검증 실패 기록

`square-1/online_control`은 mapping_replay_runtime.json까지 저장 후
`refreshed_views > 0` 사후 조건 때문에 실패했다. 로그에 dense refresh가 없고
이 adapter의 호출은 backend PGBA refresh 발생에 종속된다. 모든 시퀀스에서
refresh가 반드시 발생해야 한다는 가정이 부적절했다. 품질 실패/성공으로 판정하지 않는다.
기존 로그/지도/runner/source lock은 보존한다.

추가 runner `run_visual_pose_transfer_online.py`와 별도 artifact root
`results/campaigns/gain_attribution/visual_pose_transfer_online/`에서 UTMM 두 장면을 재실행한다.
바뀌는 것은 **refresh 횟수 양수 요구 삭제 및 실행 여부 별도 기록**뿐이다.
미래 IMU 금지·visual 실제 호출·causal bracket·동일 mapping work/선택순서·held-out·double-eval 검증은 유지한다.
학습 recipe/pose 보정 알고리즘/seed는 바꾸지 않는다.

### UTMM square-1 — online pair 완료

Control **21.33320**, visual **21.35691dB** (+0.02370).
동일 9,345 map renders / 757 Adam / dense 및 native history 선택순서.
Held-out324장·causal bracket·anchor 불변·zero-tail·독립 double-eval PASS.
IMU refresh audit는 실제 calls=0, refreshed_views=0; adapter만 설치되고 갱신 이벤트가 없었다.
Visual 70회, pose1.860초+load0.031초 추가. Mapping40.603→42.141초(+3.79%).
매핑 wall 차이와 내부 pose 시간은 다른 연산/측정 변동 때문에 정확히 합산되지 않는다.
고정지도 +0.2838dB(KF대비)에 비해 online pose 추가 효과는 작다.
Artifact root: `visual_pose_transfer_online`, `comparisons/utmm/square-1/online.json`.

### UTMM ego-centric-1 — online pair 완료

Control **17.84921**, visual **17.86313dB** (+0.01393).
동일 5,676 map renders / 466 Adam / dense 및 native history 선택순서.
Held-out308장·causal bracket·anchor 불변·zero-tail·독립 double-eval PASS.
Visual 43회, pose1.223초+load0.035초 추가. Mapping31.311→31.610초(+0.96%).
단일 실행 시간 차이는 pose 비용보다 작아 runtime noise가 있으며 비용이 사라졌다는 뜻은 아니다.
Artifact root: `visual_pose_transfer_online`, `comparisons/utmm/ego-centric-1/online.json`.

## 최종 비교

고정지도는 동일 snapshot에서 **EOS 뒤 5000 RGB step**을 학습한 결과다.

| 장면 | KF-only | 원본 dense | Visual dense | Visual − KF | Visual − 원본 dense |
|---|---:|---:|---:|---:|---:|
| RPNG table_06 | 25.8155 | 24.5434 | 25.7577 | −0.0578 | +1.2143 |
| UTMM square-1 | 23.3274 | 23.0744 | 23.6112 | +0.2838 | +0.5368 |
| UTMM ego-centric-1 | 21.8008 | 21.8361 | 22.0963 | +0.2955 | +0.2602 |

Online은 **동일 full-dense mapper에서 visual pose 보정 유무** 비교다. KF-only 대조가 아니다.

| 장면 | Control | Visual | Δ PSNR | Pose 추가 시간 | Mapping control → visual |
|---|---:|---:|---:|---:|---:|
| table_06 | 24.44525 | 24.49613 | +0.05088 | 9.779s | 143.223 → 155.765s |
| square-1 | 21.33320 | 21.35691 | +0.02370 | 1.860s | 40.603 → 42.141s |
| ego-centric-1 | 17.84921 | 17.86313 | +0.01393 | 1.223s | 31.311 → 31.610s |

고정지도에서 pose 보정 자체의 효과는 3/3, dense가 KF-only를 넘는 효과는 2/3 장면이다.
Online pose 추가 효과는 모두 작고 단일 seed라 실용적/통계적으로 유의한 개선이라고 결론내리지 않는다.
모든 성공 비교에서 source/input lock·held-out·동일 mapping work/selection·저장 후 평가 검증 PASS.
Pose 추가 계산으로 총 계산 예산은 같지 않으며 tracker와 동시 실행한 strict-live 평가도 아니다.
Production mapper는 변경하지 않았다.

## 후속 코드 방향 — 2026-09-25 사용자 논의

- Pose 보정만, gradient scope만, dense render 비중만 바꾸는 것으로 해결됐다고 주장하지 않는다.
  이미 scope-only와 ~11% dense 재배분은 일관된 online 이득을 보이지 않았다.
- Dense RGB 준비(현재 anchor로 pose 보정·anchor/map version에 따른 캐시 무효화),
  유효 training pool, 실제 photometric service/선택 count를 명시적으로 연결한다.
- Gaussian birth/필수 depth-normal geometry supervision을 보존하면서 KF와 dense를 같은
  photometric 학습 경로에서 선택한다. 별도 single-view SH-only 보너스 경로의
  batch/Adam/loss-sum 차이를 제거하거나 대조 실험에서 엄격히 고정한다.
- Training-set growth는 완료한 photometric service를 기준으로 credit을 쌓는다.
  단순 packet 수/입력 도착 수/이미 admit한 영상 수를 학습 완료량으로 대신하지 않는다.
- ERVS의 count에는 native 경로를 포함해 실제 RGB gradient에 기여한 모든 선택을 반영한다.
  공통 pool/동일 loss weighting으로 논문 목적함수의 의미와 실제 학습 배분을 맞춘다.
- 최근 geometry window와 전체 과거 photometric 후보 pool을 구분한다. CPU history와 GPU LRU cache를
  분리하고, 과거 pose는 현재 map generation/anchor version에 맞는 경우에만 학습 후보로 쓴다.
- 다음 대표 검증은 Aria1253/RPNG table_06/UTMM square-1의 3 family로 사전 고정한다.
  table_06은 이번에 KF-only 우위 미달이었지만 실패 사례를 포함한다. 장면별 튜닝 금지.
- 같은 새 backbone에서 KF-only → dense immediate+RR → growth+RR → growth+ERVS를 비교한다.
  Pose 준비·geometry quota·loss weighting·topology는 공통으로 두어 기여를 분리한다.
  현재 production baseline도 별도 비교하며, render/Adam뿐 아니라 pose 포함 총 시간과
  stream 도중 held-out 곡선/zero-tail을 함께 확인한다. Geometry/Carve는 품질 gate 뒤 별도 검증한다.

후속 구조는 아직 구현/검증하지 않은 설계 제안이다. 이번 결과를 성능 보장으로 해석하지 않는다.
