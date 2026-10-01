# Four-scene fixed40 dense depth comparison

> 후속 사용자 결정: **B를 채택하고 main에 `6d200f0f`로 병합했다.** [채택·병합 검증](../b_condition_main_adoption/README.md). 아래의 main 미변경 표기는 비교 실험 당시의 상태다.

2026-10-01. Status: **EVIDENCE — completed, 24/24 maps**; no merge into main.

## 결과와 해석

40 updates/KF, mapper seed 0·1, 네 장면의 세 조건을 모두 실행했다.
**B(dense RGB)가 네 장면 모두 held-out PSNR 최고**이고,
C(dense RGB+depth)는 B보다 평균 0.066/0.092/0.216/0.100dB 낮았다
(Aria1253/RPNG/UTMM/Aria1253rot 순). 같은 seed끼리도 8쌍 모두 C가 낮다.
C는 A(KF-only)보다는 네 장면 모두 높은 PSNR을 보였다.

Geometry에는 이득과 상충이 함께 있다.

- B→C의 held-out tracker depth MAE는 네 장면 모두 감소했다:
  0.1901→0.1782 / 0.1552→0.1494 / 0.5490→0.5316 / 0.2147→0.2050m.
  이 지표는 학습 tracker와 관련되어 독립 GT 판정으로 사용하지 않는다.
- 독립 MPS 기준 Aria1253/rot의 앞쪽 termination mass는
  18.11→15.43% / 16.42→14.82%, 표면 mass는
  67.15→68.98% / 68.00→68.72%로 개선됐다. 반면 뒤쪽 mass는
  14.73→15.60% / 15.59→16.46%로 증가했다. Hole 비율은 두 장면에서 감소했다.
- Aria1253의 독립 수동 empty-space 영역에서 opacity>0.3 Gaussian 수는
  B 165.5→C 146.0개(−11.8%), opacity-weighted support는
  196.49→174.40(−11.2%)다. 두 seed와 eroded/nominal/dilated mask 모두
  같은 감소 방향이다. 정합 residual p90 0.0384m, mask voxel 0.075m를 함께 기록한다.
- UTMM의 BA hole 비율은 B 10.52→C 10.75%로 소폭 증가했다.

따라서 이번 조건에서는 **화질 우선이면 B**, 앞쪽 floater 감소와 작은 화질
비용의 교환을 검토하려면 C가 근거를 제공한다. C를 모든 geometry 지표에서
우월하거나 새로운 기본값으로 채택했다고 해석하지 않는다. RPNG/UTMM의 독립
surface GT 검증, full live tracking/deadline 검증은 이번 실험 범위에 포함되지 않는다.
두 seed는 mapper 반복이며 독립 tracking 반복이나 통계적 유의성 검정이 아니다.

전체 수치: [SUMMARY.md](SUMMARY.md). 지도 24개: [PLY_INDEX.md](PLY_INDEX.md).

Question: with 40 render/backward/Adam updates per admitted mapping keyframe,
does adding dense RGB and then transported dense depth improve held-out appearance
and geometry? This is causal frozen-tracker mapper replay, not a strict 1.5×
live-budget benchmark. There is no final polish or post-stream optimizer update.

Pinned branch: `fixed40-geometry-merge`, commit
`37fb915242b55249c26bb4707a0d800d8789a1d5`, isolated worktree
`/tmp/vigs-dense-depth-37fb9152`. Main is unchanged.

| Arm | Keyframe supervision | Auxiliary supervision |
|---|---|---|
| A `kf_rgbd_only` (BP) | RGB + metric depth L1 | Additional keyframes with the same loss |
| B `kf_rgbd_dense_rgb` (PN) | RGB + metric depth L1 | Dense RGB |
| C `kf_rgbd_dense_rgbd` (U1) | RGB + metric depth L1 | Dense RGB + transported metric depth L1 |

Depth weight is 0.25 for keyframes and dense frames. Normals, D3 hard-proxy,
opacity-only D3 main term, dense normal/hard/edge/decoupled variants are off.
Dense geometry updates all Gaussian parameters. Dense targets use the two already
available bracketing keyframes, current poses/depth, z-buffer, agreement 5%, and
5×5 depth discontinuity threshold 10%. No MPS data enters training.

The branch's photometric forms are preserved: KF uses 0.95 × masked RGB L1;
dense uses 0.8 × L1 + 0.2 × DSSIM. Thus A→B measures the existing dense
supervision treatment as a whole; B→C isolates the added dense depth term.

