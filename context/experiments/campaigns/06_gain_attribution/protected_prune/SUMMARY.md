# Pruning-only + 최근 Gaussian 보호 — RPNG40 결과

2026-09-27. 사용자 요청 범위의 **세 조건만** 완료했다. **기존 opacity 0.7은 최근 생성 점을 보호해도 품질 하락이 크다. 0.1은 더 완만한 개수·시간 절감 후보지만 무손실은 아니다.** 기본 preset은 변경하지 않았다.

| 조건 | 최종 Gaussian | 감소율 | held-out PSNR | ΔPSNR | mapper 시간 | 시간 감소 |
|---|---:|---:|---:|---:|---:|---:|
| Pruning OFF | 357,071 | 0.0% | 25.2237 | +0.0000 | 108.12s | 0.0% |
| opacity < 0.7 | 68,439 | 80.8% | 24.5337 | -0.6900 | 92.76s | 14.2% |
| opacity < 0.1 | 159,616 | 55.3% | 25.0709 | -0.1527 | 99.62s | 7.9% |

## 동일하게 유지한 것과 보호 범위

RPNG table_06 / 40 renders/KF / seed0. 세 조건 모두 9,080 training renders와 9,080 Adam steps. PPM init64/regular256·online-rank2.5/span2, κ16·τ₀4·누적 ERVS·3:3:6·영상별 Adam·dense RGB·scale projection 유지. Densify/clone/split/크기 기반 prune/KF cap/Carve/blur는 OFF.

최근 10번의 **비어 있지 않은 KF birth batch**에 속한 점을 모두 보호했다. 초 단위 나이가 아니라 생성 순서 기준이며, 한 packet에서 여러 KF를 재생성하는 경우도 각각 한 birth batch로 센다. 지도 reset 시 보호 이력을 초기화한다. Opacity 조건은 그보다 오래된 점에만 적용한다. 이를 충분한 관측 횟수 또는 학습 완료 판정과 동일시하지 않는다.

기존 주기 값150을 완료된 training render 수에 적용하고 packet 경계에서 검사했다. 두 pruning 조건의 검사 시점은 동일한52회다. 기존 grouped-Adam150 iterations와 같은 빈도라는 뜻은 아니다. 마지막 입력 이후 별도 cleanup은 없다.

## 검증

- 최근 보호점 삭제 **0개**, 각 pruning 후 남은 stable ID·Adam moment·parameter 정렬 검사 통과.
- 세 조건의 학습 영상 UID/선택 순서·admission·loss/LR schedule·birth 수·렌더링/Adam 총수 및 prefix·causal 입력·평가 cohort 일치.
- Densify/stats/비인가 prune는 guard로 차단했고 금지 호출0회. Helper 및 worker 소스는 0.7과0.1에서 동일하다.
- 최종 지도에서 제거된 점은 0.7:288,632개, 0.1:197,455개. 모든 지도 세대의 제거량은 각각303,562/200,104개다. 이 두 수치는 지도 재초기화 때문에 다르다.
- CPU41개 테스트와 GPU3개 실행/독립 감사 통과. 저장 지도별 평가2회 일치. 학습3seed 반복 검증이 아니다.

## 해석

0.7은 점을80.8% 줄였지만 PSNR이0.690dB 하락했다. 0.1은 점을55.3% 줄이면서 하락을0.153dB로 줄였다. 시간 감소는 각각14.2%,7.9%였다. 따라서 지금 결과로는 기존0.7 pruning을 그대로 복원하기보다 낮은 기준의 pruning-only를 검토하는 편이 낫다. 다만 한 장면의 단일 실행이므로 공통 기본값으로 채택하지 않았다. Opacity pruning은 floater 여부를 직접 판정하지 않으며 geometry 개선을 주장하지 않는다.

## 집계 오류와 정정

첫0.7 실행은 학습·평가·보호점 검사를 마쳤으나, 전체 birth에서 prune_points 호출로 삭제된 점만 빼는 사후 개수 검사에서 실패했다. IMU reset은 GaussianModel 전체를 교체하므로 이 식에 잡히지 않는 점들이 있었다. 원본 실패 기록을 보존하고 마지막 reset(arrival391) 이후 birth 합과 pruning 합으로 정정했다:357,071−288,632=68,439. 학습 코드는 바꾸지 않았고 OFF/0.7을 재실행하지 않았다. 수정한 것은 runner의 개수 집계와 남은0.1 단독 실행 선택뿐이다.

## 산출물

- OFF/0.7 원본: `results/campaigns/gain_attribution/protected_prune/rpng40_v1/`
- 0.7 정정 감사: 같은 경로의 `opacity07_corrected_result.json`, `opacity07/independent_audit.json`
- 0.1 원본: `results/campaigns/gain_attribution/protected_prune/rpng40_low_v2/`
- 종합 JSON: `rpng40_v1/comparison.json`
- 구현: `benchmarks/online_gs/campaigns/gain_attribution/protected_opacity_prune.py`, opt-in `run_kf15_render_worker.py --protected-opacity-prune --prune-opacity-threshold VALUE`
- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_protected_prune_comparison.py`
