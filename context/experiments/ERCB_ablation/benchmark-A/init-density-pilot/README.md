# benchmark-A init-density pilot

목적은 benchmark-A의 낮은 절대 PSNR이 sparse fixed initialization의 용량 상한인지
확인하는 것이다. 다른 run의 point cloud나 jitter 복제를 쓰지 않고, 한 VIGS run의 동일
BA-refined keyframe depth/pose에서 두 grid를 동시에 export한다.

- control: depth anchor stride 40
- treatment: depth anchor stride 20 (이론상 최대 4배 sampling)
- 대표 scene: UTMM `square-1`, RPNG `table_01`
- replay gate: historical benchmark-A의 event당 15 update, seed0, full RR와 ERCB
- 공통: 동일 RGB, trajectory, keyframe boundaries, schedule, RGB-only, fixed topology,
  llffhold-8, zero optimizer tail

이것은 strict end-to-end VIGS 결과가 아니라 initialization density와 scheduler의 상호작용을
보는 fixed-replay 진단이다. Dense init이 low-budget에서 두 scene 모두 control보다 좋아야
고예산 또는 전체 panel로 확장한다.

실행 순서:

```bash
bash run_source_exports.sh
/home/wosas/miniconda3/envs/3dgs/bin/python prepare_replays.py
/home/wosas/miniconda3/envs/3dgs/bin/python run_pilot.py
/home/wosas/miniconda3/envs/3dgs/bin/python summarize.py
```

상태: **8/8 완료, pilot gate 통과.** stride20은 두 장면·두 scheduler의 4/4
pair에서 held-out PSNR을 높였다. 확정 수치와 비용 분석은 [RESULT.md](RESULT.md)에 있다.
source exporter의 opt-in 변경은 `evidence/vigs_dual_anchor_export.patch`로 보존했다.
