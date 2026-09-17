# ERCB benchmark-A

exp03에서 RPNG table_01 저예산 `+1.03dB`를 만든 historical fixed-replay 방식을
RTX 5070 Ti의 UTMM/RPNG 16-scene inventory 전체에 저·중·고예산으로 적용하는
무튜닝 전이 패널이다. Full-pool RR과 ERCB에 더해 최근 10개 keyframe interval의
RGB frame만 유지하는 window10 RR을 같은 update budget으로 비교한다.

- 실제 pair 가능: exp80 source가 완전한 13 scene
- unavailable: UTMM slow-straight-1, RPNG table_07/08
- 고정 비교: event당 15/30/60 update, seed0, full RR/window10 RR/interval relative-floor ERCB
- 결과 문서: [summary.md](summary.md)

실행 순서:

```bash
/home/wosas/miniconda3/envs/3dgs/bin/python prepare_datasets.py
/home/wosas/miniconda3/envs/3dgs/bin/python prepare_manifest.py
/home/wosas/miniconda3/envs/3dgs/bin/python run_panel.py
/home/wosas/miniconda3/envs/3dgs/bin/python summarize.py
```

각 단계는 기존 output을 덮어쓰지 않는다. `run_panel.py`는 완료된 job을 검증 후 건너뛰므로
중단 뒤 같은 명령으로 재개할 수 있다.

RPNG table_03 event60 ERCB의 최초 중단 산출물은
`ercb_s0_interrupted_20260915T215046`로 보존되어 있으며 집계에서 제외한다.
같은 arm의 clean rerun만 최종 결과에 포함된다.
