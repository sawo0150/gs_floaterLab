# 최근 생성 Gaussian 보호 + opacity-only pruning (2026-09-27)

사용자 요청에 따라 RPNG table_06, 40 renders/KF에서 세 조건만 비교한다: OFF / opacity < 0.7 / opacity < 0.1. 0.7은 기존 regular mapping 기준이며 0.1은 사용자가 요청한 더 낮은 기준의 단일 후보다. 파라미터 sweep이나 다른 장면으로 확장하지 않는다.

- PPM init64/regular256, online-rank2.5/span2, ERVS κ16/τ₀4, 3:3:6, 영상별 Adam, dense RGB, scale projection 유지. Blur/Carve/densify/split/clone OFF.
- **최근 10번의 비어 있지 않은 KF birth batch를 보호**한다. 기존 window 크기10에서 정한 공통 기준으로, 장면별 시점·Gaussian 수 cutoff는 사용하지 않는다. 각 점의 stable point ID와 birth 순서를 기록한다. timestamp를 정수로 바꾼 origin ID의 충돌을 피한다. 지도 reset 시 보호 이력도 초기화한다. Birth batch가 10개 이하면 모든 점을 보호한다.
- 해당 보호 범위 밖에서 opacity가 threshold보다 낮은 점만 제거한다. 크기 필터, KF별 cap, carve/floater prune은 사용하지 않는다. 오래됐다는 이유만으로 삭제하지 않는다.
- 기존 regular 주기150을 **완료된 training render 수** 기준으로 사용하며, packet의 모든 학습을 완료한 경계에서 한 번 검사한다. 다음150배수 이상이 된 packet에서 다시 검사한다. 예전 grouped-Adam의150 iterations와 실행 빈도가 동일하다는 주장은 하지 않는다. 마지막 입력 이후 cleanup은 없다.
- 점 삭제는 기존 prune_points의 optimizer-state 동반 삭제 경로를 사용한다. 매번 보호점 불변, 남은 stable ID 일치, Adam moment/parameter 크기 일치를 검사한다. 모든 densify/stats/비인가 prune는 실행 시 오류로 막는다.
- fresh OFF와 두 pruning 조건만 실행한다. View 선택·admission·loss/LR schedule·입력 pose·birth 개수·render/Adam 총수와 prefix·평가 cohort를 대조한다. Held-out PSNR, 최종GS, mapper 시간, 실제 제거 수를 보고한다. 단일seed·causal tracker replay이며 live/geometry 검증은 아니다.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_protected_prune_comparison.py`.
실험 helper는 opt-in이며 production backend와 기본 preset은 수정하지 않는다.

## 실행 기록

**2026-09-27 protected prune off / RPNG40:** PSNR=25.223685410645633, GS=357071, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_v1/off.

**2026-09-27 protected prune opacity07 / RPNG40:** PSNR=None, GS=None, audit=False, error=Traceback (most recent call last):
  File "/home/intern/gs_floaterLab/benchmarks/online_gs/campaigns/gain_attribution/run_protected_prune_comparison.py", line 113, in main
    assert births - removed - resets == x['gaussians']
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_v1/opacity07.

**2026-09-27 protected prune opacity07 / RPNG40:** PSNR=24.533669085116, GS=68439, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_v1/opacity07.

**2026-09-27 protected prune opacity01 / RPNG40:** PSNR=25.070940272013345, GS=159616, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_low_v2/opacity01.

**2026-09-27 완료:** 3조건 실측·검증 완료. OFF25.2237/357071GS,0.7=24.5337/68439GS,0.1=25.0709/159616GS. 보호점삭제0,동일9080renders/Adam. [종합 결과 및 집계 정정](SUMMARY.md). 기본값 미변경.

## 2026-09-27 — Aria/UTMM에 0.1만 교차 장면 검증

사용자 요청에 따라 opacity0.1·최근10KF birth 보호·40renders/KF를 그대로 Aria1253와 UTMM square-1에 적용한다. 신규 학습은 **두 번만** 수행하며 OFF는 이미 완료된 `init_density/gpu15_40_v1/b40_d1/{aria,utmm}`를 재사용한다. RPNG 및 0.7은 재실행하지 않는다. PPM 초기화 개수·κ·τ·학습 방식 변경 및 추가 튜닝은 없다. 초기화 증가는 이번 검증 이후 논의할 별도 가설로 남긴다. 동일 birth CSV·선택/작업량·입력·평가조건과 최근점 보호를 확인한다. 비교 시간은 서로 다른 실행에서 측정된 단일-run mapper 시간이므로 작은 차이를 일반화하지 않는다.

**2026-09-27 protected prune opacity01 / aria40:** PSNR=25.81622082222509, GS=151604, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/transfer40_v1/aria/opacity01.

**2026-09-27 protected prune opacity01 / utmm40:** PSNR=22.12074293324977, GS=96733, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/transfer40_v1/utmm/opacity01.

**2026-09-27 교차 장면 완료:** 추가2회PASS. Aria0.1=25.8162dB/151604GS(−0.0945dB/−21.3%),UTMM22.1207/96733(−0.1024dB/−31.7%). 보호점삭제0·동일work/birth/selection. [세 장면 비교](TRANSFER40.md). Init증가 실험 및기본값변경 없음.

## 2026-09-28 — Pruning 주기만 150→300으로 변경

사용자 요청에 따라 protected pruning의 기본 검사 간격을 완료된 training render150회에서300회로 늘렸다. `--prune-every-renders`로 worker와비교runner에전달하며 native `gaussian_update_every`와분리했다. 과거150회결과를재현하려면명시적으로 `--prune-every-renders 150`을사용한다. Packet경계에서만검사하고중복검사·밀린검사추가실행은하지않는다.

현재 논의하는 opacity0.1·최근10KF birth보호·PPM init64/regular256은그대로다. Pruning OFF가전체기본preset인점은바꾸지않았으며,수정은opt-in pruning경로의주기에한정한다. 기존마스크테스트5개와300회경계/중복방지/건너뛴경계동작을CPU로확인했다. **새 주기300의품질·시간GPU실험은아직하지않았다.**

추가 사용자 발언의 “init을기존원래수준까지높인다”는전제를정정했다. 완료된0.1pruning세장면실험은이미birth multiplier1.0,init64/regular256인기본생성량이다. 결과의Gaussian감소는초기화축소가아닌학습중pruning때문이다. 별도init증가나바닐라32/64로의변경은하지않았다.

**2026-09-28 protected prune opacity01 / aria40 period=300 birth_denominator=1.0:** PSNR=25.838654343408482, GS=158393, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/aria/base/opacity01.

**2026-09-28 protected prune opacity01 / aria40 period=300 birth_denominator=0.8:** PSNR=25.782753099922004, GS=195316, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/aria/increase/opacity01.

**2026-09-28 protected prune opacity01 / rpng40 period=300 birth_denominator=1.0:** PSNR=25.08195193866352, GS=164895, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/rpng/base/opacity01.

**2026-09-28 protected prune opacity01 / rpng40 period=300 birth_denominator=0.8:** PSNR=25.225351079305014, GS=202838, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/rpng/increase/opacity01.

**2026-09-28 protected prune opacity01 / utmm40 period=300 birth_denominator=1.0:** PSNR=22.129522300060884, GS=98000, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/utmm/base/opacity01.

**2026-09-28 protected prune opacity01 / utmm40 period=300 birth_denominator=0.8:** PSNR=22.27217948583909, GS=121363, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/utmm/increase/opacity01.

- 2026-09-28 [Init+25%와300주기비교완료](init_increase/SUMMARY.md): 6회PASS,평균+0.077dB이나Aria하락으로공통채택은보류.
