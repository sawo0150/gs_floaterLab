# 현재 말할 수 있는 것과 Introduction을 지탱할 실험

이 문서는 실험 제안이다. 이번 리서치에서 GPU 학습이나 새로운 성능 측정을 수행하지 않았다. 아래 수치는 기존 결과 카드의 전사이며, raw artifact 재실행 검증을 뜻하지 않는다.

## 1. 최신 구현과 기존 초안의 차이

2026-09-26 문서를 기준으로 recent KF window/full KF/admitted dense의 3:3:6 구성, 영상별 Adam, 누적 ERVS, κ=16/τ=4/blur OFF 추천이 있다. 모든 후보가 학습 풀에 들어오는 방식은 아니다. 또한 현재 결과는 geometry/floater 개선을 검증하지 않았다.

이전 `vigs_slam_method_three_contributions_notion_draft.md`의 mature-service controller/random reshuffling과 최신 구현 문서의 completed-step credit/ERVS를 같은 알고리즘으로 설명하면 안 된다. 본문에 쓸 κ 정의·credit 이월·count scope·reset 동작은 최종 채택 소스와 다시 고정해야 한다. 본 조사는 최신 [구현 메모](../../experiments/campaigns/06_gain_attribution/growth_entropy_blur/IMPLEMENTATION.md)를 우선한다.

## 2. 기존 증거의 정확한 범위

### 2.1 Dense 경로의 이득은 있으나 “모든 조건에서 필수”는 아님

[KF RGB-only 대조군 결과](../../experiments/campaigns/06_gain_attribution/kf_rgb_control/SUMMARY.md)

| 장면 | KF native loss | KF RGB-only | Dense RGB-only | Dense−KF RGB-only |
|---|---:|---:|---:|---:|
| Aria | 24.7299 | 25.0578 | 25.5921 | +0.5343 dB |
| RPNG | 24.8112 | 25.0035 | 25.1179 | +0.1144 dB |
| UTMM | 21.4156 | 21.7631 | 22.1052 | +0.3421 dB |

같은 40 renders/KF에서 RGB loss를 맞춘 KF 대조군 대비 dense 경로가 평균 +0.3303dB다. 하지만 mapping time은 KF RGB-only 24.50/88.77/30.15초, dense 54.54/144.35/56.11초다. 또한 pose·pool·selection 분포와 초기 실제 slot 배정이 모두 같지는 않다.

**가능한 주장:** 세 개발 장면의 fixed-work 비교에서 non-KF supervision 경로가 추가 held-out 이득을 보였다.

**불가능한 주장:** 동일 시간에서도 항상 우수하다; geometry가 개선됐다; 이득이 전부 픽셀 다양성 때문이다; dense 없이는 고품질이 불가능하다.

### 2.2 편입률 제어는 “전부 넣어야 한다”와 반대되는 근거도 제공

[Growth/entropy/blur 결과](../../experiments/campaigns/06_gain_attribution/growth_entropy_blur/SUMMARY.md)

- 기존 immediate/τ1/blur OFF → 선택 κ16/τ4/blur OFF: 평균 held-out +0.1734dB, 합산 mapping time −26.0%.
- 다만 admission과 τ가 함께 바뀐 최종 endpoint 비교다. κ 단독의 수치라고 쓰지 않는다.
- offered/admitted dense: Aria 924/227, RPNG 1810/465, UTMM 1133/177. 실제 학습에 쓰인 distinct dense는 213/425/166.
- dense training share는 여전히 약 48–49%다. 적게 편입한 것과 dense 학습 비중을 줄인 것을 혼동하지 않는다.
- τ를 0.25로 낮춰 더 강하게 count를 균등화한 조건은 세 장면 모두 악화했다. **동일 횟수 = 동일 유용성 = 최적 학습**이 아니다.

**좋은 연결:** supervision의 양과 각 supervision에 배정되는 학습 기회를 같이 고려해야 한다.

### 2.3 Lifetime count가 더 좋다는 결과는 없다

[누적 ERVS 결과](../../experiments/campaigns/06_gain_attribution/cumulative_ervs/SUMMARY.md)

누적 count는 recent-count 대조군보다 Aria/RPNG/UTMM에서 −0.255/−0.161/−0.077dB, 평균 약 −0.1645dB다. 기억 길이와 native window 사용 집계가 함께 바뀐 비교다.

이 실험은 **최근 frame pool vs 전체 history pool** 비교가 아니다. 두 sampler의 count 기록 방식 비교다. 따라서 “최근 pool이 더 좋다” 또는 “전체 pool이 더 좋다” 어느 쪽의 증거로도 사용할 수 없다. 수학적으로 깔끔한 count accounting과 경험적 품질 향상은 별도로 입증해야 한다.

