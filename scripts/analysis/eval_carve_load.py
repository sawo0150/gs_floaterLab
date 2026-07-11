#!/usr/bin/env python3
"""
eval_carve_load.py
==================
임의 run의 30k ply에 대해 챔피언 score 기반 "먼지 부하" 지표를 측정한다.
exp38 채점용 표준 지표 (라벨 없는 run에도 적용 가능).

지표:
  - score>0.5 총 개수 / 가시(op>0.3) 개수  : 먼지 부하 (수동 라벨 AUC 0.98 검증됨)
  - score 질량 Σscore                       : 연속 부하
  - score>0.5 점들의 시각 기여량 합          : 렌더에 보이는 먼지 총량
  - (참고) unseen-voxel & op>0.5            : 기존 ray-density 지표와 상보

기준값 (2026-07-11 측정):
  exp30 baseline : score>0.5 = 11,537 (가시 884),  질량 14,609
  exp32 plateau  : score>0.5 = 12,960 (가시 936),  질량 15,858
  exp37 dense    : score>0.5 = 58,510 (가시 1,558), 질량 60,028

사용:
  python scripts/analysis/eval_carve_load.py <ply_path> [<ply_path> ...]
"""
import sys
from pathlib import Path

import numpy as np
from plyfile import PlyData
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter

sys.path.insert(0, str(Path(__file__).parent))
from design_floater_loss_candidates import BASE, VOXEL, load_slam

_z = np.load(BASE / "carve_fields.npz")
_ts = uniform_filter(_z["transit"], 3)
_es = uniform_filter(_z["terminal"], 3)
_ratio = _ts / (_ts + 3.0 * _es + 1e-6)
_lo, _dims = _z["lo"], _z["dims"]
_slam_tree = cKDTree(load_slam())


def champion_score(xyz, opac, maxop_radius=0.05, d5_tau=0.25):
    gi = np.floor((xyz - _lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < _dims[None, :])).all(1)
    rho = np.zeros(len(xyz), np.float32)
    rho[inb] = _ratio[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    d5, _ = _slam_tree.query(xyz, k=5, workers=-1)
    w = rho * np.clip(d5.mean(1) / d5_tau, 0, 1)
    pairs = cKDTree(xyz).query_ball_point(xyz, maxop_radius, workers=-1, return_sorted=False)
    maxop = np.fromiter((opac[p].max() for p in pairs), dtype=np.float64, count=len(xyz))
    return w * (1.0 - maxop)


def evaluate(ply_path):
    v = PlyData.read(str(ply_path))["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1).astype(np.float64))
    s = champion_score(xyz, opac)

    try:
        visn = np.asarray(v["accum_visibility"]).astype(np.float64)
    except Exception:
        visn = np.ones(len(xyz))
    contrib = opac * np.sort(scales, 1)[:, 1:].prod(1) * np.clip(visn, 1, None)

    hi = s > 0.5
    return {
        "n": len(xyz),
        "score>0.5": int(hi.sum()),
        "score>0.5 & op>0.3": int((hi & (opac > 0.3)).sum()),
        "score_mass": float(s.sum()),
        "dust_contrib_pct": float(contrib[hi].sum() / contrib.sum() * 100),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    print(f"{'run':<52}{'N':>9}{'s>0.5':>8}{'가시':>6}{'질량':>9}{'먼지기여%':>9}")
    for p in sys.argv[1:]:
        r = evaluate(p)
        name = Path(p).parts[-4] if "point_cloud" in p else Path(p).name
        print(f"{name:<52}{r['n']:>9,}{r['score>0.5']:>8,}{r['score>0.5 & op>0.3']:>6,}"
              f"{r['score_mass']:>9.0f}{r['dust_contrib_pct']:>8.2f}%")


if __name__ == "__main__":
    main()
