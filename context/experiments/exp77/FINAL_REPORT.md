# exp77 최종 보고 — 예산 제약에 따른 ERCB 효과

2026-09-13. 로컬 RTX 3070 Laptop에서 총 52개 실제 학습 run 완료.
근거: [기계 판독 결과](evidence/final_ablation.json), 재현 명령은 `outputs/exp77_*`의 manifest.

## 결론

기존 ERCB를 버릴 필요는 없다. **동일한 전체 dense pool과 도착 event를 유지하고
학습 예산을 제한하면 기존 ERCB가 RR을 반복적으로 이기는 비교 조건을 확보했다.**
이는 두 장면의 고정 pose/init replay 결과이며 범용적인 PSNR 가속이나 strict SLAM 성공은 아니다.
개발 seed0에서 정한 조건을 seed1/2에 재튜닝 없이 적용했다. 새 장면 검증은 하지 않았다.

## 1. 권장 ablation 축

단일 긴 학습 예산의 종점 대신 **update/event 15·30·60에 따른 quality–budget 곡선**을 사용한다.
각 예산 내 RR와 ERCB는 같은 전체 frame, 도착 event, 초기 PLY, pose, RGB loss,
해상도4, seed, update 수, 학습률 schedule, held-out 평가 지점을 사용한다.
낮은 예산에서 데이터를 빼거나 RR만 더 어려운 조건으로 만들지 않았다.

- RPNG: 전체 2,506 / train 2,192 / held-out 314, event 244.
- UTMM: 전체 1,614 / train 1,412 / held-out 202, event 80.
- 총 update는 `1+(events-1)*budget`, 마지막 도착 후 추가 update 0.
- densify/prune/carve 없음. held-out은 sorted COLMAP index modulo8=0.
- RR는 신규 frame을 unfinished epoch의 random slot에 넣는 기존 causal RR 그대로.
- 각 예산의 position LR horizon을 해당 총 update에 맞춘다. 예산 간 차이를
  순수 update 수의 효과라고만 해석할 수는 없지만 예산 내 scheduler 비교는 동일하다.

## 2. 낮은 예산15: 세 seed 재현 결과

아래는 최종 held-out 평균 PSNR의 RR 대비 차이(dB)다.

| 장면/방법 | seed0 개발 | seed1 반복 | seed2 반복 | 평균 | 승수 |
|---|---:|---:|---:|---:|---:|
| UTMM 기존 ERCB | +0.445 | +0.131 | +0.148 | **+0.241** | 3/3 |
| UTMM coverage1 | +0.429 | +0.205 | +0.193 | **+0.276** | 3/3 |
| RPNG 기존 ERCB | +1.176 | +1.008 | +0.897 | **+1.027** | 3/3 |
| RPNG coverage1 | +1.183 | +0.969 | +1.017 | **+1.056** | 3/3 |

개발 seed를 제외해도 두 방법 모두 4/4 양수다. 독립 seed는 독립 장면이 아니므로
6개 pair를 서로 독립적인 장면 표본으로 취급하거나 유의성을 과장하지 않는다.

## 3. 불리한 예산도 포함한 seed0 곡선

| 장면 | update/event | 기존 ERCB−RR | coverage1−RR |
|---|---:|---:|---:|
| UTMM | 15 | +0.445 | +0.429 |
| UTMM | 30 | +0.135 | +0.211 |
| UTMM | 60 | −0.036 | +0.001 |
| RPNG | 15 | +1.176 | +1.183 |
| RPNG | 30 | −0.023 | −0.025 |
| RPNG | 60 | −0.199 | +0.081 |

15의 재현성은 검증했지만 30의 반복 seed는 없다. 60에서는 coverage1과 RR 및
interval-base를 세 seed 비교했고 coverage1−RR 평균은 UTMM +0.022/RPNG +0.184다.
기존 ERCB의 예산60은 이번 실험에서 seed0만 있으므로 3-seed 비교처럼 쓰지 않는다.

따라서 주장할 결과는 **고정된 작은 학습 예산에서의 품질 우위**다.
모든 예산/모든 초기 평가 지점에서 빠르다는 주장은 거짓이다. 공통 PSNR 도달 시간의
정밀 측정이나 실제 시스템 전체 throughput 검증도 이번 결과에 포함되지 않는다.