### 2.4 전체 vanilla 대비 이득을 sampler 하나로 설명하지 않기

[Gain attribution campaign](../../experiments/campaigns/06_gain_attribution/README.md)에는 initialization, update grouping, geometry carrier, pose quality 등 혼재 원인이 기록되어 있다. earlier ERVS/RR 비교도 큰 독립 이득을 입증하지 못했다. 최종 조합과 vanilla의 차이는 recipe 전체 효과이며, Introduction에서 전부 view scheduling 덕이라고 쓰지 않는다.

### 2.5 평가 계약

위 9월 26일 패널은 frozen causal tracker의 mapper 비교다. render/Adam·causal prefix·held-out 제외·zero-tail audit는 있지만, 실제 concurrent tracking/live와 strict 1.5× wall-clock 성능을 입증하는 것은 아니다. 단일 seed의 3개 개발 장면이며, 저장 지도를 두 번 평가한 것은 독립 학습 반복이 아니다.

## 3. 가장 먼저 필요한 비교: pool 범위와 count 기억 분리

**핵심 가설 H1:** 같은 후보 선택·pose·loss·work에서 전체 시간 범위의 replay eligibility가 local/최근 제한보다 과거 영역 품질을 보존한다.

| Pool policy | 유지되는 정보 | 무엇을 구분하는가 |
|---|---|---|
| Recent-only | 최근 M개 admitted views | 강한 최신성 baseline |
| Covisibility | 현재와 겹치는 admitted views | 최근보다 공간적으로 유의미한 baseline |
| Reservoir M | 전체 시간축에서 제한된 M개 | full history와 bounded-memory의 차이 |
| Coverage coreset M | 시야/공간 coverage를 보존한 M개 | count가 아니라 관측 다양성이 핵심인지 |
| Full-history | 모든 admitted views에 접근 가능 | 현재 가설의 대상 |

먼저 uniform 또는 random reshuffling을 고정해 support만 비교한다. 다음으로 full-history support를 고정하고 uniform/RR/recent-count/lifetime-count/loss-priority를 비교한다. **Pool lifetime × count memory**를 분리하지 않으면 질문에 답할 수 없다. Reservoir/coreset 크기는 별도 memory-budget 축으로 보고 장면별 성능을 보고 정하지 않는다.

## 4. Dense가 왜 유용한지를 입증하는 비교

**H2:** tracking KF로 표현되지 않은 관측 정보를 추가하면, 같은 RGB loss와 계산 예산에서 KF 재학습만으로 얻기 어려운 held-out 이득이 생긴다.

첫 단계는 지금 있는 RGB-only 대조군의 반복·held-out scene 확장이다. 이후 추가 dense를 무조건 많이 넣기보다 uniform temporal selection, coverage selection, blur/pose quality selection, Online NVS 계열 selection과 비교한다. 선택 정책은 같은 candidate inventory에서 실행한다.

Dense 후보마다 다음 metadata를 기록하면 “왜”를 설명할 수 있다: 가까운 KF와의 overlap/시점 차이, keyframe frustum 밖에서 보인 영역 비율, 선명도, online pose residual, 최종 사용 횟수, 준비 비용. 이런 proxy와 gain의 상관관계는 인과 증명이 아니므로, 가설에 맞는 subset ablation으로 이어간다.

추가로 **full-frame dense vs 같은 수의 KF renders**, **동일 wall-clock에서 준비비용 포함**, **pose 품질을 통제한 진단**을 구분한다. GT pose 진단은 관측 정보의 가능성을 알아보는 용도이며 strict RGB+IMU 성능 결과로 합치지 않는다.

## 5. Robotics 독자가 보고 싶어 할 시간축 지표

최종 평균 PSNR 하나로는 “빠르게 유용해지는 지도”라는 Introduction을 지탱하기 어렵다.

- **Prefix held-out curve:** 시점 t까지 실제 관측된 영역의 공통 held-out cohort에서 quality(t)를 측정한다. 아직 관측하지 않은 장면까지 포함한 future-view 점수와 분리한다. 평가 영상은 끝까지 학습·선택·stop rule에 사용하지 않는다.
- **관측 후 지연:** 각 영역이 처음 관측된 시각부터 사전 정의한 품질 수준에 도달할 때까지의 시간. threshold 미달은 누락하지 않고 censored/failure로 표시한다. threshold는 개발 결과를 보고 장면별 조정하지 않는다.
- **과거 영역 유지:** 동일 old-region held-out cohort를 여러 시점에서 평가해 개선/퇴화를 추적한다. 단순 frame arrival order와 실제 surface first-seen time이 다를 수 있다.
- **종료 시점 점수:** zero-tail 지도와 +고정 refinement 지도를 별도 보고해 사후 학습이 메운 간극을 드러낸다. 실제 시스템이 마지막 프레임을 미리 알도록 만들지 않는다.
- **서비스 지표:** map age, tracking queue 지연, wall-clock deadline 초과, input 준비·pose refinement·render/backward·IO 분해.
- **메모리:** RAM/VRAM/disk와 후보·편입·학습된 distinct view 수를 trajectory 길이에 대해 보고한다. GPU cache가 제한되어도 CPU history가 무한히 작아지는 것은 아니다.

