# Paired ERVS의 누적 선택 횟수 복원

2026-09-25 사용자 지시: 최근 선택 횟수 대신 누적 선택 횟수를 사용한다.

## 경위

`online_dense_training` v16에서 오래된 영상의 재방문 부족을 완화하려고 최근 N회 선택 count를 실험했다. 해당 기록은 평균 +0.07596 dB였지만 품질 채택 실패를 명시한다. 이 옵션이 이후 paired full-pool과 40 renders/KF 비교의 기본값으로 이어졌다. 누적 count를 설명하는 논문과 다른 설정이며, 이를 정당화할 확정 근거는 없다.

## 변경 계약

- `/home/intern/VIGS-SLAM-online-worker-integration`의 paired runtime 기본 scope를 `all_rgb`로 변경한다.
- 각 영상이 실제 optimizer step에 참여한 횟수를 해당 map generation 시작부터 누적한다. KF는 native window 및 추가 KF 학습을 모두 포함한다. dense는 추가 RGB 학습을 포함한다.
- 하나의 native optimizer step이 여러 영상을 사용하면 각 영상에 +1한다. 예약·pose 준비·실패/취소는 count를 올리지 않는다.
- 추가 KF/dense 1:1 교대, 역할별 full pool, entropy weight, loss, 단일 영상 Adam, Growth 비활성 상태는 그대로 유지한다.
- dense→KF 승격 시 누적 count를 보존한다. 지도 reset 시 새 generation의 count는 0에서 시작하고 이전 기록은 보고서에 남긴다.
- 최근 횟수는 명시적 `recent_photometric` 옵션으로만 재현 가능하게 남긴다. mixed legacy 경로의 기본값은 이 변경 범위 밖이다.
- 고정 예산/arrival runner에 `--selection-count-scope`를 추가한다. 기본값 생략 시 paired는 누적, 기존 측정 재현은 `--selection-count-scope recent_photometric` 사용.
- ledger audit가 실제 완료 native+추가 service를 독립 재집계하도록 수정한다.

기존 40회 PSNR과 grouped timing은 최근 횟수 설정의 결과로 보존한다. 누적 설정으로 이득이 유지되는지는 별도 검증 전이며, 이번 변경으로 기존 숫자를 재해석하지 않는다. 생산 `VIGS-SLAM-paper-full`과 논문 tex는 수정하지 않는다.

## 검증

CPU 회귀 검증 결과를 아래에 추가한다. GPU 품질 실험은 이 변경 확인 범위에 포함하지 않는다.

**2026-09-25 paired 누적 ERVS 복원:** 사용자 지시로 integration paired 기본 count를 recent_photometric→all_rgb로 변경. KF native+추가 및 dense 실제 완료 사용 횟수를 generation별 누적; 승격 시 보존, 취소 미집계, reset 시 새 generation. CLI로 과거recent 명시 재현 가능. 독립 service ledger audit 및 관련 CPU15test/compile PASS. sampling pool·교대·loss·배치수는 유지. 기존40회 PSNR은 recent 설정 결과이며 새 cumulative 품질 미검증.

검증 기록: `results/campaigns/gain_attribution/cumulative_ervs/cpu_v1/validation.json`. 소스 스냅샷은 같은 폴더의 `source_lock.json`/`source/`.

## GPU 검증 사전 정의 — 40회 공통 예산

사용자가 누적 설정의 성능 테스트를 요청했다. Aria1253/RPNG table_06/UTMM square-1에서 `all_rgb` 및 명시적 `recent_photometric` 대조군을 같은 현재 소스로 각각 실행한다(seed0, 총6회). 40 training camera renders/KF, 기존 causal tracker trace/평가 cohort, batch1, loss/topology/pose 경로는 유지한다. 바닐라는 기존 검증된 official40 결과를 사용하되 실제 prefix render 수·pose trajectory·cohort 일치를 재검사한다. 최근 방식도 같은 소스로 다시 실행해 소스 변경과 이전 실행 편차를 구분한다.

매 run 저장 지도 평가2회 일치 및 독립 render/count ledger audit를 요구한다. 성능 저하도 장면별 그대로 기록하며 sampler·예산·threshold를 결과에 맞춰 튜닝하지 않는다. 이 실험은 fixed-work 품질 비교이며 동시 tracking/live 성능 검증이 아니다. 묶음 업데이트도 적용하지 않는다.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_cumulative_ervs_panel.py`

Results: `results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/`

**2026-09-25 cumulative ERVS40 / aria / all_rgb:** execution=True, audit=True, held-out PSNR=24.604614177732977; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/aria/all_rgb.

**2026-09-25 cumulative ERVS40 / aria / recent_photometric:** execution=True, audit=True, held-out PSNR=24.859723265844448; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/aria/recent_photometric.

**2026-09-25 cumulative ERVS40 / rpng / all_rgb:** execution=True, audit=True, held-out PSNR=24.666318010209917; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/rpng/all_rgb.

**2026-09-25 cumulative ERVS40 / rpng / recent_photometric:** execution=True, audit=True, held-out PSNR=24.827265703355945; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/rpng/recent_photometric.

**2026-09-25 cumulative ERVS40 / utmm / all_rgb:** execution=True, audit=True, held-out PSNR=21.32949548886146; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/utmm/all_rgb.

**2026-09-25 cumulative ERVS40 / utmm / recent_photometric:** execution=True, audit=True, held-out PSNR=21.406847058990856; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/utmm/recent_photometric.

## GPU 검증 완료

**2026-09-25 누적 ERVS40 최종 검증 완료:** 동일40 renders/KF·seed0·batch1에서 누적/최근 방식 총6회 실행 및 독립 count/work audit·저장 지도별 평가2회 모두 PASS. 누적 held-out PSNR Aria/RPNG/UTMM=24.6046/24.6663/21.3295 dB, 공식 vanilla40 대비 +3.8532/+2.2053/+2.5049 dB 유지. 현재 소스 recent 재실행 대비 −0.2551/−0.1609/−0.0774 dB(장면 평균 −0.1645). native window 사용까지 포함하는 all_rgb 누적 기본값 유지; 최근 방식의 우위를 누적 ERVS 오류로 해석하지 않음. 기억 기간과 native count 반영이 함께 바뀐 비교이며 causal fixed-work 결과로 actual-live/동시 tracking 성공을 뜻하지 않음. 반복 평가는 학습 seed 반복이 아님.

[장면별 수치·작업량·제약](SUMMARY.md). 누적/최근 간 training renders·native/추가 KF/dense 횟수·Adam steps가 모두 일치했다. 과거 recent 재실행 편차는 +0.0005/−0.0064/−0.0111 dB였으며, 이번 결과에 맞춰 sampler나 예산을 튜닝하지 않았다.
