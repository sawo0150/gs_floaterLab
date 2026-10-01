# 누적pool에서 recent KF window 몫의 필요성 (2026-09-28)

사용자 요청: 직전 init1.25배·prune0.1/300·최근10KF birth보호를 채택하고,window가 필요한 이유를 비율조정과window몫제거로 확인한다. 결론을 미리 정하지 않는다.

## 고정 설정 및 범위

채택설정은 `benchmarks/online_gs/campaigns/gain_attribution/selected_mapping_recipe.json`에 고정하고 `run_selected_mapping.py`로 재생 실행할 수 있다. 이는 검증된 mapper replay recipe이며 라이브런타임에pruning까지이식했다는뜻은아니다. 논문tex는이번작업에서수정하지않는다.

40renders/KF,PPM생성량1.25배(downsample0.8,init51.2/regular204.8),opacity0.1,prune300renders,최근10KF birth보호,ERVS κ16/τ₀4,영상별Adam,denseRGB,scale projectionON,densify/Carve/blurOFF,seed0.

- 대조군: window/full KF/dense **3:3:6**, 직전세장면결과재사용.
- 감소: **1:5:6**.
- 제거: **0:6:6**.
- Aria1253,RPNG table_06,UTMM square-1. 신규실행6회만. Init/pruning/κ/τ재튜닝없음.

KF전체와dense의목표비중은50:50으로두고recent window의별도몫만전체KF ERVS에넘긴다. Window밖KF와densepool의retention은모든조건에서같다. **0:6:6에서도최근KF는전체KFpool에서선택가능하며,SLAM frontend의window를없애는실험이아니다.** 누적pool은지도generation내에서age/window에따라삭제하지않는다는뜻이며,무한메모리나무제한동시학습의주장이아니다.

## 확인 항목

- 동일render/Adam총및prefix,causal입력pose,held-out평가,admission과풀membership,PPM birth개수,prune주기와최근점보호.
- 실제window/KF/dense학습횟수,전체KF선택중최근window에속한영상비중,loss종류및LR시점차이를보고한다. 초기pool부족·중복방지·잔여quota때문에명목비율만으로동일RGB/geometry횟수라고단정하지않는다.
- PSNR,최종GS,mapper시간. Sampling이달라지면opacity와prune결과도달라질수있으므로최종GS를동일하게강제하지않는다.
- 단일seed고정work실험으로window의보편적필요성이나실시간성/geometry개선을증명하지않는다.

## 논문에서 구분할 내용

관측을언제pool에서제거하는지(retention)와어디에학습량을배분하는지(sampling allocation)는별개다. 현구조는모든admittedhistory를보관하면서최근KF에도별도몫을주는방식이다. Window가새geometry의초기정제를돕는다는설계의도는가능하지만실험전에필수라고단정하지않는다. KF fullpool도동일한RGB-D/normal loss를쓰므로window만geometry를학습한다고설명하면안된다.

논문 `paper/latex/sec/4_method.tex`는아직native/flexible service시대의기술이남아있으며,current unified336과같은구조라고볼수없다. HumanTech의짧은ERVS설명도모든선택이하나의globalERVS인것처럼읽히지않도록범위를명시할필요가있다.

## 실행 기록

**2026-09-28 window quota 156 / aria40:** PSNR=25.8073416193023, GS=194674, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/aria/156.

**2026-09-28 window quota 066 / aria40:** PSNR=25.778746939797436, GS=193307, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/aria/066.

**2026-09-28 window quota 156 / rpng40:** PSNR=25.183229226464622, GS=199189, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/rpng/156.

**2026-09-28 window quota 066 / rpng40:** PSNR=24.9324430826548, GS=193157, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/rpng/066.

**2026-09-28 window quota 156 / utmm40:** PSNR=22.214482425171653, GS=121702, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/utmm/156.

**2026-09-28 window quota 066 / utmm40:** PSNR=22.10634505012889, GS=121305, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/utmm/066.

## 완료 요약

신규 6회와 독립 감사 모두 통과했다. 1:5:6 평균 −0.025dB, 0:6:6 평균 −0.154dB. 채택 3:3:6을 유지하며, full-history retention과 recent quota를 구분한다. [결과 및 해석](SUMMARY.md).
