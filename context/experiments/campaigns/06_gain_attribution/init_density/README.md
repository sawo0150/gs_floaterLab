# Gaussian birth density at 15 / 40 renders per KF (2026-09-27)

사용자 요청: 기본 mapping 설정에서 Gaussian 초기화 수를 줄여15와40 renders/KF 모두 비교한다. 최근사용한ERVS/κ16/τ4/3:3:6/영상별Adam/denseRGB를 기준으로 유지한다. 기본 JSON preset 변경은 하지 않는다.

- 세 scene 공통 factor1/2/4로 PPM downsample denominator를 곱한다. 현재 init64, regular256을128/512 또는256/1024로 변경한다. 첫 지도뿐 아니라 매새로운KF에서depth로생성하는Gaussian을 모두줄인다. Point-size,causal online-rank density2.5/span2, PPM Sobel weighting 등은그대로다. 개수는rounding으로정확히절반/1/4이아닐수있다.
- 각budget×factor×scene=18개fresh runs. Sampler trace,admission,KF arrival/pose/held-out,render/Adam총및prefix는해당budget의기존baseline과일치검증한다. Gaussian총수는기존의1/factor±2%인지검사하고per-birth CSV로init/regular모두적용됨을검증한다.
- Densify/prune/Carve/blurOFF,scaleprojectionON,zero-tail. 관측Gaussian birth는계속한다. 장면별절대시점/freeze/topologycutoff없음.
- 근사1/2·1/4 후보가세scene공통으로어떤품질/시간tradeoff인지보고한다. 사전품질보존참고선은각scene동일budgetfreshbaseline 대비PSNR감소≤0.1dB(통계적유의성기준아님);더나은숫자만보고선택하지않는다. Map 품질을trainPSNR로판정하지않는다.
- mapper seconds와held-outPSNR,최종GS,PyTorch peak allocated/reserved memory 기록. Peak는mapper 실행구간이며system전체VRAM또는동시tracking메모리측정이아니다.
- Point count가달라지면PPM RNG표본과nearest-neighbor기반초기scale도달라질수있다. 기존표본의완전nested subset이아니며init budget recipe변경효과로해석한다.
- 세개발scene·단일seed·frozen causal tracker. Live나geometry/floater검증아님.

## 실행 기록

**2026-09-27 init density budget15 b15_d1 / aria:** execution=True, audit=True, PSNR=23.25464710206476, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d1/aria.

**2026-09-27 init density budget15 b15_d1 / rpng:** execution=True, audit=True, PSNR=24.023711683943464, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d1/rpng.

**2026-09-27 init density budget15 b15_d1 / utmm:** execution=True, audit=True, PSNR=20.87415121808464, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d1/utmm.

**2026-09-27 init density budget15 b15_d2 / aria:** execution=True, audit=True, PSNR=23.232974969703733, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d2/aria.

**2026-09-27 init density budget15 b15_d2 / rpng:** execution=True, audit=True, PSNR=23.892736204680023, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d2/rpng.

**2026-09-27 init density budget15 b15_d2 / utmm:** execution=True, audit=True, PSNR=20.284989053820386, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d2/utmm.

**2026-09-27 init density budget15 b15_d4 / aria:** execution=True, audit=True, PSNR=23.317019058547857, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d4/aria.

**2026-09-27 init density budget15 b15_d4 / rpng:** execution=True, audit=True, PSNR=23.506212351343653, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d4/rpng.

**2026-09-27 init density budget15 b15_d4 / utmm:** execution=True, audit=True, PSNR=19.369094477759468, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d4/utmm.

**2026-09-27 init density budget40 b40_d1 / aria:** execution=True, audit=True, PSNR=25.910708995265814, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d1/aria.

**2026-09-27 init density budget40 b40_d1 / rpng:** execution=True, audit=True, PSNR=25.220881003302498, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d1/rpng.

**2026-09-27 init density budget40 b40_d1 / utmm:** execution=True, audit=True, PSNR=22.223149417359153, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d1/utmm.

**2026-09-27 init density budget40 b40_d2 / aria:** execution=True, audit=True, PSNR=25.699089334211276, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d2/aria.

**2026-09-27 init density budget40 b40_d2 / rpng:** execution=True, audit=True, PSNR=25.011698600837775, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d2/rpng.

**2026-09-27 init density budget40 b40_d2 / utmm:** execution=True, audit=True, PSNR=21.528685793464568, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d2/utmm.

**2026-09-27 init density budget40 b40_d4 / aria:** execution=True, audit=True, PSNR=25.409114167890475, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d4/aria.

**2026-09-27 init density budget40 b40_d4 / rpng:** execution=True, audit=True, PSNR=24.59093381520864, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d4/rpng.

**2026-09-27 init density budget40 b40_d4 / utmm:** execution=True, audit=True, PSNR=20.53334234967644, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d4/utmm.
