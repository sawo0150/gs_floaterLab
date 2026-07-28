# exp56 — mapping 고정비(픽셀/커널 launch) 절감: "gaussian 개수를 줄여도 왜 안 빨라지나"

- 상태: **완료 (2026-07-26).** Phase 0(기존 계측 재분석)으로 원인 확정(픽셀·
  커널-launch 고정비가 지배적, N-비례 항 아님) → Phase 1(`map()` iters
  10→7→5 스캔)에서 **`iters=7` 채택** — 시간 −16.1%(59.80→50.17s, 실시간
  여유 0.08배→0.23배), PSNR mean/kf 둘 다 개선(+0.21dB), map() 성사 횟수도
  22→26회 증가라는 전 지표 동시 개선(iters=10이 과잉 투자였음을 실측 확정).
  Phase 2(`render_downsample=2`를 이 새 baseline 위에 재검증)는 기각(시간
  이득 −1.7%뿐, PSNR −0.8dB 손해). Phase 3(coverage/GPU경합을 직접 겨냥한
  3축: `queue_size`↑·CUDA Graph·stream 분리)은 **전부 기각** — queue_size=4는
  역효과(시간·PSNR·coverage 셋 다 악화), CUDA Graph는 조사 후 구조적 부적합
  판정(구현 안 함), stream 분리는 **실행 중 CUDA illegal memory access로
  크래시**(custom rasterizer의 멀티스트림 미검증 상태 추정, 안전하게 되돌림 —
  다른 프로세스/GPU엔 영향 없음 확인). **부록(사용자 재확인 질문, 07-26)**:
  "병렬이라 경합 때문에 그런 거 아니냐"는 의심에 순수 직렬(경합 0)로 재검증 —
  render_downsample=2가 직렬에서도 rasterize/backward/loss_compute를 겨우
  1~3%만 줄임(병렬 6~8%보다도 작음) — 경합이 아니라 **커널-launch 고정비
  자체가 데이터量과 무관하게 지배적**이라는 Phase 0 결론이 경합과 독립적으로
  참임을 재확인. **Phase 4(신규, 07-27) — 이 세션 최대 발견**: "1iter당
  연산량을 줄이려면 뭘 건드려야 하나"는 질문에 `map_call` 세부 로그(기존에
  있었지만 한 번도 집계 안 해본 `iters`/`n_view`/`n_gauss` 메타데이터)를 처음
  집계 — **`map()` 호출 26회 중 단 2~3회(맵 최초 초기화 + IMU 재초기화 시
  `remove_all_gaussians()`로 맵 전체 삭제 후 재구축)가 mapping 전체 시간의
  49%를 차지**하고 있었음(이 호출들은 `iters=90~131`로, Phase 1이 튜닝한
  일반 keyframe의 `iters=7`과 전혀 다른 코드 경로). 이 초기화 반복 횟수의
  기준값 `Training.init_itr_num`(1050)을 600으로 낮춰 **`iters=7` 위에 추가로
  시간 −6.2%(50.17→47.08s)를 확보, PSNR은 사실상 무손실(mean −0.09dB 노이즈
  이내, kf는 오히려 +0.05dB), map() 성사 횟수도 26→30회 증가** — 채택.
  300까지 내리면 시간은 더 줄지만(46.15s) PSNR이 −0.35~0.44dB 실손실이라
  기각, 600이 스위트스팟. **exp53+54+55+56 누적: 47.08s, 실시간 배수
  0.72배(exp55 baseline 대비 −21.3%), kf PSNR 23.21(오히려 +0.26dB 개선).**
  **Phase 5(신규, 07-27) — 파트별 시간을 파라미터 회귀식으로 규명**: 세션
  전체(11개 run, 548개 실제 `map()` 호출)의 `map_call` opt-in 로그를 처음
  집계해 최소자승 회귀(`scripts/analysis/exp56_fit_timing_model.py`) —
  직렬(경합 0) 데이터에서 R²=0.93~0.998로 rasterize/loss_compute/backward/
  optimizer_step 각각이 `(iters, n_view, n_gauss, 해상도)`와 어떤 관계식인지
  정확히 도출(실측 5% 이내로 검증). 결론: **`iters × n_view`(반복 횟수 ×
  카메라 수)가 압도적 — gaussian 수 계수는 그 1/10, 해상도 계수는 통계적으로
  0**. 병렬 데이터로 다시 피팅하면 고정비 계수만 거의 2배(경합이 "커널
  launch 대기시간"만 정확히 부풀림을 계수로 확인). `n_view` 의존이 왜
  이렇게 큰지도 코드로 확인: `render()`가 원본 3DGS 코드 그대로라 애초에
  카메라 1대 전용(batch 미지원)이라, `map()`이 Python for문으로 카메라를
  하나씩 순차 처리하며 고정비를 매번 새로 지불하는 구조 — 잠재력 큰(뷰당
  고정비의 최대 91% 절감 가능) 다음 후보(rasterizer batch화)를 식별했으나
  CUDA 소스 수정이 필요해 고위험으로 별도 라운드 필요. **Phase 6(신규,
  07-27) — iters↓·n_view↑ 재배분(같은 view-op 예산, 품질 축) 시도, 기각**:
  Phase 5 회귀식에서 나온 "같은 iters×n_view면 시간은 그대로이니 뷰를
  다양하게 하면 품질이 오히려 좋아지지 않을까"라는 가설을 실측 — dead
  config였던 `Training.window_size`를 실제 로직에 연결(`current_window`
  상한 하드코딩 `10`을 대체)해 두 지점(window=15/iters=5, window=19/iters=4)
  테스트. **시간 예측은 정확히 맞았지만(거의 무변화) PSNR은 −1.1→−3.5dB로
  window를 키울수록 단조 악화** — 프론티어(최근 keyframe)가 과거 keyframe
  들과 제한된 gradient 예산을 나눠 쓰게 되면서 수렴이 희석되는 것으로 분석,
  3번째 지점은 추세가 명확해 실행 없이 기각 확정. window_size는 기본값
  10으로 원복(코드 연결 자체는 유지 — 향후 재검증 가능한 자산). **Phase 7
  (신규, 07-27) — window_size는 그대로, global 뷰 개수만 늘리기, 채택**:
  Phase 6의 실패 원인(프론티어가 과거 keyframe과 예산 경쟁)을 사용자가
  정확히 짚어 "프론티어 window는 안 건드리고 이미 있던 `include_global`
  메커니즘(iteration마다 과거 keyframe 랜덤 2개 추가)의 그 `2`만 늘리면
  안 되냐"고 제안 — 하드코딩된 `2`를 `Training.n_global_views`로 config화
  해 테스트. **결과: n_global=6·10 둘 다 PSNR +0.17~0.30dB 개선, 시간은
  거의 그대로(+0.25~0.9%)** — Phase 6과 정반대. 프론티어를 그대로 둔 채
  "덤으로" 다양성만 추가하니 수렴 방해 없이 순이득. 6과 10이 PSNR은 동급
  (수확체감)이라 시간·coverage·궤적이 더 나은 **`n_global_views=6` 채택**.
  **exp53+54+55+56 최종(갱신): 47.20s, 실시간 배수 0.73배, PSNR 22.97/23.43
  (exp55 baseline 대비 mean +0.36dB, kf +0.48dB).** **Phase 8(신규, 07-27) —
  batch 구현 전에 프로파일로 진짜 원인 확인, 대신 안전한 부수 발견을 적용**:
  사용자가 batch 구현을 요청해 `torch.profiler`로 `render()` 1회를 격리
  분석 — Python autograd 디스패치 오버헤드는 작아(0.1~0.14ms/call) 진짜
  고정비는 **CUDA 커널 실행 자체**임을 확인, 즉 진짜 batch화는
  forward.cu/backward.cu(~2800줄) 커널 자체에 카메라 batch 차원을 넣어야
  하는 큰 작업(그래디언트가 조용히 틀려질 위험, Phase 3보다 높은 위험도) —
  이번 세션에서 안전하게 검증까지 마치기 어렵다고 판단해 보류. 대신
  프로파일링 중 **`Camera.world_view_transform`/`full_proj_transform`/
  `camera_center`가 매 `render()` 호출마다(카메라 pose는 안 바뀌는데도)
  `torch.linalg.inv()`를 포함해 처음부터 재계산되고 있음을 발견** —
  R/T가 바뀌는 지점이 `update_RT()` 단 하나뿐임을 grep으로 확인한 뒤
  세 property에 캐싱 추가(그래디언트 수학은 전혀 안 건드리는 무위험
  변경). **결과: 시간 −3.0%(47.20→45.79s), PSNR +0.52/+0.45dB, map() 성사
  26→36회(+38%) — 전부 개선, 이 세션 최고 ROI 레버.** **exp53+54+55+56
  최종: 45.79s, 실시간 배수 0.70배(exp55 baseline 대비 −23.4%), PSNR
  23.49/23.88(exp55 baseline 대비 mean +0.88dB, kf +0.93dB).**
  **Phase 8b(신규, 07-27, 사용자 요청 "물어보지 말고 끝까지") — batch를
  실제로 구현·검증·통합, 결론은 "정확하지만 속도 이득 없음"**: 기존
  단일-카메라 CUDA 커널(수정 없음)을 C++에서 카메라 수만큼 루프 도는
  안전한 설계로 구현(`rasterize_points_batch.{h,cu}` 신규) — forward는
  순차 실행과 완전 bit-exact, backward는 float32 잡음 수준으로 일치(raw
  바인딩·Python 통합 레벨 둘 다 검증). **1차 실전 실행에서 PSNR 붕괴
  (6.65dB)를 실측으로 발견** — `render_batch()`의 `depth` 텐서가
  `render()`의 `(1,H,W)` 관례와 다른 `(H,W)` shape를 반환해
  `get_loss_normal()`의 reshape 로직이 매 호출 조용히 실패(`except
  Exception: pass`가 은폐)하고 있었음, 격리 수치검증은 이 project-specific
  loss 함수를 안 건드려서 못 잡음 — 수정 후 재실행하니 크래시 없고
  PSNR도 오히려 소폭 개선(23.55/24.07)했지만 **시간은 개선 없음(45.79→
  47.37s), 정규 호출 평균 시간이 761.6ms→755.7ms로 사실상 동일(<1%)** —
  Phase 8에서 프로파일로 예견한 대로 "진짜 병목은 CUDA 커널 실행 자체라
  Python 오버헤드만 없애는 걸로는 이득이 없다"가 실측으로 확정됨.
  `batch_render` 기본값 false로 원복(채택 안 함), 코드는 향후 커널-레벨
  batch화의 기반 자산으로 보존.
- 배경: 사용자 관찰 — "실시간이 되긴 하는데 품질이 썩 좋지는 않다. gaussian
  개수를 줄여도 그만큼 속도가 안 빨라지는 것 같은데 왜 그런가." exp55에서
  평균 gaussian 수를 −35.9% 줄였지만 순수 mapping 시간은 −12.2%뿐이었고
  ([[exp55_adaptive_density_carve_plan]] 부록), exp54 축6+2에서도 이미 같은
  현상이 관측됐다("gaussian 개수 자체가 더 이상 지배 변수가 아님", 118쪽 참조)
  — 이번엔 그 이유를 `_Sect` 타이밍 계측(이미 코드에 있는 rasterize/loss_compute/
  backward/optimizer_step/densify_prune 세부 태그)으로 직접 뜯어봄.

## Phase 0 — 기존 timing.csv 재분석으로 원인 확정 (신규 실행 없이 완료)

exp55의 직렬 재실행(`exp55_serial_final`, GPU 경합 없는 순수 110개 keyframe
전부 처리)의 `timing.csv`를 `map_dispatch`(=`self.map()` 1회 호출) 내부
세부 태그별로 합산 — 이 값이 이미 exp55 부록의 "map() 핵심 5단계 68.16s"의
내역이다:

| 구간 | 합계(110회) | 비중 | gaussian 개수(N) 의존성 |
|---|---:|---:|---|
| **rasterize** | 27.18s | **40%** | O(N) 겹침 검사 + O(픽셀) 블렌딩 — 혼합 |
| **backward** | 23.34s | **34%** | rasterize와 동형 — 혼합 |
| **loss_compute** | 16.48s | **24%** | **O(픽셀)만** — L1/SSIM/depth-L1/carve 전부 elementwise, N과 무관 |
| optimizer_step | 1.04s | 1.5% | O(N) (파라미터 수) — 절대량 작음 |
| densify_prune | 0.12s | 0.2% | 호출 자체가 드묾(11/110회만) |
| (map_dispatch 총합 대비 미계측 잔차) | 7.31s | 10% | 데이터 이동·`add_next_kf`·python 루프 |

**결론**: keyframe당 `map()`은 이미지 해상도(464×464, 고정)에 대해 `iters`번
반복되는 구조라, 시간의 상당 부분이 **N과 무관한 고정비**다.
- `loss_compute`(24%)는 전부 픽셀 단위 elementwise 연산 — carve loss 추가로
  더 늘었지만(exp55 Phase3) N에는 애초에 의존하지 않음.
- `rasterize`+`backward`(74%)는 이론상 N에 비례하는 항이 있지만, exp54
  축6+2(N을 122,957→116,143으로 눌러도 시간 그대로)·exp55 Phase2(N −35.9%,
  이 두 구간은 "소폭"만 감소)로 **이 gaussian 개수 규모(85k~130k)·이 해상도
  조합에서는 픽셀/타일 처리 고정비가 N-비례 항을 압도**한다는 게 두 번
  반복 확인됨.
- 부가로 병렬 모드(`exp55_final_confirm`, 22회 성사)의 같은 구간 평균은
  직렬 대비 rasterize 3.4배·backward 2.3배·loss_compute 3.4배 더 걸림 —
  GPU 경합이 tracking뿐 아니라 mapping 자신의 GPU 연산도 부풀리고 있음을
  시사(단, 병렬은 window 구성이 다른 22회, 직렬은 110회라 완전한 controlled
  비교는 아님 — 방향성 참고용).

**함의**: "gaussian 개수를 줄이는" 레버(exp54 축1/2/6, exp55 Phase1/2)는
이미 한계에 도달했다. 다음으로 시간을 줄이려면 **(a) N과 무관한 고정비
자체를 줄이거나(해상도↓, iters↓) (b) GPU 경합을 줄이는** 방향이어야 한다.

## Phase 1 — `map()` iters 하향 스캔 (10→7, 10→5)

exp54 축3(iters 10→5)이 이미 한 번 기각됐지만, 그건 **exp53 이전의
tracking-bound 구간**(tracking이 전체의 91%)에서 테스트된 것이라 "mapping을
반으로 깎아도 critical path가 tracking에 있어 안 줄어든다"는 게 기각 사유였다
(문서상 원인 자체가 지금과 다름). 지금은 exp53으로 tracking을 47.5% 줄이고
mapping이 pure 기준 압도적 비중(74%)을 차지하는 상태로 바뀌었고, Phase 0로
`iters`가 곱으로 걸리는 rasterize/backward/loss_compute가 시간의 74%+24%임을
재확인했으니 — **다시 테스트할 가치가 있는 축**. 오늘 오전 반대 방향(10→15/20)
테스트에서 "iters를 올리면 큐 드롭으로 처리 keyframe 수만 준다"는 게 확인됐으므로,
이번엔 **내리는** 방향 — 반복을 줄이면 `map()` 1회가 빨라져 mapper가 밀리지
않고 오히려 더 많은 keyframe을 처리할 수 있는지가 핵심 질문.

측정: 1253 전체, 현재 최종 채택 레시피(adaptive_density on, carve_lambda=0.05,
ppm on) 위에서 `iters`만 7, 5로 변경. 비교 기준선은 `exp55_carveon_anchors`
(iters=10, carve on) — 59.80s, PSNR 22.61/22.95, evo Sim3 2.41cm, map() 22회.

| iters | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 |
|---|---:|---:|---:|---:|---:|
| 10(baseline) | 59.80s | 0.92배 | 22.61 / 22.95 | 2.41cm | 22회 |
| **7(채택)** | **50.17s** | **0.77배** | **22.82 / 23.16** | 2.41cm | **26회** |
| 5 | 49.44s | 0.76배 | 22.80 / 23.19 | 2.42cm | **32회** |

**iters=7 — 전 지표 동시 개선(예상 밖 압승)**: 시간 −16.1%(59.80→50.17s,
실시간 여유가 0.08배에서 0.23배로 3배 확대), PSNR mean/kf 둘 다 개선(+0.21/
+0.21dB), evo APE Sim3 동일(2.41cm), 게다가 **map() 성사 횟수도 22→26회로
오히려 증가**. Phase 0 가설이 정확히 들어맞음: `iters=10`은 이 지점에서
과잉 투자였고, 반복을 줄이면 (a) 고정비가 곱으로 줄어 `map()` 1회가 빨라지고
(b) mapper가 큐에서 덜 밀려 더 많은 keyframe을 처리하게 되며 — coverage
증가가 반복 감소로 인한 개별 정밀도 손실을 상쇄하고도 남음. 오늘 오전
반대 방향(10→15/20, coverage 감소로 역효과) 테스트와 정확히 대칭인 결과.

**iters=5 — 수확체감 확인, 7이 더 나은 지점**: 시간은 7 대비 거의 그대로
(50.17→49.44s, −1.5%뿐), PSNR·evo는 둘 다 노이즈 범위 내 동급(mean만 −0.02dB,
kf는 오히려 +0.03dB — run-to-run 노이즈 ±0.24~0.33dB보다 훨씬 작은 차이).
map() 횟수는 26→32회로 계속 늘지만 시간·품질엔 더 이상 보탬이 안 됨 —
**per-call 고정비(카메라 init·데이터 이동 등 iters와 무관한 부분, Phase 0의
"미계측 잔차 10%")가 바닥에 가까워지는 지점**으로 해석. **`iters=7`을 채택**
(5와 사실상 동급이지만 반복 깊이를 조금 더 남겨 안전마진 확보), `gs_backend.py`
정규 keyframe `map()` 호출을 `iters=10→7`로 영구 변경.

## Phase 2 — `render_downsample` 현재 최종 레시피 위 재검증

exp54 축4(`render_downsample=2`)는 **exp55 이전**(adaptive_density/carve
없음, `pcd_downsample=128` 기준)의 구 baseline 위에서 테스트돼 −4.2%
시간(58.09s)·−0.8dB PSNR로 "이미 실시간이라 감수할 이유 없음"으로 미채택
됐었다. **Phase 1에서 `iters=7`을 채택**했으므로, 이번엔 그 위에(=exp55
Phase2+3+exp56 Phase1) `render_downsample=2`를 추가로 얹어 재검증 — 두
레버가 겹칠 때 시너지(둘 다 rasterize/backward/loss_compute를 줄이는
동일 방향)인지 상쇄인지 확인.

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 |
|---|---:|---:|---:|---:|
| **iters=7 단독(baseline, 채택)** | 50.17s | 0.77배 | **22.82 / 23.16** | 2.41cm |
| iters=7 + render_downsample=2 | 49.31s | 0.76배 | 21.98 / 22.65 | 1.91cm |

**기각 — 상쇄가 아니라 손해만 추가**: iters=7 위에 render_downsample=2를
더하면 시간은 겨우 −1.7%(50.17→49.31s) 더 줄고 PSNR은 −0.84/−0.51dB
악화. Phase 1(iters↓)에서 이미 실시간 여유가 0.23배로 크게 벌어진 상태라
이 추가 −1.7%는 실익이 거의 없고, 픽셀 해상도를 줄이는 손실은 고스란히
남음 — exp54 축4 때와 같은 결론(품질 대비 시간 이득이 나쁨)이 새 baseline
위에서도 재확인됨. **기각, `render_downsample`은 config에서 제거(기본 1
유지)**. evo APE만 1.91cm로 개선됐는데 이는 트래킹과 무관한 렌더 해상도
변경이라 우연/노이즈로 해석(가드레일 통과에는 어차피 문제없는 수준).

## 최종 채택 설정 (Phase 1 + Phase 4 + Phase 7 + Phase 8)

```yaml
# vigs/gs_backend.py, 정규 keyframe map() 호출
self.map(self.current_window, iters=7, include_global=True,
         max_viewpoints=self.window_size + 1 + self.n_global_views)  # Phase 1/7

# config/aria1253.yaml, Training:
init_itr_num: 600      # 1050 -> 600 (Phase 4)
window_size: 10         # dead config를 실제 로직에 연결(Phase 6), 기본값 유지
n_global_views: 6       # 2 -> 6 (Phase 7)

# vigs/gaussian/utils/camera_utils.py: world_view_transform/full_proj_transform/
# camera_center property 캐싱, update_RT()에서만 무효화 (Phase 8)
```
(`render_downsample`은 config에 넣지 않음 — 기본 1/off 유지. exp55의
`pcd_downsample`/`adaptive_density`/`carve_lambda` 등 나머지 설정은 그대로.)

## 최종 결과 요약 (exp53+54+55+56 누적, 1253 전체)

| | exp55 최종(iters=10, init=1050) | +Phase1(iters=7) | +Phase4(init=600) | +Phase7(n_global=6) | +Phase8(카메라 캐싱, 최종) | 누적 변화 |
|---|---:|---:|---:|---:|---:|---:|
| 온라인 루프 총합 | 59.80s | 50.17s | 47.08s | 47.20s | **45.79s** | **−23.4%** |
| 실시간 배수(예산 65.1s) | 0.92배 | 0.77배 | 0.72배 | 0.73배 | **0.70배** | 여유 3.7배 확대 |
| PSNR mean/kf | 22.61 / 22.95 | 22.82 / 23.16 | 22.73 / 23.21 | 22.97 / 23.43 | **23.49 / 23.88** | mean **+0.88dB**, kf **+0.93dB** |
| evo APE Sim3 | 2.41cm | 2.41cm | 2.07cm | 1.95cm | **2.42cm** | 동급 |
| map() 성사 횟수 | 22회 | 26회 | 30회 | 26회 | **36회** | +64% |

**사용자 질문("품질 개선 방법 없나" → "1iter당 연산량 줄이려면 어디를
건드려야 하나" → "카메라 뷰를 늘리면 안 되나")에 대한 답**: iters를 올리는
방향(Phase 1 이전 테스트)은 틀렸고, 내리는 방향(Phase 1)이 시간·품질·
coverage를 동시에 개선했다. "1iter당 연산량의 95%+가 고정 오버헤드"라는
Phase 0/2 결론을 더 파고들어 **Phase 4에서 진짜 핵심 지점을 찾음**: `map()`
호출 26회 중 단 2~3회(초기화/IMU 재초기화)가 전체 mapping 시간의 49%를
차지 — `init_itr_num`을 600으로 낮춰 추가 절감(무손실). Phase 5 회귀분석이
"카메라 수(n_view)가 시간을 지배한다"는 걸 계수로 확정하자 사용자가 "그럼
뷰를 늘리면 품질이 좋아지지 않나"를 제안 — Phase 6(window 자체를 키움)은
프론티어 gradient 희석으로 대실패(PSNR −1~3.5dB)했지만, **Phase 7(프론티어
window는 그대로 두고 과거-뷰 곁눈질만 늘림)은 성공** — PSNR mean/kf 둘 다
개선(+0.24/+0.22dB)에 시간 비용은 무시할 수준(+0.25%). 마지막으로 사용자가
batch 렌더링 구현을 요청 — 프로파일로 먼저 확인해보니 진짜 CUDA 커널
비용이라 batch화 자체는 그래디언트 위험이 큰 별도 작업으로 보류했지만,
그 과정에서 **Phase 8: 카메라 pose가 안 바뀌는데도 매 view마다 재계산되던
행렬 역산(`torch.linalg.inv()`)을 캐싱**하는 무위험 최적화를 발견·적용 —
시간 −3.0%, PSNR +0.52/+0.45dB, coverage +38%로 이 세션 최고 ROI였다.
**exp55 baseline 대비 최종 누적: 시간 −23.4%(45.79s, 실시간 배수 0.70배),
PSNR mean +0.88dB·kf +0.93dB, 궤적도 동급** — "시간을 거의 1/4 줄이면서
PSNR을 거의 1dB 끌어올린" 결과.

## Phase 3 — coverage/경합을 직접 겨냥한 3축 (2026-07-26, 사용자 요청)

exp56 Phase 1/2로 "N/해상도를 줄이는" 레버가 소진됐음이 확정된 뒤, 사용자가
제안한 다음 3개 축을 전부 실행:

1. **`Training.queue_size`(2→4) 확대** — 오버헤드(iters·해상도)는 그대로 두고
   드롭되는 keyframe만 줄여 coverage를 늘리는 방향.
2. **커널 launch를 CUDA Graph로 묶기** — 조사 결과 **기각(미실행)**, 사유는
   아래 참조.
3. **GPU 경합 완화(CUDA stream 분리)** — mapping을 tracking과 분리된 별도
   CUDA stream에서 실행해 legacy default stream 공유로 인한 암묵적 동기화를
   제거.

### 축2(CUDA Graph) — 조사 후 기각, 구현 안 함

**이유**: CUDA Graph capture는 재생(replay) 구간의 모든 텐서가 **고정된 메모리
주소·shape**를 유지해야 하는데, VIGS의 `map()` 루프는 구조적으로 이 조건과
맞지 않음:
- `densify_and_prune()`가 gaussian 파라미터(`_xyz`/`_opacity`/...)를 주기적으로
  cat/prune해 메모리를 재할당 — capture된 그래프가 무효화됨(다행히 한 `map()`
  호출 내에서는 대개 발생 안 함, 26회 중 4회만 densify 발생).
- **keyframe마다 gaussian 개수(N)와 `current_window`의 카메라 구성이 다름** —
  즉 거의 매 `map()` 호출마다 새로 capture해야 함. 특히 exp55의 content-adaptive
  예산(축2)이 keyframe마다 다른 N을 만드는 설계라 이 문제가 구조적으로 더 심함.
- `torch.optim.Adam`이 `capturable=True` 없이 기본 설정으로 쓰이고 있어(코드
  확인, `gaussian_model.py:472`) graph-safe하지 않음 — 이것만 고쳐도 별도
  검증이 필요한 변경.
- 대안으로 `torch.compile(mode="reduce-overhead")`(PyTorch가 CUDA Graph
  안전장치를 자동 처리)도 검토했으나, 동일한 이유(매 호출마다 다른 N/shape)로
  **컴파일을 거의 매번 다시 해야 해서 컴파일 비용이 iters=7 루프가 절약하는
  시간보다 커질 가능성이 높음** — 이 workload(매 keyframe마다 동적 N)는애초에
  CUDA Graph/torch.compile이 설계된 "고정 배치 크기 반복 학습"과 정반대 패턴.
- **결론**: 구현하지 않음. 조용히 잘못된 결과를 낼 위험(그래프가 stale
  메모리를 참조)이 큰데 이득은 불확실 — exp53 축D(재학습 없이 구현 불가)와
  같은 성격의 "조사 후 기각".

### 축1(queue_size)·축3(CUDA stream 분리) — 구현·실행

- **축1**: `Training.queue_size: 2→4`.
- **축3**: `vigs.py`에 `Training.gs_dedicated_stream`(신규, 기본 false) 플래그
  추가 — true면 `self._gs_stream = torch.cuda.Stream()`을 만들어 `_gs_worker`의
  `process_track_data` 호출을 `with torch.cuda.stream(self._gs_stream):`로
  감쌈. **⚠ 구현 중 레이스 컨디션 실측 전에 발견·수정**: 기존 코드는 tracking
  스레드와 mapping 스레드가 명시적 stream 관리 없이 **동일한 legacy default
  stream을 공유**하고 있었음(`grep`으로 전체 레포에 `cuda.Stream`/`cuda.stream`
  이 전무함을 확인) — mapping을 별도 stream으로 분리하면 `demo.py`의
  `_gs_queue.join()` 직후 메인 스레드가 곧바로 `save_ply`/`eval_rendering`으로
  gaussian GPU 텐서를 읽는데, `queue.join()`은 파이썬 호출이 반환됐음만
  보장하지 GPU 커널 완료를 보장하지 않음 — **stream 동기화 없이는 아직 끝나지
  않은 densify/optimizer.step() 쓰기와 경합해 PLY/PSNR이 조용히 오염될 수
  있는 실제 레이스**였음. `demo.py`의 `_gs_queue.join()` 직후에
  `torch.cuda.current_stream().wait_stream(vigs._gs_stream)`을 추가해 해결
  (실행 전에 코드 리딩으로 발견 — [[feedback_verify_unmeasured]] 원칙:
  실측 전에 이런 위험은 코드로 직접 확인해야 함).

**측정** (iters=7 baseline 위, 1253 전체):

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 |
|---|---:|---:|---:|---:|---:|
| baseline(queue=2, stream 공유) | 50.17s | 0.77배 | 22.82 / 23.16 | 2.41cm | 26회 |
| queue_size=4 | 52.38s | 0.80배 | 22.57 / 23.05 | 1.91cm | **25회** |
| gs_dedicated_stream=true | **크래시** | | | | |

**축1(queue_size=4) — 기각, 역효과**: 시간 +4.4%(50.17→52.38s), PSNR
mean/kf 둘 다 악화(−0.25/−0.11dB), **map() 성사 횟수도 26→25회로 오히려
감소** — "버퍼를 키우면 더 많이 처리될 것"이라는 예상과 정반대. 원인 추정:
드롭 정책(`while full: get_nowait()`)은 큐 크기와 무관하게 "최근 N개만
유지"이므로, 버퍼가 클수록 mapper가 밀렸을 때 **더 오래된(최대 4개 밀린)
packet부터 순서대로 처리**하게 돼 신선도가 오히려 나빠짐(queue=2일 땐
최대 2개 밀린 packet까지만 허용). 처리량 자체도 늘지 않아 순이득이 없음 —
**기각, `queue_size=2` 유지**.

**축3(gs_dedicated_stream) — 실행 중 크래시, 기각**: keyframe 10~11 부근에서
`torch.AcceleratorError: CUDA error: an illegal memory access was encountered`
발생, GPU 컨텍스트가 오염돼 이후 모든 CUDA 호출이 연쇄 실패 — 프로세스
강제 종료 후 `nvidia-smi`로 GPU가 깨끗한 상태(459MiB, 유휴 프로세스 없음)로
복구됐음을 확인, 다른 작업엔 영향 없음.

**원인 분석**: 레포 전체에 명시적 CUDA stream 관리가 전혀 없었다는 걸
구현 전에 이미 확인했었는데(`grep`으로 확인), 즉 지금까지 tracking과
mapping은 **암묵적으로 legacy default stream을 공유**하고 있었고, 이
legacy null stream 특유의 "다른 모든 stream과 교차 동기화"하는 특성이
사실상 두 스레드의 GPU 작업을 순차화해 안전하게 만들어주고 있었다.
mapping을 별도 stream으로 옮기자 **진짜 동시 실행**이 되면서, custom CUDA
rasterizer(`thirdparty/diff-gaussian-rasterization`, 이 프로젝트 계열의
전형적인 hand-written CUDA extension)가 멀티스트림 환경에서 안전하다고
검증된 적이 없는 내부 상태(재사용되는 정적/스크래치 버퍼 등, 추정)와
충돌한 것으로 판단됨 — 정확한 라인은 CUDA 커널 소스까지 파고들어야 하는데
투자 대비 낮은 우선순위로 판단해 더 파지 않음.

**결론 — 기각(구현 안전성 문제로 재시도 안 함)**: `gs_dedicated_stream`
플래그는 코드에 남겨두되(기본 false, off) `vigs.py`에 "패치 없이 켜지
말 것" 경고 주석 추가. rasterizer CUDA 소스를 멀티스트림 안전하게 고치지
않는 한 이 축은 닫힌 것으로 취급 — exp53 축D(재학습 없이 구현 불가)·exp56
축2(CUDA Graph, 구조적 부적합)와 같은 성격의 "조사/시도 후 기각".

**Phase 3 종합**: 3축(queue_size↑·CUDA Graph·stream 분리) 전부 기각 —
coverage/경합을 직접 겨냥한 접근은 이번 아키텍처(legacy default stream
암묵적 동기화에 의존하는 스레드 안전성, 큐의 "최근 N개만 유지" 드롭 정책)
에서는 추가 이득을 못 냄. **exp56의 실질적 성과는 Phase 1(iters=7)
하나로 확정.**

## 부록 — Phase 2(render_downsample) 결론이 GPU 경합 때문 아니냐는 재검증 (2026-07-26)

사용자 질문: "병렬로 테스트해서 그런 거 아니냐, 직렬이면 GPU 연산량 줄어든
만큼 mapping도 줄어야 하는 거 아니냐" — Phase 2가 병렬(`parallel: true`)
에서만 테스트됐다는 점을 정확히 짚은 재검증 요청. 순수 직렬(`parallel:
false`, tracking과 GPU 경합 0)로 iters=7 baseline과 render_downsample=2를
다시 비교(1253 전체, `map_dispatch` 세부 태그 per-call 평균):

| | 직렬, 원해상도(iters=7) | 직렬, render_downsample=2 | 변화 |
|---|---:|---:|---:|
| rasterize | 192.59ms | 186.07ms | −3.4% |
| backward | 160.80ms | 159.16ms | −1.0% |
| loss_compute | 118.51ms | 116.28ms | −1.9% |

**경합 가설 기각, Phase 0/2 결론 재확인**: 경합이 전혀 없는 직렬에서도
픽셀 수를 1/4로 줄였는데 겨우 1~3%만 줄어듦 — 오히려 병렬 측정치(−5.5~
−7.7%, 본문 Phase 2 표)보다도 작음. 즉 "병렬 경합이 데이터量 감소 효과를
가려서 작아 보였다"는 가설은 틀렸고, **데이터量(픽셀·gaussian 수) 자체가
직렬/병렬과 무관하게 이 시간 구조를 거의 안 좌우한다**는 게 재확인됨.

대조로 `iters`는 직렬에서도 확실히 비례해서 줄었음(같은 방식으로 비교,
참고: iters=10 직렬은 exp55_serial_final의 rasterize 247.06ms/backward
212.20ms/loss_compute 149.78ms):

| | iters=10(직렬) | iters=7(직렬) | 변화 |
|---|---:|---:|---:|
| rasterize | 247.06ms | 192.59ms | **−22.0%** |
| backward | 212.20ms | 160.80ms | **−24.2%** |
| loss_compute | 149.78ms | 118.51ms | **−20.9%** |

**결론**: "GPU 연산량"은 두 가지 다른 축이었다 — **(a) 커널 한 번이 처리하는
데이터量**(픽셀 수·gaussian 수, Phase 0/2가 다룬 것)과 **(b) 커널을 호출하는
횟수**(`iters`, Phase 1이 다룬 것). 이 규모(gaussian 10만 대, 464×464)에서는
(a)는 거의 공짜(launch 오버헤드에 묻힘, 직렬·병렬 무관하게 일관), (b)만
실제로 시간에 거의 선형으로 반영됨. 병렬/직렬 여부와 무관한 구조적 사실임을
직접 실측으로 확정.

## Phase 4 — 새로 발견: map() 호출 26회 중 2~3회(초기화/재초기화)가 mapping 시간의 49%

사용자 질문("1iter당 연산량을 줄이려면 어떤 핵심 부분을 건드려야 하는가")에
답하려 `map_call` 세부 로그(`iters=`/`n_view=`/`n_gauss=` 메타데이터 포함,
기존 코드에 이미 있던 opt-in 계측)를 처음으로 직접 파싱해봄 — Phase 0~3은
전부 "map_dispatch"(호출 전체 합)만 봤지, **호출 하나하나를 구분해서 본 적이
없었다**.

**발견**: `map()` 호출 26회는 종류가 균일하지 않다 — 코드상 세 가지 호출
경로가 있음(`gs_backend.py:299/302/305`):

| 호출 종류 | `iters` | 발생 조건 |
|---|---|---|
| 일반 keyframe | 7(exp56 채택값) | 매 keyframe마다(21회) |
| PGBA(pose graph 보정) | 20(고정) | 루프클로저 등 pose 업데이트 시(4회) |
| **초기화/재초기화** | `init_itr_num // len(current_window)` = **95~131** | 시퀀스 최초 1회 + `remove_all_gaussians()` 호출 시(IMU 늦은 초기화, `track_frontend.py:257`, `t1==imu_late_init_from`일 때 맵 전체를 삭제하고 처음부터 다시 채움) |

**실측(exp56_iters7 run 재분석)**: 이 "초기화/재초기화" 호출은 26회 중
단 2~3회뿐인데(`map_call` 로그상 iters=131 1회 + iters=95 2회 — 정확히
왜 2회인지는 미해결, 아래 한계 참조), **합쳐서 19.98초** — 일반 keyframe
21회 합(16.65초)보다 크고, **전체 mapping 시간(40.55초)의 49.3%**를 차지함.
`remove_all_gaussians()`가 `self.gaussians = GaussianModel(0, ...)`로
gaussian을 통째로 삭제하고 `self.initialized = False`로 되돌리기 때문에,
그 다음 keyframe에서 "첫 keyframe"과 똑같은 무거운 초기화 경로(`init_itr_num
//len(current_window)`, 지금 규모로는 iters 90~131)를 다시 타는 구조.

**함의**: Phase 1(`iters=7`)은 26회 중 21회(일반 keyframe)에만 적용됐다 —
초기화/재초기화 경로는 손도 안 댐. 여기가 지금까지 발견된 것 중 **가장 큰
단일 절감 여지**(호출 2~3개에 전체 시간의 절반이 몰려있음).

**테스트**: `Training.init_itr_num`(현재 1050, 초기화 반복 횟수의 기준값)를
300으로 낮춰(≈3.5배 절감) 1253 전체 재실행. 초기화/재초기화 경로에만 영향
(정규 keyframe의 `iters=7`은 무관), 대신 맵의 "첫 기하 골격" 품질이
낮아질 위험이 있어 PSNR·evo를 함께 확인.

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 | 초기화 호출 시간(3회 합) |
|---|---:|---:|---:|---:|---:|---:|
| baseline(init_itr_num=1050) | 50.17s | 0.77배 | 22.82 / 23.16 | 2.41cm | 26회 | 19.98s(49.3%) |
| init_itr_num=300 | 46.15s | 0.71배 | 22.38 / 22.81(**−0.44/−0.35dB**) | 1.91cm | 34회 | 6.99s(19.5%) |
| **init_itr_num=600(채택)** | **47.08s** | **0.72배** | **22.73 / 23.21**(mean −0.09, kf **+0.05**) | 2.07cm | **30회** | 12.96s(34.7%) |

**init_itr_num=300은 너무 세게 깎음**: 시간·coverage는 가장 좋지만 PSNR이
−0.35~0.44dB 하락 — 이 프로젝트가 실측한 run-to-run 노이즈(±0.24~0.33dB)를
벗어나는 **진짜 품질 비용**. 초기화/재초기화 경로(맵을 처음부터 짓는 "cold
start" 순간)는 정규 keyframe보다 반복이 더 필요하다는 뜻으로 해석 —
95~131회에서 27~37회까지(약 1/3.5) 깎은 건 과했음.

**init_itr_num=600 채택**: 시간 −6.2%(50.17→47.08s, iters=7 위에 추가 절감),
PSNR은 mean만 −0.09dB(노이즈 이내)·kf는 오히려 +0.05dB — **사실상 무비용**.
초기화급 호출 3회의 합이 19.98s→12.96s(−35.1%)로 줄었고, 전체 mapping
시간에서 차지하는 비중도 49.3%→34.7%로 낮아짐(여전히 크지만 훨씬 완화).
map() 성사 횟수도 26→30회로 늘어(+15%) — iters=7 때와 같은 패턴("호출을
가볍게 하면 mapper가 덜 밀려 더 많이 처리한다")이 여기서도 재현됨.
evo APE Sim3도 2.07cm으로 동급/개선.

**exp53+54+55+56 누적 최종**: 47.08s, 실시간 배수 **0.72배**(exp55 baseline
59.80s 대비 **−21.3%**, iters=7 단독 채택 시점 50.17s 대비 추가 −6.2%).

**한계(정직하게 기록)**: `remove_all_gaussians()`는 코드상
`self.t1 == self.imu_late_init_from`(정확히 한 번만 참이 되는 조건)에서만
호출되는 것으로 확인했는데, 실측 로그엔 "초기화급" 호출이 (최초 1회 +
이 재초기화 1회 = 총 2회여야 할 것 같은데) 2회의 `iters=95` 로그가 잡혀
총 3회로 보임 — 정확한 원인(같은 재초기화 이벤트가 이후 packet에서 한 번
더 무거운 경로를 타는 부수효과인지, 다른 트리거가 있는지)은 미해결. 다만
"초기화급 호출이 극소수인데 전체 시간의 절반 가까이를 차지한다"는 헤드라인
결론 자체는 정확한 횟수(2 vs 3)와 무관하게 견고함.

## Phase 5 — 파트별 시간을 파라미터 회귀식으로 규명 (2026-07-27, 사용자 요청)

**요청**: "40s를 파트별로 나누고, 각 파트가 어떤 param에 종속되는지, 총
시간과 param의 관계식(추세선)을 꼼꼼히 규명해달라." Phase 0~4는 전부
`map_dispatch`(호출 전체 합) 또는 개별 호출 몇 개를 손으로 비교하는
수준이었음 — 이번엔 **기존에 이미 있었지만 한 번도 집계 안 해본
`map_call` opt-in 로그**(`rasterize`/`loss_compute`/`backward`/
`optimizer_step`마다 `iters`/`n_view`/`n_gauss` 메타데이터 포함)를 이 세션
전체 실험(exp55~56, 11개 run, 548개 실제 `map()` 호출)에서 전부 파싱해
최소자승 회귀로 관계식을 피팅. 스크립트:
`scripts/analysis/exp56_fit_timing_model.py`(재사용 가능, 신규 run 추가 시
`RUNS` 리스트에 추가하면 재실행 가능).

### 파트 구조부터 — `map()`의 실제 루프

```python
for _ in range(iters):                          # iters번 반복
    for viewpoint in current_viewpoints:         # 매 iteration마다 n_view대 카메라를
        render(viewpoint, ...)                   #   "한 대씩" 순차 호출 (rasterize)
        get_loss_mapping_rgbd(...)               #   (loss_compute)
    loss_mapping.backward()                      # iteration당 1번(전체 뷰 합산 후)
    optimizer.step()                             # iteration당 1번
```
`rasterize`·`loss_compute`는 **iteration마다 카메라 1대씩 순차 처리**하는
구조라 자연 단위가 "뷰-연산 1회"(`iters × n_view`)이고, `backward`·
`optimizer_step`은 iteration당 1번만 불리지만 그 안에서 다루는
그래프 크기/파라미터 수가 `n_view`·`n_gauss`에 비례.

### 회귀 결과 (직렬 데이터만, GPU 경합 없음 — n=330 실제 호출)

| 파트 | 관계식 | R² |
|---|---|---:|
| rasterize | `1.473·(iters·n_view) + 0.00545·(iters·n_view·n_gauss/1000) − 0.035·(iters·n_view·pixratio)` | **0.992** |
| loss_compute | `0.956·(iters·n_view) + 0.00207·(iters·n_view·n_gauss/1000) − 0.024·(iters·n_view·pixratio)` | **0.994** |
| backward | `−1.623·iters + 1.126·(iters·n_view) + 0.126·(iters·n_gauss/1000)` | **0.929** |
| optimizer_step | `1.739·iters − 0.095·(iters·n_view) + 0.001·(iters·n_gauss/1000)` | **0.998** |

(`pixratio` = 1.0 원해상도, 0.25 = `render_downsample=2`. 계수의 부호/크기가
±0.02~0.09 수준으로 작은 항은 통계적으로 0과 구분 안 됨 — 잡음.)

**검증(회귀에 실제로 쓰인 값이지만 별도로 대조)**: `iters=95, n_view=11,
n_gauss=18103`(Phase 4에서 발견한 그 초기화 호출) → 모델 예측 **3,927ms**,
실측 **3,734ms**(오차 5%).

### 파트별로 뭐가 지배적인가 — 계수를 직접 비교

| 항 | 대표 계수 크기(뷰-연산 또는 iteration당) | 지금 규모에서 기여 |
|---|---:|---|
| **고정비(a)** — `iters`·`n_view` 자체 | rasterize 1.47ms + loss_compute 0.96ms + backward(n_view항) 1.13ms **≈ 뷰-연산 1회당 3.5ms** | **가장 큼** |
| gaussian 수(b) | 1000개당 0.005~0.13ms | n_gauss 5만 기준 rasterize·loss_compute 합쳐 ≈0.4ms(뷰-연산당) — 고정비의 10% 남짓 |
| 해상도(c) | −0.02~−0.03(잡음, 사실상 0) | 무시 가능 |

**즉 시간을 지배하는 건 압도적으로 `iters`와 `n_view`(카메라 수)의 곱이지,
gaussian 수·해상도가 아니다** — Phase 0~2가 이미 보인 결론을 이번엔 정확한
숫자(계수)로 다시 확인.

### 병렬(실배포 상태)에서는 고정비(a)만 부풀어

같은 피팅을 병렬 데이터(n=186, GPU 경합 있음)로 하면 R²는 0.73~0.86으로
떨어지지만(경합이 노이즈를 더함) **고정비(a) 계수만 거의 2배**로 뜀 —
rasterize 1.47→2.69, loss_compute 0.96→1.76, backward의 `n_view` 계수도
1.13→1.93. **gaussian/해상도 계수는 거의 그대로.** GPU 경합은 "커널
launch·스케줄링 대기시간"만 정확히 부풀리지, 데이터 처리 자체를 느리게
만들지 않는다는 걸 계수 수준에서 확인 — exp55 부록의 정성적 "경합이
tracking을 부풀린다"는 관찰을 mapping 쪽에서도 정량 재확인한 셈.

### 왜 하필 `n_view`(카메라 수)에 이렇게 크게 종속되는가 — 코드 레벨 원인

`vigs/gaussian/renderer/__init__.py::render()`를 직접 확인 — 이건 **원본
3DGS(Inria/GRAPHDECO) 코드 그대로**이고, 원래 설계 자체가 **카메라 1대만
받아서 그때그때 `GaussianRasterizationSettings`/`GaussianRasterizer`를
새로 만들어 처리**하는 함수다(batch 차원 없음, `viewmatrix`/`projmatrix`가
스칼라 하나). VIGS의 `map()`은 멀티뷰 supervision이 필요해 이 단일-카메라
함수를 Python for문으로 `n_view`번 반복 호출하는 구조를 얹었을 뿐, 원본
함수 자체는 여러 카메라를 한 번에 처리하도록 만들어진 적이 없다.

이게 왜 문제냐면 — rasterize/loss_compute 비용의 85~95%가 픽셀·gaussian
처리량이 아니라 **커널 launch/디스패치 고정비**(Phase 0에서 확인)인데,
이 고정비는 **카메라를 하나 처리할 때마다 매번 새로 지불**된다(같은
iteration 안에서도 배치로 묶이지 않고 순수 순차 for-loop, 카메라 사이에
공유되는 게 전혀 없음). 그래서 카메라를 하나 더 넣으면 그 카메라의
데이터量과 무관하게 "고정비 한 세트"가 통째로 추가된다 — `iters`가 이
파이프라인을 몇 번 반복하는지를 결정하듯, `n_view`는 "한 iteration 안에서
이 파이프라인을 몇 번 반복하는지"를 결정하는 것이라 **사실상 iters와
동일한 메커니즘(고정비 반복)이 곱으로 두 번 걸리는 구조**.

**함의(다음 후보, 고위험·미착수)**: 만약 rasterizer가 여러 카메라를 **한
번의 커널 launch로 묶어 처리**(batch dimension)할 수 있다면, 뷰-연산당
고정비를 `n_view`번이 아니라 **1번만** 지불하게 돼 이론상 뷰당 고정비의
(n_view−1)/n_view ≈ 91%(n_view=11 기준)를 아낄 여지가 있다 — Phase 0에서
확인한 "고정비가 압도적"이라는 사실 자체가 이 lever의 잠재력을 크게 만듦.
다만 이건 `thirdparty/diff-gaussian-rasterization`의 **CUDA 소스 자체를
멀티카메라 batch 지원하도록 수정**해야 하는 일이라, Phase 3에서 겪은
stream-분리 크래시(같은 서드파티 CUDA 코드의 미검증 영역을 건드려 실제로
크래시 남)와 같은 성격의 리스크 — 신중한 별도 라운드가 필요.

## Phase 6 — iters↓·n_view↑ 재배분(같은 view-op 예산, 품질 축) (2026-07-27, 사용자 제안)

Phase 5 회귀식(`rasterize/loss_compute ∝ iters×n_view`)에서 나온 자연스러운
질문: 같은 `iters×n_view`(view-op 총량) 예산을 유지한 채 **iters를 줄이고
n_view(카메라 수)를 늘리면** — 회귀식대로면 rasterize/loss_compute 시간은
거의 그대로(경제적 규모 없음)이고 `optimizer_step`만 `iters`에 비례하니
살짝 이득이지만, **매 gradient step마다 더 다양한 뷰를 보게 돼 기하 일관성
(품질)이 개선될 수 있다**는 게 가설 — 순수 품질 축, 속도 축 아님.

**구현**: `self.window_size`(config `Training.window_size`)가 로드만 되고
실제로는 한 번도 안 쓰이던 **dead config**였음을 발견(`current_window`
상한이 `10`으로 하드코딩, 우연히 config 기본값 10과 일치) — 실제 로직에
연결(`gs_backend.py`, `len(self.current_window) > self.window_size`)해서
window 크기(≈`n_view`)를 config로 통제 가능하게 만듦. 정규 keyframe
`map()` 호출에 `max_viewpoints=self.window_size + 3`도 추가해 window+global
전체가 잘리지 않고 다 들어가도록 함(기존 기본값 20은 window_size≥18에서
subsampling 발생).

**축**: baseline(window_size=10→n_view≈11-13, iters=7, product≈77-91) 대비
product를 대략 유지하면서 재배분:

| 축 | window_size | iters | 예상 n_view | product |
|---|---:|---:|---:|---:|
| baseline(현재 채택) | 10 | 7 | 11~13 | 77~91 |
| 1 | 15 | 5 | 16~18 | 80~90 |
| 2 | 19 | 4 | 20~22 | 80~88 |
| 3 | 25 | 3 | 26~28 | 78~84 |

측정: 1253 전체, 그 외 exp56 최종 채택 레시피(init_itr_num=600 등) 유지.

| 축 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 |
|---|---:|---:|---:|---:|---:|
| baseline | 47.08s | 0.72배 | 22.73 / 23.21 | 2.07cm | 30회 |
| **1(ws=15,iters=5, 실측 n_view=16)** | 46.17s | 0.71배 | **21.64 / 21.89**(**−1.09/−1.32dB**) | 2.41cm | 30회 |
| **2(ws=19,iters=4, 실측 n_view=20)** | 46.34s | 0.71배 | **19.27 / 19.57**(**−3.46/−3.64dB**) | 2.41cm | 32회 |
| 3(ws=25,iters=3) | **미실행(추세로 기각 확정, 아래 참조)** | | | | |

**가설 기각 — 명확하고 악화 추세**: 시간은 예상대로 거의 안 바뀌었지만
(회귀식 예측대로, product를 맞췄으니 rasterize/loss_compute는 거의 그대로)
**PSNR이 축1(−1.1~1.3dB)→축2(−3.5~3.6dB)로 window를 키울수록 더 나빠짐** —
이 프로젝트 노이즈(±0.24~0.33dB)를 훨씬 벗어나는 명백한 실손실, 그것도
단조 악화 추세. "같은 view-op 예산이면 재배분은 공짜"라는 Phase 5 회귀식의
**시간 예측은 정확히 맞았지만, 품질에 대한 예측(다양한 뷰가 도움될 것)은
정반대로 틀렸다** — 그래서 축3(ws=25, iters=3, 더 극단적 재배분)은 추세가
이미 명확해 실행하지 않고 기각 확정.

**왜 틀렸는가(원인 분석)**: `window_size`를 키우면 "iteration당 보는 뷰
개수"만 늘어나는 게 아니라 **current_window 자체가 훨씬 오래된 keyframe까지
붙잡아두는 방향으로 바뀐다** — incremental SLAM 특성상 지도의 "프론티어"
(가장 최근에 새로 들어온, 아직 수렴 안 된 영역)가 한정된 iteration 예산을
과거 keyframe들과 나눠 써야 하고, 게다가 iters까지 줄였으니(7→5→4) **새로
들어온 gaussian이 densify/수렴할 시간 자체가 줄면서 동시에 그 적은
gradient step조차 오래된 영역과 경쟁**하게 됨 — "총 view-op 예산"은 같아도
"프론티어에 집중되는 유효 gradient 밀도"는 크게 줄어드는 구조. Phase 5
회귀식은 순수 **연산 시간**만 설명하는 모델이라 이런 **최적화 동역학
(optimization dynamics)** 효과는 애초에 잡을 수 없었던 것 — 시간과 품질은
서로 다른 메커니즘으로 움직인다는 걸 확인.

**코드 자산은 유지**: `self.window_size`가 dead config였던 걸 실제 로직에
연결한 수정 자체는 유지(기본값 10 그대로 두면 기존과 완전히 동일하게
동작 확인됨) — 향후 window_size를 진짜 원인 분석 없이 건드리면 안 된다는
확실한 반증 데이터를 남긴 것으로 가치가 있음.

**⚠ CLAUDE.md 로드맵(dense-frame supervision)에 대한 함의**: 이 결과는
"n_view를 단순히 늘리기만 하면 품질이 좋아진다"는 가정에 대한 반증이다 —
dense-frame supervision(keyframe 사이 프레임을 supervision 뷰로 추가)을
나중에 시도할 때, 단지 뷰 개수만 늘리고 iters를 줄이거나 window를 무작정
넓히면 **오히려 프론티어 수렴이 희석돼 역효과가 날 수 있음**을 미리
확인한 셈 — 뷰를 늘리려면 (a) iters는 유지/늘리거나 (b) 프론티어(최근
keyframe)에 gradient가 집중되도록 가중치를 주는 설계가 같이 필요할
가능성이 큼. batch 렌더링으로 "시간" 문제를 풀어도 "품질" 문제는 별도로
설계해야 한다는 경고.

## Phase 7 — window_size는 그대로, global 뷰 개수만 늘리기 (2026-07-27, 사용자 제안)

Phase 6은 `window_size`(프론티어 슬롯 자체)를 키워서 n_view를 늘렸다가
품질이 무너졌다 — **원인으로 지목한 게 "프론티어가 과거 keyframe과
gradient 예산을 나눠 쓰게 됨"**이었으니, 그럼 **프론티어 window는 그대로
두고 global(랜덤 과거 뷰) 개수만 늘리면** 같은 문제 없이 "더 다양한 뷰"
효과만 얻을 수 있지 않겠냐는 사용자 제안. `map()` 내부에 이미 있던
`include_global` 메커니즘(iteration마다 과거 keyframe 중 랜덤 2개를 추가로
보는 것)의 하드코딩된 `2`를 `Training.n_global_views`로 config화.

**차이점 명시**: 이번엔 Phase 6처럼 iters를 맞춰 "재배분"하는 게 아니라
`window_size=10`·`iters=7` 그대로 두고 global만 순수 추가라, **view-op
총량 자체가 늘어나 시간도 비례해서 늘 것으로 예상**(회귀식 예측: 대략
`iters × 추가global × 3.5ms` 만큼 rasterize+loss_compute+backward 증가) —
품질이 그 시간 비용을 상쇄할 만큼 개선되는지가 핵심 질문.

| 축 | n_global_views | 실측 n_view(대략) | product(iters×n_view) |
|---|---:|---:|---:|
| baseline(현재 채택) | 2 | 13 | 91 |
| 1 | 6 | 17 | 119 |
| 2 | 10 | 21 | 147 |

측정: 1253 전체, 나머지 exp56 최종 채택 레시피(iters=7, init_itr_num=600,
window_size=10) 유지.

| 축 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 |
|---|---:|---:|---:|---:|---:|
| baseline | 47.08s | 0.72배 | 22.73 / 23.21 | 2.07cm | 30회 |
| **1(n_global=6, 채택)** | 47.20s | 0.73배 | **22.97 / 23.43**(**+0.24/+0.22dB**) | 1.95cm | 26회 |
| 2(n_global=10) | 47.51s | 0.73배 | 23.03 / 23.38(+0.30/+0.17dB, 1과 동급) | 2.42cm | 24회 |

**Phase 6과 정반대 결과 — 이번엔 가설이 맞았다**: 시간은 거의 그대로
(+0.25%/+0.9%, 회귀식이 예측한 소폭 증가와 방향은 맞지만 절대 크기는
작음), **PSNR이 두 지점 모두 개선**(+0.17~0.30dB) — 노이즈(±0.24~0.33dB)
경계선이지만 두 지점이 같은 방향으로 일관되게 나온 게 우연치곤 신뢰할
만함. map() 성사 횟수는 30→26→24로 줄었는데도(뷰가 늘어 호출당 시간이
길어져 큐가 더 밀림) PSNR은 오히려 좋아짐 — **"몇 번 처리하는가"보다
"한 번 처리할 때 얼마나 다양한 뷰를 보는가"가 이 지점에선 더 중요하다는
뜻**. n_global=6과 10은 PSNR이 사실상 동급(수확체감)인데 10은 시간·
coverage·궤적이 전부 살짝 더 나빠 — **`n_global_views=6` 채택**.

**Phase 6과 왜 다른가**: Phase 6은 `window_size`(프론티어 슬롯 자체)를
키워 프론티어가 과거 keyframe과 매 iteration 그 좁은 예산을 경쟁적으로
나눠 써야 했다. Phase 7은 프론티어 window(11개)는 **그대로 온전히 보존**한
채 "덤으로" 과거 keyframe을 더 많이 곁눈질하게만 한 것 — 프론티어 수렴을
방해하지 않으면서 전역 일관성 신호만 추가된 구조라 정반대 결과가 나온 것으로
해석. 정확히 사용자가 제안한 "window_size는 그대로 두고 n_view만 늘리기"가
맞아떨어진 사례.

**exp53+54+55+56 누적 최종(갱신)**: 47.20s, 실시간 배수 0.73배, PSNR
mean/kf **22.97/23.43**(exp55 baseline 대비 mean +0.36dB, kf +0.48dB).

## Phase 8 — rasterizer batch화 조사 → 진짜 CUDA 커널 비용임을 프로파일로 확인, 대신 안전한 부수 발견을 먼저 적용 (2026-07-27, 사용자 요청)

사용자가 "batch 구현 ㄱㄱ"를 요청 — 실제 착수 전에 `torch.profiler`로 `render()`
단일 호출을 격리해 CPU(Python/autograd 디스패치)와 CUDA(커널 실행) 시간을
직접 분리해봄(합성 gaussian으로 마이크로벤치, 절대 수치는 비현실적이지만
**구조**는 유효):

**확인**: `_RasterizeGaussians`/`_RasterizeGaussiansBackward`(Python autograd
wrapper) 자체의 CPU 오버헤드는 호출당 0.1~0.14ms로 작음 — 즉 뷰-연산당
고정비의 정체는 Python 디스패치가 아니라 **진짜 CUDA 커널 실행/launch**
(forward의 preprocess/duplicate/sort/render, backward의 대응 커널). 이는
"Python 루프를 C++ 루프로만 바꿔도 상당 부분 해결될 것"이라는 낙관적
가설을 기각 — **진짜 이득을 보려면 forward.cu/backward.cu/
rasterizer_impl.cu(~2800줄)의 타일 정렬·블렌딩 커널 자체에 카메라 batch
차원을 넣어야 함**. 이건 그래디언트가 조용히 틀려질 수 있는 위험도가
Phase 3(stream 분리, 크래시로 바로 티가 남)보다 한 단계 높은 작업(수치가
미묘하게 틀린 채 계속 학습되는 실패 모드) — 이번 세션에서 안전하게
검증까지 마치기엔 스코프가 크다고 판단해 **보류**.

**부수 발견(안전, 즉시 적용)**: 프로파일링 중 `render()` 1회 호출마다
`Camera.world_view_transform`/`full_proj_transform`/`camera_center`가
property로 정의돼 **매번 `torch.linalg.inv()`를 포함해 처음부터 다시
계산**되고 있음을 발견 — 같은 `map()` iteration 안에서 카메라 pose(R/T)는
안 바뀌는데도 뷰마다(그리고 `full_proj_transform`/`camera_center`가
내부적으로 `world_view_transform`을 또 부르므로 사실상 호출당 최대 3중으로)
재계산되고 있었음. 코드 전체를 grep해 R/T가 바뀌는 지점이 `Camera.
update_RT()` 단 한 곳(+생성자, 캐시가 비어있는 시점)뿐임을 확인한 뒤 —
`vigs/gaussian/utils/camera_utils.py`의 세 property에 **캐싱**을 추가하고
`update_RT()`에서만 무효화. 그래디언트 수학은 전혀 안 건드리는(캐싱된
값도 원래와 동일한 계산 결과) 무위험 변경.

**측정**: 1253 전체, exp56 최종 채택 레시피(iters=7, init_itr_num=600,
window_size=10, n_global_views=6) 위에 캐싱만 추가.

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 |
|---|---:|---:|---:|---:|
| baseline(캐싱 없음) | 47.20s | 0.73배 | 22.97 / 23.43 | 1.95cm |
| **+카메라 행렬 캐싱(채택)** | **45.79s** | **0.70배** | **23.49 / 23.88**(**+0.52/+0.45dB**) | 2.42cm |

**무위험 변경인데 시간·품질·coverage 전부 개선 — 이 세션 최고 ROI 레버**:
시간 −3.0%(47.20→45.79s), **PSNR +0.52/+0.45dB**(노이즈 범위를 확실히
넘는 실개선), **map() 성사 횟수 26→36회(+38%)**. 그래디언트 수학을 전혀
안 건드리고(캐싱된 값 = 원래 계산값과 동일) 순수하게 CPU 측 중복 계산만
없앴을 뿐인데, 그만큼 매 view-op가 빨라져 mapper가 훨씬 덜 밀리면서
(coverage 급증) 품질까지 따라 올라간 것으로 해석 — Phase 1/4/7에서 반복
확인된 "coverage가 늘면 품질도 는다" 패턴이 여기서도 재현. **채택**.

**exp53+54+55+56 누적 최종(갱신)**: 45.79s, 실시간 배수 **0.70배**(exp55
baseline 대비 **−23.4%**), PSNR mean/kf **23.49/23.88**(exp55 baseline
대비 mean **+0.88dB**, kf **+0.93dB**) — 시간을 거의 1/4 줄이면서 PSNR은
거의 1dB 끌어올린 결과.

**batch 렌더링(진짜 CUDA 커널 수정)은 계속 보류**: 이번 발견으로 얻은
이득은 batch화가 목표로 했던 "커널 launch 자체를 줄이는" 것과는 다른
경로(CPU측 중복 계산 제거)라 batch화의 필요성 자체를 없애지는 않음 —
다만 지금 실시간 여유(65.1s 예산 대비 45.8s, 여유 19.3s)가 이미 커져서
batch화의 시급성은 낮아짐. 여전히 고위험(그래디언트 정합성 검증 필요)
작업이라 이번 세션에선 미착수 상태 유지.

## Phase 8b — rasterizer 멀티카메라 batch 실제 구현 (2026-07-27, 사용자 요청: "물어보지 말고 끝까지")

Phase 8에서 "진짜 batch는 CUDA 커널 자체를 고쳐야 하는 고위험 작업"이라
보류했었는데, 사용자가 "묻지 말고 될 때까지 가보라"고 명시적으로 요청 —
실제로 구현·검증·통합까지 완료.

### 설계 — 안전을 위해 커널 자체는 건드리지 않음

`forward.cu`/`backward.cu`는 원본 3DGS 코드가 아니라 VIGS가 이미 크게
확장한 버전(`ray_planes`/`ts`를 이용한 깊이 모호성 해소, eigenvalue 기반
공분산 분해, **SE3 리대수 카메라 pose 그래디언트(`dL_dtau`)까지 손으로
미분한 커널**)이라는 걸 코드를 실제로 읽고 확인 — 이 커널을 직접 고쳐
멀티카메라 batch 차원을 넣는 건 그래디언트가 조용히 틀려질 위험이 매우
커서(Phase 3 stream-크래시보다 한 단계 위험도 높음, 크래시처럼 바로
티가 안 나고 미묘하게 나쁜 채로 계속 학습됨) 채택하지 않음.

대신: **기존의, 이미 검증된 단일-카메라 CUDA 커널(forward/backward)을
그대로, 수정 없이, C++ 쪽에서 카메라 수만큼 루프 돌리는 방식**으로 구현
(`thirdparty/diff-gaussian-rasterization/rasterize_points_batch.{h,cu}`,
신규 파일). 커널 수학은 1바이트도 안 바꿨으니 정확성 리스크가 거의 0 —
얻는 이득은 "Python에서 카메라 수만큼 별도로 `.apply()`를 호출하던 것"을
"C++ 안에서 한 번에 처리"로 바꿔 Python/autograd 디스패치 오버헤드(카메라
행렬 캐싱과 같은 종류의 "고정비") 및 커널 launch 자체를 카메라 수만큼
반복하는 구조는 유지하되 그 사이의 파이썬 왕복을 없애는 것.

가우시안 파라미터(means3D/opacity/scales/rotations/sh)는 카메라 배치
전체가 **공유**하므로, backward에서 카메라별 그래디언트를 C++에서 그냥
`+=`로 합산 — 이건 원래 Python 쪽에서 `loss_mapping = sum(per-view losses);
loss_mapping.backward()`가 하던 것과 수학적으로 동일.

### 실측 코드 리딩으로 잡은 진짜 위험 지점 2개 (구현 전에 발견, 실행 전에 수정)

1. **`dL_dmeans2D`(스크린 공간 그래디언트)를 배치 합산하면 안 됨** —
   `GaussianModel.add_densification_stats()`가 **뷰마다 따로** 호출되며
   그 뷰만의 그래디언트 norm을 누적하는 구조(`xyz_gradient_accum[filter]
   += norm(grad[filter,:2])`, `denom[filter] += 1`)임을 코드에서 확인 —
   합산하면 (a) `norm(합)≠합(norm)`이라 크기 자체가 달라지고 (b) `denom`
   누적 횟수도 달라져 densify 판단 자체가 바뀜. **카메라별로 분리 유지**
   하도록 수정.
2. **`projmatrix_raw`가 실제로는 죽은 파라미터**임을 커널 소스에서 직접
   확인 — `BACKWARD::preprocess`에 전달만 되고 내부에서 한 번도 읽히지
   않음(`grep`으로 전체 파일 확인). 처음엔 아무 값이나 넣어도 안전하다는
   뜻이지만, 나중에 커널이 바뀌면 잠복 버그가 될 수 있어 의미상 올바른
   값(`viewpoint.projection_matrix`, 카메라 intrinsics 행렬)을 정확히
   넣도록 구현.

### 정확성 검증 (실행 전 필수 게이트로 설정, 통과 후에만 통합 진행)

**1단계 — raw CUDA 바인딩 레벨**(`scripts/analysis`에 준하는 검증 스크립트,
합성 gaussian 5개 카메라): forward 색상/깊이/알파 **완전 bit-exact**(diff
0.0), backward 그래디언트(means3D/opacity/scales/rotations/sh/means2D)
전부 float32 잡음 수준(상대오차 ~1e-9)으로 순차 실행과 일치.

**2단계 — Python 통합 레벨**(실제 `Camera`/`GaussianModel` 객체로
`render()` 순차 루프 vs `render_batch()` 비교): forward **완전 일치**
(diff 0.0), backward 그래디언트는 상대오차 ~1e-3~1e-4(활성화 함수·SH
평가 등 연산이 더 길어지며 GPU atomic 연산의 실행순서 비결정성이 살짝
증폭된 것으로 판단, 동일 코드 재실행 시에도 유사한 수준의 편차가 나타남 —
학습에 영향 없는 수준). `viewspace_points.grad`(densification 통계용)도
카메라별로 올바르게 분리됨을 확인.

**과정에서 실제로 잡은 버그 2건**(실행 전 발견, 프로덕션에 영향 없었음):
`colors_precomp` 자리에 실수로 `sh`를 넣었던 것(다른 파라미터 슬롯 혼동),
`viewspace_points`를 하나의 텐서를 슬라이싱해 반환했더니 `.grad`가 채워지지
않는 문제(leaf 텐서가 아니라 select 연산 노드가 돼버림 — 카메라별 독립
leaf 텐서를 만들어 stack하는 방식으로 수정).

### 통합 — `Training.batch_render`(신규, 기본 false) 플래그로 opt-in

`gs_backend.py::map()`의 `for viewpoint in current_viewpoints:` 순차
루프를 `render_batch()` 단일 호출로 대체하는 분기 추가(플래그 꺼져 있으면
기존 코드 100% 그대로, 되돌리기 쉬움). 짧은 시퀀스(200프레임) 스모크
테스트 통과 확인 후 1253 전체 실행:

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 |
|---|---:|---:|---:|---:|
| baseline(batch_render off) | 45.79s | 0.70배 | 23.49 / 23.88 | 2.42cm |
| batch_render=true (1차 실행) | **34.21s(위험 신호)** | 0.53배 | **6.65 / 6.42(붕괴)** | 1.91cm |

**1차 실행에서 PSNR 붕괴 — 격리 검증을 통과했는데도 실전에서 실패한
사례**: 시간은 34.21s로 훨씬 빨라 보였지만 PSNR이 6.65/6.42로 완전히
붕괴 — 명백히 뭔가 잘못됨. `except Exception: pass`가 원인을 숨기고
있었음(디버그 프린트로 열어보니 매 호출이 조용히 실패하고 있었음 —
시간이 빨랐던 건 batch화 덕분이 아니라 **연산 자체가 실패해서 거의
아무 일도 안 하고 있었기 때문**).

**실제 원인 — `depth` 텐서 shape 불일치**: `render()`는 depth를 `(1,H,W)`
로 반환하는데(원본 rasterizer의 `torch::full({1,H,W},...)` 그대로),
`render_batch()`는 배치 차원과 채널 차원을 한 번에 슬라이싱해
`out_depth[b,0]`(shape `(H,W)`)를 반환하고 있었음 — 이 미묘한 shape
차이가 `get_loss_normal()` → `depth_to_normal()` → `.reshape(*depth.
shape[1:], 3)`에서 `depth.shape[1:]`를 잘못 계산해(`(464,)` vs 올바른
`(464,464)`) `RuntimeError`를 던짐, `except`가 그걸 삼켜버려 손실 계산이
거의 아무 것도 안 한 채로 계속 진행됨. **격리된 forward/backward 수치
검증(Phase 8b 본문)은 이 project-specific loss 함수를 애초에 안 건드려서
못 잡아낸 것** — "커널 수학이 맞다"와 "실제 학습 파이프라인과 통합했을 때
맞다"는 다른 질문이라는 걸 재확인. `out_depth[b]`(채널 차원 유지)로 수정,
`transmittance`도 같은 패턴이라 함께 수정.

**2차 실행(수정 후) — 정확성은 확인, 속도 이득은 없음**:

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 |
|---|---:|---:|---:|---:|---:|
| baseline(batch_render off) | 45.79s | 0.70배 | 23.49 / 23.88 | 2.42cm | 36회 |
| batch_render=true(수정 후) | 47.37s | 0.73배 | **23.55 / 24.07**(소폭 개선) | 1.91cm | 38회 |

크래시/붕괴 없음(traceback 0건), PSNR은 오히려 소폭 개선(노이즈 범위
근처)되고 coverage도 늘었지만 — **시간은 개선이 아니라 오히려 소폭 악화**
(45.79→47.37s). 정규 keyframe 호출의 평균 시간을 직접 대조하면 원인이
분명해짐: baseline 761.6ms/call vs batch_render 755.7ms/call — **차이가
1% 미만, 사실상 동일**. Phase 8에서 `torch.profiler`로 미리 확인했던
가설이 실측으로 확정된 것: **뷰당 고정비의 정체는 Python/autograd 디스패치
오버헤드가 아니라 진짜 CUDA 커널 실행/launch 그 자체**였고, 내 구현(기존
단일-카메라 커널을 C++에서 루프 도는 것)은 **커널 launch 횟수 자체를
전혀 줄이지 않았으므로**(여전히 카메라 수만큼 forward/backward 커널이
그대로 실행됨, 단지 그 사이 Python 왕복만 없앤 것) 애초에 큰 이득을 낼
구조가 아니었음 — Python 오버헤드가 원래 작았으니 그걸 없애봐야 남는 게
거의 없었던 것.

**결론 — 구현은 정확하지만(버그 수정 후 검증됨) 채택 안 함**:
`batch_render` 기본값 `false`로 원복(코드는 남겨둠, 향후 재검증 가능한
자산). **진짜 속도 이득을 보려면 결국 처음에 고위험으로 분류해 보류했던
그 작업 — forward.cu/backward.cu 커널 자체에 배치 차원을 넣어 커널 launch
횟수 자체를 줄이는 것 — 이 유일한 길임이 이번 실측으로 재확인됨.**

## Phase 9 — "고정비가 지배적" 결론 재검증: 통제된 단일-view-op 마이크로벤치마크 (2026-07-28, exp56 후속분석)

지도교수 미팅 피드백("view 개수보다 iter당 시간을 줄이는 게 중요", "backprop이 어떤
gaussian에 gradient를 줄지 정하면 쉬움", visibility filter 활용 제안) 이후, Phase 0/5가
내린 "고정비(N-무관)가 지배적" 결론이 이 제안과 정면으로 부딪힌다는 걸 짚고(exp57
설계 논의 중 발견) — 직접 **통제된 실험**으로 확인하기로 함(추정으로 넘기지 않는다는
프로젝트 원칙, `feedback_verify_unmeasured` 적용).

### 방법

Phase 0/5는 전부 **실제 학습 중** 로그(카메라 수·해상도·gaussian 수가 keyframe마다
전부 다르게 뒤섞여 있음)에서 회귀로 역산한 것이었음 — 변수가 서로 얽혀있어 "N만 바꿨을
때" 순수 효과를 못 봄. 이번엔 반대로: **카메라(view) 1개 고정**, gaussian 개수 N만
10,000 / 30,000 / 60,000 / 90,770(exp56 최종 체크포인트 실측치)로 바꿔가며 forward+
backward를 반복 측정 — exp56_ax8_camcache의 실제 학습된 gaussian을 무작위 서브샘플링해
재사용(합성 데이터 아님).

### 방법론 사고 — torch.profiler가 이중계산하고 있었음 (중요, 재사용 시 주의)

1차 시도는 `torch.profiler`의 `key_averages()`에서 모든 이벤트의
`device_time_total`을 그냥 합산 → N=90,770에서 "총 8.39ms"가 나왔는데, 이름이 붙은
실제 CUDA 커널(`preprocessCUDA`/`renderCUDA`/정렬 등)만 따로 합하면 2.86ms뿐이라
**65%가 미계측**인 것처럼 보였음. 더 파보니 원인 발견: C++ 확장 바인딩 함수
(`_RasterizeGaussians`/`_RasterizeGaussiansBackward`)가 프로파일러 트레이스에서
"self_device_time"으로 **자기 자식 커널의 실행시간을 다시 한번 통째로 떠안고 있었음**
(자식이 kineto 트리에 제대로 안 걸려서 벌어지는 프로파일러 자체의 계측 방식 문제로
추정) — 그래서 이름 붙은 커널들과 그 커널을 감싼 wrapper 둘 다에서 같은 시간이
중복 집계됨. **`torch.cuda.synchronize()` 기준 순수 wall-clock**으로 교차검증한
결과 N=90,770에서 진짜 총합은 **3.43ms**(프로파일러가 말한 8.39ms의 41%) — 이걸
ground truth로 채택.

### 결과 (wall-clock, N=10k/30k/60k/90.77k, 최소제곱 피팅)

| | forward | backward |
|---|---:|---:|
| N=10,000 | 0.509ms | 0.599ms |
| N=30,000 | 0.703ms | 0.996ms |
| N=60,000 | 0.854ms | 1.729ms |
| N=90,770 | 1.067ms | 2.358ms |
| 피팅식 | 0.466ms + 6.65μs·N | 0.366ms + 22.1μs·N |
| R² | 0.988 | 0.999 |
| N=90,770에서 고정비 비중 | **43.6%** | **15.4%** |

### 결론 — "고정비가 지배적" 결론을 부분 정정

**단일 view-op을 놓고 N만 순수하게 바꿔보면, 특히 backward는 N-비례 항이 압도적
(84.6%)이고 forward도 절반 이상(56.4%)이 N-비례** — Phase 0/5가 말한 "고정비가
지배적, N은 부차적"은 **실제 다변량 학습 로그에서 여러 변수가 얽혀 계수가 희석된
결과**였을 가능성이 큼(실측 로그에서 n_gauss가 6~13만으로 좁은 범위에서만 움직였고
동시에 iters/n_view 설정이 실험마다 바뀌어 순수 N-효과가 회귀식에 잘 안 잡혔을 것으로
추정). Phase 0/5의 "N을 줄여도 시간이 안 준다"는 관측 자체는 틀리지 않았지만(exp55
결과: gaussian −35.9%인데 시간 −12.2%뿐 — 아래 참고), 원인은 "N이 원래 시간에
안 미쳐서"가 아니라 **"전체 시간(rasterize+backward+loss_compute+optimizer_step
+기타)에서 N-무관 항목(loss_compute 등)이 섞여 있어 평균적으로 희석됐기 때문"**일
가능성 — 이 통제 실험은 rasterize/backward **자체**만 놓고 보면 N이 꽤 크게
작용함을 보여줌.

**exp57 방향에 대한 함의**: 지도교수가 제안한 "visibility 기반으로 backprop할
gaussian을 선별"하는 방향은 **이 결과로 재확인됨** — 특히 backward가 forward보다
N-slope이 3.3배 가파르므로(22.1 vs 6.65 μs/gaussian), backward에 참여하는 gaussian
수를 줄이는 게 forward만 줄이는 것보다 ROI가 클 것으로 예상. exp57에 "coarse
frustum/거리 기반 pre-filter로 map() 호출에 넘기는 유효 N을 줄이기" 항목을
공식적으로 추가.

**exp55의 "N −35.9%인데 시간 −12.2%"와의 정합성 확인(사용자 재질문, 2026-07-28)**:
이 −12.2%(mapping 전체) / −15.1%(map() 5단계) 수치는 exp55 최종 레시피
(**적응 예산 + carve loss 둘 다 적용**된 상태)로 잰 것 — exp55 문서 자신도 이미
"carve loss가 loss_compute에 계산을 소폭 더했다"고 원인 중 하나로 적어뒀음(구현
당시엔 두 원인 다 "고정비 지배" 프레임 안에서 부차적으로 처리됨). Phase 9 계수로
역산: rasterize+backward가 map() 5단계의 74%(Phase 0)이고 그중 N-비례가 평균
약 70%(forward 56.4%·backward 84.6%를 Phase0 비중 40:34로 가중평균)이므로,
N을 35.9% 줄이면 순수 N-효과만으로 0.74×0.70×0.359 ≈ **18.6%**의 map()-전체
시간 감소가 기대됨 — 여기서 같이 켜진 carve loss의 loss_compute 추가 비용을
빼면 관측된 −15.1%와 **자기일관적으로 맞아떨어짐**(모순 아니었음). 즉 "N을
줄여도 시간이 별로 안 준다"는 게 "N이 원래 시간에 별 영향이 없어서"가 아니라
"N-효과(−18.6%)가 carve의 추가 비용으로 일부 상쇄됐기 때문"이었다는 것 —
Phase 9의 "N이 유의미하다"는 결론과 완전히 정합.

**이게 visibility filtering을 더 강하게 지지하는 이유**: exp55의 N-감축은 **무딘
도구**다 — 보이든 안 보이든 지도 전체에서 균일하게 gaussian을 줄임. 반면
visibility filtering은 Phase 9 후속 ROI 조사가 확인한 "뷰당 평균 74%가 애초에
안 보임"(위 §)이라는 **낭비되는 부분만 정밀 타격**하는 도구 — keep_frac 45.5%
(더 많이 걷어냄)이면서도 "보이는" gaussian은 거의 100% 보존(margin=3.0에서
recall 99.97%)하니, exp55의 균일 감축보다 이론상 더 큰 시간 절감을 **품질
손상 없이** 얻을 여지가 큼.

**한계(정직하게 기록)**: 이 마이크로벤치마크는 카메라 1개를 고정 반복한 것이라 실제
map() 호출의 다양한 시점 조합(여러 카메라가 서로 다른 영역을 보는 경우)과는 다름 —
절대 수치가 아니라 "N이 실제로 유의미하게 영향을 준다"는 정성적 결론에 무게를 둘 것.
스크립트: `scripts/analysis/exp56_phase9_kernel_microbenchmark.py`.

### Phase 9 후속 — frustum pre-filter의 실제 ROI 검증 (구현 전 사전 조사)

Phase 9가 "N이 유의미하다"를 확인했으니, 구현(고위험 커널 수정 없이 host-side 필터링만)
전에 **얼마나 절감 여지가 있는지부터** 정량화. exp56 최종 체크포인트(90,770개)에
실제 keyframe 궤적 29곳에서 `render()`가 이미 공짜로 주는 `visibility_filter`
(`radii>0`)를 ground truth 삼아 측정.

**1) 단일 뷰 기준 가시 비율**: 평균 **25.9%만 visible** — 카메라 하나당 gaussian의
74%가 안 보이는데도 매번 preprocessCUDA/computeCov2D 등 전체 N을 통과함(장면
전역에 걸쳐 계속 누적되는 지도 구조상 당연 — 로컬 window 카메라가 전역 90k 중
자기 근방 일부만 봄).

**2) 저비용 frustum pre-filter 설계·검증**: 커널 안 건드리고 순수 PyTorch로 —
gaussian 중심을 `world_view_transform`(render()가 쓰는 것과 동일)으로 카메라
좌표계에 투영해 z>0 및 FOV cone(여유배율 margin) 안에 있는지만 검사. **margin을
스윕해 recall(진짜 visible을 놓치지 않는 비율) vs keep_frac(필터 통과 비율)
트레이드오프 확인**:

| margin | mean recall | min recall | mean keep_frac |
|---:|---:|---:|---:|
| 1.3 | 96.64% | 91.10% | 38.99% |
| 2.0 | 99.62% | 98.97% | 42.93% |
| **3.0** | **99.97%** | **99.92%** | **45.54%** |
| 4.0 | 100.00% | 99.99% | 46.82% |

`margin=3.0`을 안전 기본값으로 채택(진짜 visible을 놓칠 위험 사실상 0, 그런데도
단일 뷰 기준 N을 절반 가까이 줄임).

**3) ⚠ 중요한 반전 — per-call 공유 필터로는 이 절감이 대부분 사라짐**: 정규 keyframe
`map()` 1회는 뷰 1개가 아니라 **~17개**(window+global)를 봄. 이 17개 뷰의
**합집합(union)**으로 필터를 한 번만 계산해 map() 호출 전체에 공유하면 —
서로 다른 뷰가 서로 다른 영역을 보므로 합집합이 금방 지도 대부분을 덮어버려
**keep_frac이 평균 76.0%까지 뛰어오름**(단일 뷰 45.5%의 절반도 안 되는 절감).
**결론: 필터를 map() 호출 전체에 한 번 공유하면 안 되고, 이미 존재하는
per-viewpoint for-loop 안에서 뷰마다 따로 걸어야** Phase 9가 확인한 진짜 절감
(뷰당 N 절반 가까이)을 실제로 가져올 수 있음 — 다행히 현재 구조가 이미 뷰별
for-loop이라 아키텍처 변경 없이 "each render() 호출 앞에 그 뷰만의 필터링된
텐서 슬라이스를 넘기기"로 구현 가능(leaf tensor 인덱싱은 PyTorch autograd가
표준적으로 지원 — 그래디언트가 인덱싱된 위치로만 정확히 라우팅되고 나머지는
자동으로 0-grad, 별도 sparse-gradient 처리 불필요).

**⚠ 구현 전 확인: 기존 `filter_mask` 인자는 이미 있지만 이 용도로 못 씀** —
`diff_gaussian_rasterization/__init__.py`의 `filter_mask`는 grep으로 확인해보니
`rasterize_points.cu`/`cuda_rasterizer/*`(실제 CUDA 소스) 어디에도 안 쓰이고,
Python 쪽 `backward()`에서 **커널이 이미 전체 N을 다 계산한 뒤에** `grad[~filter_mask]
= 0.0`으로 사후적으로 그래디언트만 지우는 장치임(`__init__.py:151-157`) — **연산 자체를
스킵하지 않아 시간 절감이 전혀 없음**. 진짜 절감을 얻으려면 `render()` 호출 **이전에
입력 텐서 자체를 슬라이싱**해야 함.

**정확한 구현 계획(다음 실행 단계, 코드 미변경 상태로 계획만 기록)**:
1. `gaussian/renderer/__init__.py`에 `render_filtered(viewpoint_camera, pc, bg_color,
   keep_mask)` 신규 함수 — `pc.get_xyz[keep_mask]`/`get_opacity[keep_mask]`/
   `get_scaling[keep_mask]`/`get_rotation[keep_mask]`/`get_features[keep_mask]`로
   부분집합을 만든 뒤 기존 `render()`와 동일한 로직으로 호출(기존 `render()` 자체는
   수정 안 함 — 새 함수가 감싸는 형태).
2. **`viewspace_point_tensor`는 반드시 full-N zero tensor로 유지**하고 KEPT 행에만
   실제 그래디언트가 채워지게(EXCLUDED 행은 자동으로 0-grad, 이게 "원래 안 보였다"는
   것과 의미상 동일) — `add_densification_stats(viewspace_point_tensor, update_filter)`가
   `self.xyz_gradient_accum[update_filter]`와 `viewspace_point_tensor.grad[update_filter]`를
   **같은 인덱스 공간(전체 N)**으로 가정하고 접근함(`gaussian_model.py:813-817`, 확인
   완료) — 여기서 인덱스가 어긋나면 Phase 8b급 조용한 버그가 남.
3. `radii`/`visibility_filter`(길이=kept 수)도 `torch.zeros(N)`에 `keep_mask`로
   scatter-back해서 `max_radii2D[visibility_filter_acm[idx]]` 갱신 로직과 호환되게.
4. margin=3.0을 기본값으로, `gs_backend.py::map()`의 기존 per-viewpoint for-loop
   안에서 뷰마다(공유 union 아님, Phase 9 후속에서 확인한 대로) 개별 호출.
5. 검증 순서(Phase 8b와 동일 수준 요구): ① 필터 없음 vs `keep_mask=all_true`로
   호출한 필터 있음 버전이 forward/backward 수치 일치하는지(경로 자체의 정확성) →
   ② 짧은 라이브 구간(length=300)에서 크래시/PSNR 붕괴 없는지 → ③ 1253 전체
   시간·PSNR 실측.

스크립트(ROI 사전조사): `scripts/analysis/exp56_phase9b_frustum_filter_roi.py`.

## Phase 10 — `render_filtered()` 구현·검증 (2026-07-28)

위 계획대로 구현. `gaussian/renderer/__init__.py`에 `frustum_prefilter()`(margin=3.0
기본값)와 `render_filtered()` 신규 함수 추가(기존 `render()`는 1바이트도 안 건드림),
`gs_backend.py::map()`의 정규 keyframe per-viewpoint for-loop 안에 `Training.
frustum_prefilter`(opt-in, 기본 false) 플래그로 배선 — 뷰마다 개별적으로 필터링
(Phase 9 후속에서 확인한 대로 공유 union 아님).

### 검증 ① — 수치 정확성(Phase 8b와 동일 기준)

**첫 시도(실패, 원인 규명)**: `keep_mask=all_true`로 `render_filtered()`와
`render()`를 비교했더니 forward는 bit-exact인데 xyz/scaling/rotation의 backward
gradient가 최대 50~87% 상대오차로 크게 어긋남 — 처음엔 버그로 의심. **원인 규명**:
테스트 loss로 `render.sum()+depth.sum()`(1024×1024 전체 픽셀을 그대로 합산)을 썼더니
그래디언트 절대값이 수십만~수백만 단위로 폭발 → 이 스케일에서는 **`render()` 자신도
반복 호출 간 재현이 안 됨**(같은 입력으로 `render()`를 두 번 부른 것끼리 비교해도
최대 diff 2.5e6, 918개 gaussian이 어긋남 — `render_filtered()`와 무관하게 원본 커널의
GPU atomic 비결정성이 원인, 이 스케일에서 증폭돼 드러난 것). **realistic loss**(L1 vs
고정 랜덤 GT + depth 항, `gs_backend.py`가 실제 쓰는 것과 같은 스케일)로 다시 재면:

| 비교 | grad 상대오차(max) |
|---|---:|
| `render()` vs 자기 자신(반복 호출) | ~1e-7(atomic 비결정성 기준선) |
| `render_filtered(all_true)` vs `render()` | xyz 7.7e-6, opacity 1.8e-7, scaling 6.4e-6, rotation 9.0e-6, features_dc 2.3e-7 |
| `render_filtered(partial frustum)` vs `render()`, (진짜 visible ∩ kept)만 비교 | xyz 8.6e-7, opacity 8.8e-8, scaling 1.2e-6, rotation 5.8e-6 |

**전부 `render()` 자체의 반복-호출 노이즈 수준(~1e-7)과 같은 자릿수** — Phase 8b가
채택 기준으로 삼았던 "float32 노이즈 수준 일치"를 만족. `render_filtered()` 검증 통과.
스크립트: `scripts/analysis/exp56_phase10_render_filtered_check.py`.

### 검증 ② — 짧은 라이브 구간(length=300)

`--pure_online --length 300`, `Training.frustum_prefilter: true`(margin=3.0)로
1253 앞 300프레임 실행 — **크래시 없음**, gaussian 개수가 keyframe마다 정상적으로
누적됨(0→24,995까지 정상 증가, 0에서 멈추거나 폭주하는 이상 없음).

### 검증 ③ — 1253 전체 시간·PSNR 실측 (완료, 결론: 기각)

`Training.frustum_prefilter: true`(margin=3.0), 그 외 exp56 최종 채택 레시피
그대로 1253 전체 실행(`VIGS_TIMING_LOG` 켜서 재실행, exp56_ax8_camcache와
동일 `vigs_track_total` 지표로 비교):

| | baseline(exp56_ax8_camcache) | frustum_prefilter(Phase 10) | 변화 |
|---|---:|---:|---:|
| 온라인 루프 총합(`vigs_track_total`) | 45.79s | 45.38s | **−0.89%**(사실상 잡음 수준) |
| PSNR mean/kf | 23.49 / 23.88 | 23.14 / 23.59 | **−0.35 / −0.29dB** |
| map() 성사 횟수 | 36회 | 30회 | **−17%** |

**map_call 로그로 원인 진단 — rasterize가 오히려 2배 느려짐**:

| | baseline avg/call | frustum avg/call |
|---|---:|---:|
| rasterize | 139.4ms | **290.5ms**(+108%) |
| backward | 348.9ms | 439.4ms(+26%) |
| loss_compute | 434.9ms | 420.0ms(−3%, 거의 무변화, 예상대로 N-무관) |

**원인 확정**: `keep_mask = frustum_prefilter(...)` 호출을 `with _Sect(_acc,
"rasterize")` 블록 **안에** 넣었기 때문에(뷰마다, 즉 map() 1회당 최대 17번) 이
필터링 자체의 비용(`(N,4)@(4,4)` 행렬곱 + 5개의 별도 인덱싱 연산 —
`get_xyz[idx]`/`get_scaling[idx]`/`get_opacity[idx]`/`get_rotation[idx]`/
`get_features[idx]`, 각각 자체 커널 launch)이 "rasterize" 시간에 그대로
잡힘. **이 필터링 자체가 만들어내는 추가 launch 비용이, 필터링으로 줄어든
gaussian 수만큼 rasterizer 커널이 아낀 시간보다 컸다** — 결과적으로 순
효과가 마이너스에 가까움. map() 1회가 더 느려지니 mapper가 밀려 큐 드롭이
늘어 성사 횟수가 36→30으로 줄고(Phase1/4/7/8에서 반복 확인된 "느려지면
coverage↓→PSNR↓" 패턴 그대로 재현), PSNR도 같이 하락.

**결론 — 기각, `frustum_prefilter` 기본값 `false` 유지**(코드는 향후 자산으로
보존, `batch_render`와 같은 패턴). **이게 Phase 9의 결론을 뒤집는 게 아니라
오히려 더 강하게 재확인하는 결과다**: Phase 9는 "N-비례 항이 유의미하다"였지,
"host-side에서 N을 줄이면 공짜로 이득이 난다"가 아니었음 — N을 줄이는 행위
자체가 Python/PyTorch 레벨에서는 반드시 추가 커널 launch를 동반하고, Phase 9가
이미 확인한 대로 launch 자체의 비용이 크기 때문에 "덜 계산하되 launch를 더
하는" 방식은 구조적으로 손해를 보기 쉽다. **진짜 이득을 보려면 필터링을
Python/host 레벨이 아니라 CUDA 커널 내부(preprocessCUDA에 조건 분기를 넣어
애초에 launch를 늘리지 않고 안에서 skip)에 융합해야 한다** — 이건 처음부터
고위험으로 분류해 미뤄왔던 forward.cu/backward.cu 직접 수정과 결국 같은
결론으로 수렴함(Phase 8/8b/다음 단계 0번과 동일).

## 다음 단계

0. **rasterizer 멀티카메라 batch 지원(고위험, 여전히 보류)** — Phase 8에서
   프로파일로 확인한 대로 진짜 CUDA 커널 비용이라 batch화의 잠재력 자체는
   여전히 유효(`n_view`가 뷰-연산당 고정비를 그대로 곱으로 반복). 다만
   Phase 8의 카메라 캐싱으로 실시간 여유가 커져서(19.3s 여유) 시급성은
   낮아짐 — `thirdparty/diff-gaussian-rasterization`의 forward.cu/
   backward.cu 커널 자체를 수정해야 하는 별도의 신중한 라운드로 남겨둠
   (forward부터 pixel-exact 검증 → backward는 gradient 대조 검증 필요).
1. **Phase 4의 "왜 2~3회인가" 미해결 질문 규명** — `remove_all_gaussians()`는
   코드상 정확히 한 번만 조건이 참이 되는데 실측 로그엔 초기화급 호출이 그보다
   많이 잡힘. 정확한 메커니즘을 알면 PGBA 호출(`iters=20`, 4회, 3.96~3.93s)도
   같은 방식으로 더 줄일 여지가 있는지 판단 가능 — 우선순위 상위 후보.
2. `init_itr_num`을 600 밑으로(예: 450) 더 세밀하게 스캔 — 300(기각)과
   600(채택) 사이에 더 나은 지점이 있을 수 있음, 지금은 두 지점만 확인.
3. iters를 7 밑으로(예: 3~4) 더 내리는 것도 미탐색 — Phase 1에서 5→7 사이
   수확체감이 이미 보였으므로 ROI는 낮을 가능성이 크지만, 완전히 배제하진
   않음.
4. carve floater 지표(exp55의 `exp55_score_carve_vigs.py`)로 iters=7+
   init_itr_num=600 채택 레시피의 floater 수준도 재확인할 가치 — carve_lambda는
   그대로 0.05를 유지했지만 iters가 줄어 carve loss 자체의 gradient step 수도
   줄었으므로 효과가 희석됐을 가능성.
5. (낮은 우선순위, 고위험) `thirdparty/diff-gaussian-rasterization`을
   멀티스트림 안전하게 패치하면 축3(stream 분리)을 다시 시도할 여지 — CUDA
   커널 소스 레벨 작업이라 투자 대비 효과가 불확실, 지금 우선순위는 아님.