## 4. ERCB 수정안과 ablation 의미

coverage1은 기존 ERCB의 interval/inner RR 구조를 유지하고 초기 한 pass까지만
count bonus를 준다. interval j의 크기 n_j, 배정 count c_j에 대해:

`w_j = n_j * exp(log(3) * max(0, 1-c_j/n_j))`.

기존 relative-floor는 target이 전체 평균 서비스의 절반으로 계속 변하지만,
coverage1은 평균 한 pass를 받으면 bonus가 0이 된다. K8 interval 비복원 및 inner
persistent RR는 동일하다. repo의 기존 TwoPass 구현에서 quota를1로 둔 수정이므로
완전히 새로운 알고리즘이라고 주장하지 않는다. 추가 backward/gradient storage 없음.

낮은 예산에서 기존 ERCB보다 평균 약 +0.03dB만 높아 필수 교체 근거는 약하다.
예산60에서는 기존 ERCB의 지속 보정 손실을 줄이는 개발 후보로 의미가 있다.
interval-base control은 특히 RPNG에서 자체 이득이 있으므로 count bonus에
전체 개선을 단독 귀속하면 안 된다. 현재 권장은 **기존 ERCB를 주 비교로 유지하고
coverage1을 보정 지속시간 ablation으로 제시**하는 것이다.

## 5. 서비스와 비용: 반드시 함께 보고할 한계

예산15 seed0의 zero-service는 RR/ERC B/coverage1 순으로 UTMM 398/567/535,
RPNG 269/501/482다. 품질이 올라도 미서비스 frame은 늘었다. 이는 품질 개선이
단순 첫 서비스 균등화에서 나왔다는 설명을 지지하지 않는다. 모든 frame이 같은
유용성을 가진다고 가정할 수 없으며 원인 메커니즘은 이 결과만으로 확정하지 않는다.
현재 어떤 후보도 bounded service latency를 보장하지 않는다.

예산15 seed0 draw CPU 누적은 ERCB UTMM15.6ms/RPNG88.9ms, RR4.6/15.6ms다.
training CUDA 누적은 각 장면 약4.2s/13.1s로 비슷하다. 이는 scheduler의 저비용
가능성을 보여주지만 전체 mapping 시간 1–3% overhead를 직접 입증하는 값은 아니다.
모든 run에서 입력 로딩·평가를 별도로 포함한 wall time도 저장했다. CUDA 시간은
매 step 동기화로 계측했으므로 실제 production throughput과 구분한다.

## 6. 실패 후보와 검증 범위

- packet(m4,r2): seed0 UTMM +0.018/RPNG −0.204dB, 미서비스 증가 → 미채택.
- coverage2: 양쪽 약 −0.058dB → 미채택.
- window reorder: −0.093/−0.159dB, 모든 평가 지점 RR 미달 → 미채택.
- interval top-K는 `|G_j|` base weight를 블록 전체 marginal에 보존하지 않음.
  CPU 반례는 확인했지만 이것을 PSNR 손실의 확정 원인으로 쓰지 않는다.

52개 run은 초기6 + coverage6 + window4 + coverage반복12 + 예산12 + 낮은예산반복12.
완료 run의 실제 optimizer count=draw count=T, last arrival=T, post-update report,
동일 held-out/도착표/평가 grid와 유한 PSNR을 검사했다. 원래 packet pair의 outer hash도
일치했다. 데이터 복사본은 유지했으며 UTMM full의 깨진 링크만 복구하고 원래 경로를 보존했다.

## 7. 논문에 쓸 수 있는 문장

> 고정된 지도 초기화와 pose를 사용하는 두 incremental replay 장면에서, 동일한
> dense-view stream에 event당 15 updates를 배정했을 때 ERCB는 causal RR보다
> 세 seed 평균 held-out PSNR을 각각 0.241dB와 1.027dB 높였다. 이 이득은
> 학습 예산에 의존하며, 더 큰 예산에서는 감소하거나 역전될 수 있다.

실제 VIGS 통합, 독립 장면, 엄격한 causal 초기 geometry, service latency 개선은
후속 검증 대상이다. 이번 fixed-final-pose/cumulative-geometry 실험을 strict online
RGB+IMU-only의 인과성 증명이나 Aria27dB 달성으로 사용하지 않는다.
