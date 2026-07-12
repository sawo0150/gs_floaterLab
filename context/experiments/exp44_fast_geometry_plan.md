# exp44 (계획) — 고속·고품질 geometry 트랙: dense init × no-densify × carve

- 상태: **계획** (2026-07-12 수립, 미실행)
- 최종 목표(프로젝트 재정의): **Aria glass 실시간 촬영 스트림 → 분 단위 turnaround로 geometry 좋은 3DGS recon.**
  실시간 경로에는 MPS(오프라인 클라우드 서비스) 사용 불가 → **ORB(OpenMAVIS) 트랙이 본선**.
- 참조 방법론: EDGS (CompVis) — dense correspondence 삼각측량 init + **densification 제거**로 25% 시간에 도달.
  (Instant-GI는 2D Gaussian 이미지 표현이라 직접 부적용 — "내용 적응적 점 배치" 사상만 차용, exp37이 이미 3D판)

## 왜 "dense init + no-densify + carve"가 서로를 완성하는가

1. **floater 출생의 100%가 densification에서 나왔다** (split 29.5%가 허공, 먼지가 먼지를 낳는 연쇄 — exp38 계측).
   → **densification을 끄면 출생 채널 자체가 소멸**: gate 불필요, 남는 먼지는 init 유래뿐.
2. exp37(dense init 148k)의 약점 = **먼지 부하 4.5배** (champion score 기준) — dense init은 빈 공간에도 점을 뿌림.
   → **carve soft+prune이 정확히 그 반대 방향**: init 직후(iter 0~)부터 빈공간 점을 소멸. 상호보완.
3. no-densify → N 고정 → iteration 비용 일정 + 메모리 예측 가능 + budget prune 캘리브레이션 단순화.
4. 학습 단축: EDGS는 3k step에 근접 품질 주장. 우리 하드웨어에서 30k=8~14분이므로 **5~7k step 목표 시 2~4분/장면** 예상.

## 설계 (변형 사다리)

| 변형 | init | densify | carve | 목표 |
|---|---|---|---|---|
| 44a | exp37 dense init (SLAM core + monodepth conf, 148k) | **off** | soft+prune (gate 불요, start_iter 0/500) | 기존 자산만으로 EDGS 사상 재현 |
| 44b | 44a | off | 44a + force | force 가치 재확인 |
| 44c | **correspondence 삼각측량 init (EDGS/RoMA식)**: keyframe 쌍 dense matching → SLAM pose로 삼각측량 (기하 검증된 점) | off | soft+prune | monodepth의 scale 오차 없는 init |
| 44d | **hybrid**: 44c(기하 검증) + monodepth fill(텍스처 없는 흰 벽/천장 — matching 실패 지역) | off | soft+prune | 이 방의 feature-poor 문제 정면 대응 |
| 44e | **2D GS 선최적화 → 3D 사영** (Instant-GI 사상의 3D 이식, 사용자 제안): 각 keyframe에서 2D Gaussian을 빠르게 fit → monodepth로 3D lift | off | soft+prune | 내용-적응 밀도 + **색·이방성 사전 최적화** — init 시점에 이미 '거의 학습된' gaussian 제공 |
| 공통 sweep | — | — | — | iterations ∈ {3k, 7k, 15k, 30k} — 시간-품질 Pareto |

> 44e 메모: 2D fit이 주는 것 = ① 텍스처 복잡도 비례 점 밀도(평탄한 벽엔 큰 gaussian 소수) ② 사전 최적화된 색/공분산 → 3D 초기 수렴 가속. lift에는 monodepth 필요(44d와 공유). 다중 뷰 중복 점은 voxel 병합. 44a/c/d 결과를 본 뒤 착수 판단.

## 평가 (사전 등록)

- 축 1 (품질): region GT 지표 + 시각 검수 + segment held-out SSIM/LPIPS (train PSNR 금지)
- 축 2 (속도): wall time (데이터셋 생성 제외 학습만) — 목표 **총 5분 내 gaussian 가시 먼지 exp40b급**
- 비교선: exp40b(30k, 14분), exp37(dense init+densify, 먼지 4.5배)
- 주의: no-densify에서는 opacity reset(3k/6k)도 재검토 필요 (원래 densify 보조 장치) — off/유지 A/B
- carve budget prune의 contribution proxy가 accum_visibility에 의존 → no-densify에서는 전 구간 누적으로 변경 필요 (코드 1줄)

## 선행 작업

1. train.py에 `--no_densify` 경로 확인/추가 (densify_until_iter=0으로 대체 가능한지 확인)
2. 44c용: RoMA(또는 LoFTR/DKM) 페어 매칭 + 삼각측량 스크립트 — keyframe 656장 기준 인접쌍 매칭
3. exp37 init 자산 재사용: `results/`의 dense init 3종 (148,564 / 144,830 / 65,095 pts)