All arms use the selected fixed40 ERVS/growth 3:3:6 recipe, one Adam step per
render, identical birth/protected-opacity-prune settings and frozen tracker inputs.
A replaces auxiliary dense slots with keyframes; it does not reduce total work.
Mapper seeds 0 and 1 (the tracker archive remains fixed), without scene-dependent tuning, are run on aria1253,
aria1253rot, RPNG table_06, and UTMM square-1 (24 maps total).

| Scene | Fixed held-out RGB views | Total updates, every arm/seed |
|---|---:|---:|
| aria1253 | 262 | 4,760 |
| table_06 | 555 | 9,080 |
| square-1 | 324 | 3,600 |
| aria1253rot | 305 | 6,120 |

The inherited budget ledger credits a KF again if it is re-admitted after a
mapper reset. The per-generation/per-arrival ledger is held identical across
arms, including this existing reset behavior. Seeds vary the mapper only.

## Evaluation and acceptance

- Saved-map held-out PSNR against the existing predeclared fixed manifests;
  evaluation repeated twice. Check identical view cohorts, trajectories, and
  per-prefix render counts against the prior four-scene validation.
- Four-scene auxiliary geometry: held-out KF BA-depth MAE, front/within/behind
  fraction (±6.25% depth band), and hole fraction. BA is related to the training
  tracker and **is not independent ground truth**.
- Aria scenes: independent MPS semidense reference, evaluation only, local
  30-KF Sim(3) alignment; report alignment errors and reference support. Also
  termination mass in front of / near / behind the reference surface, so mean
  depth cancellation cannot conceal front mass.
- aria1253: existing independent manually annotated empty-space region metric,
  with registration errors and eroded/dilated-mask sensitivity.
- No claim of independent surface accuracy for RPNG/UTMM without a reference.
  No success decision based only on crash-free completion.

## Artifacts

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_dense_depth_four_scene.py`
- Raw: `results/campaigns/gain_attribution/dense_depth_four_scene/v1`
- [Measured comparison](SUMMARY.md), [named PLY index](PLY_INDEX.md).
- Viewer links: `results/campaigns/gain_attribution/dense_depth_four_scene/v1/ply/<scene>/`
  (named symlinks to immutable result PLYs; raw files are preserved).

2026-10-01 path correction: the initially created singular `context/experiment`
viewer folder was moved into the canonical result campaign. The temporary
launcher alias was removed after all 24 runs completed, and the launcher's viewer
path was corrected. The original launcher and a resolved source lock are retained
in raw `provenance/`; every initial source hash was verified before this path-only
edit. Existing experiment inputs, raw maps, and learning code remain intact.

## 완료 검증

`final_validation.json`에 24개 지도·48회 saved-map 평가, zero-tail, 동일
per-prefix update budget/trajectory/cohort, B↔C 8쌍의 완전히 동일한 supervision
trace, 모든 PLY SHA 보존, 초기 source lock 일치, main/branch clean을 기록했다.
독립 MPS 평가는 12개 지도에서 완료했고 reference ray 수는 Aria1253 73,472개,
rot 101,489개로 조건 간 동일하다. Termination kernel의 renderer RGB/alpha
재현 최대 오차는 0이었다. 학습에서 MPS 사용 0, normal/hard-proxy loss 0,
추가 geometry render 0 조건도 확인했다.

MPS 정합은 local 30-KF Sim(3)이며 local RMS median은 0.0073/0.0080m다.
nearest MPS timestamp gap이 5ms를 넘는 KF는 각각 2/1개이고,
gap 최대는 0.350/0.750초다. 이 진단과 local RMS의 전체 분포는 raw
`mps_alignment_diagnostics.json`에 보존했다. MPS는 독립 semidense reference이며
완전한 dense surface GT로 간주하지 않는다.

Canonical raw tables: `comparison.csv`, `comparison.json`, `COMPARISON.md`.
Complete viewer folder: `results/campaigns/gain_attribution/dense_depth_four_scene/v1/ply/`.

## Reproduce / resume on this machine

Use the pinned detached worktree and existing dataset/extension inventory. The
mapper launcher skips completed map/evaluation stages and never overwrites a PLY.

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python benchmarks/online_gs/campaigns/gain_attribution/run_dense_depth_four_scene.py
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python benchmarks/online_gs/campaigns/gain_attribution/evaluate_dense_depth_four_scene.py
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python benchmarks/online_gs/campaigns/gain_attribution/summarize_dense_depth_four_scene.py
```

Raw `protocol.json`, per-stage command files, source locks, reference hashes,
per-run `evaluation_consistency.json`, and `paired_trace_audit.json` preserve
the exact execution/evaluation contract. `passed` in a run summary denotes
execution and evaluation consistency, **not adoption or a quality win**.
