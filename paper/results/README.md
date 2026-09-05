# results/ — 논문 숫자의 유일한 출처

```
원격 실험(5090/5070Ti)
   └→ results/runs/<run_id>/manifest.json  +  metrics.csv     (경량, git에 커밋)
        └→ results/tables/<table_name>.csv                     (표 하나 = CSV 하나)
             └→ scripts/make_tables.py
                  └→ latex/tab/<table_name>.tex  →  \input      (git ignore, 생성물)
```

## 규칙

- **latex 에 숫자를 손으로 적지 않는다.** exp72 재실험이 확정되어 있어, 숫자가 여러 곳에
  박히면 반드시 어긋난다.
- raw 로그·PLY·체크포인트는 **git에 넣지 않는다.** 원격 머신에 두고 `manifest.json` 에
  경로만 기록한다.
- 모든 run은 `manifest.json` 에 **protocol 버전**을 적는다
  (→ [`../experiments/protocol/CURRENT.md`](../experiments/protocol/CURRENT.md)).
- `run_id` 규칙: `<Pnn>_<YYYYMMDD>_<machine>_<arm>_seed<N>`
  예: `P01_20260908_5070ti_token-noprepurchase_seed0`

## metrics.csv 최소 열

```
run_id,scene,seed,psnr_heldout,ssim,lpips,wall_time_s,final_pool,rho_H,lifetime_mid_first,notes
```

실험마다 열이 늘어나는 건 괜찮지만, 위 열 이름은 바꾸지 않는다 (`make_tables.py` 가 참조).
