# 렌더링당 학습 시간: 1/2/4장 묶음

2026-09-25. 사용자 요청: 우리 추가 매핑을 여러 영상씩 묶어 Adam update하면 렌더링당 평균 시간이 줄어드는가?

## 사전 정의

- 현재 causal40 paired 경로를 그대로 replay하여 Aria1253/RPNG table_06/UTMM square-1 endpoint를 재구성한다. 생산 코드는 수정하지 않는다.
- 이후 폐기할 Gaussian clone에서만 offline timing diagnostic을 수행한다. 이 추가 학습은 strict online 결과가 아니며 결과 지도를 배포/평가하지 않는다.
- 같은 시작 Gaussian 파라미터와 기존 Adam moments를 매 trial 복원. 같은 96개 KF/dense 교대 ERVS 선택 순서. 1/2/4장씩 loss를 합산하고 backward/Adam/synchronize를 한 번 수행한다.
- 3개 조건 워밍업 후 6개 순열 순서로 반복 측정. 렌더링당 동기화 wall time의 중앙값과 범위, 별도 CUDA event 단계별 시간과 추가 peak VRAM을 기록한다.
- KF RGBD+normal과 dense RGB loss 유지. 묶음 loss는 vanilla처럼 sum. LR은 render 순서 기준, 각 묶음 첫 render의 값. 그룹 변경은 최적화 궤적을 바꾸므로 품질 동등성을 주장하지 않는다.
- RGB/깊이/pose는 GPU에 준비한 상태다. 트래킹·pose 준비·전송·선택·topology·실행 guard/audit는 제외한다. 따라서 순수 학습 경로의 grouping 비용 비교이며 live 전체 시스템 속도 측정이 아니다.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/benchmark_grouped_render_time.py`

Results: `results/campaigns/gain_attribution/grouped_render_timing/`

## 결과

측정 전.

2026-09-25 v1: causal Aria replay 완료 뒤 offline timing camera 준비가 닫힌 worker의 thread guard에 거부되어 측정 실패. 유효 timing 결과 없음. v2에서 diagnostic의 deferred camera preparation guard만 분리하며 production/EOS guard는 수정하지 않음.

**2026-09-25 grouped render timing v2 완료:** 3scene, 같은 초기지도/Adam/영상96개, 1/2/4장 묶음 각6회 warm 측정. ms/render Aria3.407→2.940→2.770, RPNG6.615→6.125→5.950, UTMM2.457→2.077→1.916. 2장7.4–15.4%,4장10.0–22.0% 단축. 준비/전송/선택/guard 제외한 compute 진단이며 live/품질 유지 미검증. 생산 변경 없음. source unchanged 및 replay3run audit PASS.

[측정표와 범위](SUMMARY.md) · [전체 구현 구조](../render_budget40_feasibility/IMPLEMENTATION.md)
