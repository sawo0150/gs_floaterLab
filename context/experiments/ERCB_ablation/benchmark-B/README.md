# benchmark-B — stride20 initialization full-family panel

목적은 benchmark-A의 sparse stride40 initialization 병목을 줄였을 때 저예산 ERCB 이득과
절대 held-out PSNR이 UTMM, RPNG, Aria 전체 입력으로 전이되는지 확인하는 것이다.

## 사전 고정 protocol

- source scene: UTMM 8, RPNG 8, 현재 VIGS 입력이 있는 Aria 4
- 한 VIGS source run에서 stride40/20 depth anchor를 동시에 export
- primary panel: stride20 × RR/ERCB × event당 15/30/60 update
- paired bridge: 같은 source의 stride40 × RR/ERCB × event당 15 update
- 공통: seed0, RGB-only, fixed topology, llffhold-8, optimizer tail 0
- 제외: 이미 benchmark-A에서 기각된 recent-window10 RR
- 실패 scene은 재시도하되 성공한 것처럼 제외하지 않고 inventory에 unavailable로 기록

이것은 final online VIGS pose/init를 고정한 scheduler-isolation replay다. Strict end-to-end
VIGS 결과가 아니며, stride20의 계산비 증가 때문에 fixed-update 결과와 wall-time 비용을
함께 보고한다.

## 실행

```bash
/home/wosas/miniconda3/envs/3dgs/bin/python run_source_exports.py
/home/wosas/miniconda3/envs/3dgs/bin/python prepare_datasets.py
/home/wosas/miniconda3/envs/3dgs/bin/python prepare_manifest.py
/home/wosas/miniconda3/envs/3dgs/bin/python run_panel.py
/home/wosas/miniconda3/envs/3dgs/bin/python summarize.py
```

각 단계는 완성된 산출물을 검증하고 재사용하며 불완전한 디렉터리를 덮어쓰지 않는다.
