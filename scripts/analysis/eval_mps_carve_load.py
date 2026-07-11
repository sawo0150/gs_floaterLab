#!/usr/bin/env python3
"""
eval_mps_carve_load.py
======================
MPS 트랙 run(exp08/exp13 등)의 30k ply에 MPS carve field 기반 챔피언 score를
적용해 먼지 부하를 측정. ORB 트랙의 eval_carve_load.py와 동일 지표.

주의: MPS anchor는 626k semidense (outlier 포함) — d5는 terminal 증거>10인
anchor만 사용해 outlier 합법화를 차단(수정B; ORB에선 무효과였지만 MPS는
outlier가 실재하므로 적용).
"""
import sys
from pathlib import Path

import numpy as np
from plyfile import PlyData
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter

VOXEL = 0.10
FIELD = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/mps_carve_field.npz")
MPS_PTS = Path("/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253/sparse/0/points3D.txt")

_z = np.load(FIELD)
_ts = uniform_filter(_z["transit"], 3)
_es = uniform_filter(_z["terminal"], 3)
_ratio = _ts / (_ts + 3.0 * _es + 1e-6)
_lo, _dims = _z["lo"], _z["dims"]


def _load_pts():
    pts = []
    for line in open(MPS_PTS):
        if line.startswith("#") or not line.strip():
            continue
        t = line.split()
        if len(t) >= 7:
            pts.append([float(t[1]), float(t[2]), float(t[3])])
    return np.array(pts, np.float32)


def _grid(field, p):
    gi = np.floor((p - _lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < _dims[None, :])).all(1)
    out = np.zeros(len(p), np.float32)
    out[inb] = field[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    return out


print("[init] MPS anchors + terminal 검증 ...")
_anchors = _load_pts()
_term = _grid(_es, _anchors)
_good = _term > 10
print(f"  anchors {len(_anchors):,} → terminal>10: {_good.sum():,}")
_tree = cKDTree(_anchors[_good])


def evaluate(ply_path):
    v = PlyData.read(str(ply_path))["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1).astype(np.float64))
    rho = _grid(_ratio, xyz)
    d5, _ = _tree.query(xyz, k=5, workers=-1)
    w = rho * np.clip(d5.mean(1) / 0.25, 0, 1)
    pairs = cKDTree(xyz).query_ball_point(xyz, 0.05, workers=-1, return_sorted=False)
    maxop = np.fromiter((opac[p].max() for p in pairs), dtype=np.float64, count=len(xyz))
    s = w * (1.0 - maxop)
    try:
        visn = np.clip(np.asarray(v["accum_visibility"]).astype(np.float64), 1, None)
    except Exception:
        visn = np.ones(len(xyz))
    contrib = opac * np.sort(scales, 1)[:, 1:].prod(1) * visn
    hi = s > 0.5
    return {"n": len(xyz), "s>0.5": int(hi.sum()),
            "vis": int((hi & (opac > 0.3)).sum()),
            "mass": float(s.sum()),
            "dust%": float(contrib[hi].sum() / contrib.sum() * 100)}


if __name__ == "__main__":
    print(f"{'run':<62}{'N':>9}{'s>0.5':>8}{'가시':>6}{'질량':>9}{'먼지%':>7}")
    for p in sys.argv[1:]:
        r = evaluate(p)
        name = Path(p).parts[-4] if "point_cloud" in str(p) else Path(p).name
        print(f"{name:<62}{r['n']:>9,}{r['s>0.5']:>8,}{r['vis']:>6,}{r['mass']:>9.0f}{r['dust%']:>6.2f}%")