이 지표들은 제안이다. 아직 우리 시스템의 online map readiness가 개선됐다는 측정 결과는 없다.

## 6. Geometry를 같은 이야기로 연결하는 조건

Appearance를 빨리 맞춘다는 사실만으로 좋은 mapping이라고 결론 내리지 않는다. 추가 RGB가 free-space artifacts를 줄일 수도, pose error를 map distortion으로 흡수할 수도 있다. Geometry/floater는 region GT, depth/normal/mesh 지표, 관측된 빈공간 위반 등의 독립 측정이 필요하다.

Carve를 통합한 주장을 하려면 동일 initialization·topology·pose·budget에서 supervision policy × carve 유무를 비교하고, photometric/geometry/time을 함께 보고한다. 현재 27dB 미달 지도에 hard carve/pruning을 우선 투입하지 말라는 프로젝트 규칙은 그대로 따른다. 여기서는 실행을 제안하거나 승인한 것이 아니라 논문 주장의 조건을 정리했다.

기존 Introduction의 “position gradients는 본질적으로 실패하므로 opacity만으로 제거해야 한다”는 강한 인과 주장은 이번 조사로 뒷받침되지 않는다. Geometry section은 별도 원문 조사·gradient 진단·matched-budget ablation을 거쳐야 한다. opacity penalty가 항상 position update보다 우월하다고 쓰지 않는다.

## 7. 예상 리뷰 질문과 정직한 답

| 질문 | 현재 답 | 필요한 증거 |
|---|---|---|
| KF를 더 자주 뽑으면 되는가? | tracking/BA까지 늘리는 것과 추가 mapping view만 쓰는 것은 비용이 다름 | tracker KF density sweep와 mapper-only admission 비교 |
| 단순히 training image가 늘어난 효과인가? | 일부가 그 효과일 수 있으며 그것 자체도 유용함 | matched-work/matched-time, sampler 단독 ablation |
| Non-KF pose를 어떻게 얻는가? | 도착한 KF interval에서 online refinement; 비용과 latency 존재 | causal timestamp/pose-version ledger, 비용 포함 |
| Global replay는 이미 있지 않은가? | 있다. broad novelty로 주장하지 않음 | CaRtGS/Online NVS/EliGSiR 정책과 공통 backend 비교 |
| 과거 전부 저장해야 하는가? | 현재로서는 입증 안 됨 | reservoir/coreset 및 memory-quality 곡선 |
| Count가 loss보다 나은가? | 아직 모름. count는 사용량 proxy일 뿐 | stale-loss 대응 포함 priority baseline, overhead 비교 |
| 메모리와 계산 모두 bounded인가? | per-step work 제한과 total history memory 제한은 다름 | trajectory 길이별 storage/cache/latency |
| 왜 robotics 논문인가? | causal map availability와 geometry를 연구 대상으로 삼음 | online curves/geometry, 필요하면 downstream 평가 |
| VLA에 실제 도움이 되는가? | 이번 시스템에서는 검증 안 됨 | 별도의 policy 실험이 없으면 motivation에만 사용 |
| 이미 충분히 학습된 과거 프레임은 왜 또 쓰는가? | map 변경에 대한 제약으로 남김; 모든 프레임이 항상 유용하지는 않음 | old-view regression과 replay intervention의 연계 |

## 8. 우선순위

1. 현재 dense-vs-KF RGB-only 비교를 같은 wall-clock에서도 확인한다.
2. full-history vs recent/reservoir를 **동일 sampler**로 비교한다.
3. full-history를 고정한 뒤 uniform/RR/CaRtGS식 loss quota/count policy를 비교한다.
4. final PSNR뿐 아니라 prefix·old-region·new-region 곡선으로 기전을 확인한다.
5. geometry와 concurrent live 검증을 마친 범위만 최종 contribution으로 올린다.

실험을 많이 나열하기보다, Introduction의 각 인과 문장에 대응하는 결과 하나가 있는지 확인하는 것이 목적이다.
