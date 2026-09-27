# 묶음별 렌더링당 학습 시간 측정 결과

2026-09-25 · RTX 5090 · 현재 paired mapper endpoint · warm compute microbenchmark

**세 장면 모두 여러 영상을 묶으면 렌더링당 평균 학습 시간이 줄었다.** 2장 묶음은 7.4–15.4%, 4장 묶음은 10.0–22.0% 단축했다. 이는 실행 처리량 측정이며, 수렴 속도·held-out 품질 유지·실시간 성공을 검증한 결과는 아니다.

|장면|Gaussian 수|영상 H×W|1장 ms/render|2장 ms/render|2장 단축|4장 ms/render|4장 단축|
|---|---:|---:|---:|---:|---:|---:|---:|
|aria|131,523|464×464|3.407|2.940|13.7%|2.770|18.7%|
|rpng|273,610|344×616|6.615|6.125|7.4%|5.950|10.0%|
|utmm|77,142|328×648|2.457|2.077|15.4%|1.916|22.0%|

조건별 96 renders, 6회 반복, 실행 순서는 (1,2,4)의 모든 순열. 동일한 96개 KF/dense 교대 선택, 같은 초기 지도 및 기존 Adam state를 매 trial 복원했다. 각각 96/48/24번 optimizer step을 수행했다. 모든 trial은 동일 Gaussian 수를 유지했고 parameter finite 검사를 통과했다.

재구성 endpoint의 Gaussian 수는 원래 품질 평가 run과 약간 다를 수 있다(CUDA 학습 재실행). 이 실험의 1/2/4장 조건들은 해당 재구성 지도를 정확히 공유한다. 새로운 endpoint를 품질 개선 결과로 사용하지 않는다.

## 측정 범위

- 포함: 단일 camera renderer 반복, KF RGBD+normal/dense RGB loss, sum-loss backward, Adam, zero_grad, 묶음마다 GPU synchronize, 묶음 시작의 learning-rate 설정.
- 제외: RGB/IMU 입력, tracking, ERVS 후보 선정, dense pose 준비, H2D 전송, topology 생성/제거, worker queue, 실행 guard/audit. 이미지와 pose를 GPU에 준비한 뒤 측정했다.
- batch GPU rasterizer로 바꾼 실험이 아니다. 같은 단일 camera renderer를 쓰고 gradient/optimizer step 묶음만 바꿨다.
- loss는 vanilla와 같은 sum. 묶음 크기별 gradient/Adam 경로는 달라지므로 품질 동등성은 미검증이다.
- offline timing clone은 폐기. 실제 생산 trainer는 여전히 한 장씩 학습한다.

## 반복 변동과 한 묶음의 시간

|장면|묶음|ms/render 중앙값 [최소,최대]|한 묶음 평균 ms (중앙값 환산)|추가 peak allocated MiB (반복 중앙값)|
|---|---:|---:|---:|---:|
|aria|1|3.407 [3.361, 3.618]|3.407|86.5|
|aria|2|2.940 [2.902, 3.037]|5.879|143.5|
|aria|4|2.770 [2.726, 2.823]|11.080|259.1|
|rpng|1|6.615 [6.558, 6.814]|6.615|137.7|
|rpng|2|6.125 [6.096, 6.160]|12.250|240.8|
|rpng|4|5.950 [5.940, 5.989]|23.800|441.7|
|utmm|1|2.457 [2.429, 2.586]|2.457|71.7|
|utmm|2|2.077 [2.052, 2.106]|4.154|115.1|
|utmm|4|1.916 [1.889, 1.929]|7.666|205.9|

추가 peak은 해당 trial 시작 시점의 allocated memory를 뺀 값이며, 전체 시스템 VRAM이 아니다. 묶음이 커지면 여러 영상의 autograd graph를 동시에 유지하므로 증가한다.

## 별도 CUDA event 구간 계측

아래는 각 조건 32 renders의 별도 계측이다. 이벤트 기록 오버헤드가 있어 위 wall-time 표와 직접 합산/일치시키지 않는다. CUDA event 구간은 kernel 실행뿐 아니라 해당 stream에서 host enqueue를 기다리는 간격도 포함할 수 있으므로 순수 kernel-time 분해로 단정하지 않는다.

|장면|묶음|render ms/render|loss|backward|Adam+zero_grad|
|---|---:|---:|---:|---:|---:|
|aria|1|0.568|0.414|2.147|0.534|
|aria|2|0.548|0.417|2.010|0.273|
|aria|4|0.508|0.402|2.042|0.135|
|rpng|1|0.936|0.406|4.337|0.583|
|rpng|2|0.989|0.494|4.283|0.293|
|rpng|4|0.890|0.404|4.241|0.146|
|utmm|1|0.426|0.414|1.340|0.484|
|utmm|2|0.396|0.420|1.069|0.271|
|utmm|4|0.364|0.401|1.052|0.134|

Adam+zero_grad 비용의 render당 감소가 확인됐다. 렌더링 및 역전파 자체는 이미지마다 필요하므로 2장 묶음이 2배 속도를 뜻하지 않는다.

한 묶음의 총 시간은 늘어난다. 따라서 현재 next-arrival slack gate에서 평균 처리량이 좋아져도 admission 기회가 증가한다고 단정할 수 없다. 실제 live에 도입하려면 묶음 시간 예측·예산·count commit·EOS 처리를 함께 검증해야 한다.

## 검증 및 파일

- 3개 scene replay execution audit PASS; 원본 소스 해시 변화 0. GPU 측정은 순차 실행.
- v1은 closed worker thread guard가 diagnostic camera 준비를 막아 실패. v2는 측정용 deferred preparation guard만 분리한 뒤 disposable clone으로 측정. 생산 EOS 정책은 변경하지 않음.
- 원시 결과: `results/campaigns/gain_attribution/grouped_render_timing/v2/summary.json` 및 scene별 `timing.json`.
- 실행기: `benchmarks/online_gs/campaigns/gain_attribution/benchmark_grouped_render_time.py`.
- [이득을 보인 구현 상세](../render_budget40_feasibility/IMPLEMENTATION.md).
