#!/usr/bin/env python3
"""
floater_metric_region.py
========================
표준 floater 지표 (ORB 트랙, 2026-07-12 채택).

GT = 수동 라벨 2,817개로 조각한 3D 삭제 영역 (dilate ∪ tetra 사면체 채움,
`results/diagnostic/floater_region_gt.npz`, 85.4m³, 라벨 recall 98%+,
exp32 가시 표면 침범 0). 사람이 검증한 공간을 상속하므로 현존 지표 중
신뢰도 최고. 자세한 근거: context/rounds/round8_carve_loss_design.md Round 12.

지표 (낮을수록 좋음):
  region_n        영역 안 gaussian 수
  region_visible  영역 안 op>0.3 수 (눈에 보이는 floater)
  region_contrib% 영역 안 시각 기여량 (op×면적×노출수) 비율

⚠ 한계:
  - ORB 트랙(data/03_rgb_3dgs_full 좌표계) 전용 — MPS 트랙은 좌표계가 달라 부적용.
  - 영역 밖 floater는 못 셈 (새 run 먼지 일부가 영역 밖에 실재함을 패치 스팟체크로
    확인 — 이 지표는 하한). ray-density(unseen-voxel) 지표와 상호보완으로 사용.

사용: python scripts/analysis/floater_metric_region.py <ply> [<ply> ...]
"""
import sys
from pathlib import Path

import numpy as np
from plyfile import PlyData

GT = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/floater_region_gt.npz")
_z = np.load(GT)
_mask, _lo, _vox = _z["mask"], _z["lo"], float(_z["voxel"])
_dims = np.array(_mask.shape)


def region_metric(ply_path):
    v = PlyData.read(str(ply_path))["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1).astype(np.float64))
    try:
        visn = np.clip(np.asarray(v["accum_visibility"]).astype(np.float64), 1, None)
    except Exception:
        visn = np.ones(len(xyz))
    contrib = opac * np.sort(scales, 1)[:, 1:].prod(1) * visn

    gi = np.floor((xyz - _lo) / _vox).astype(int)
    ok = ((gi >= 0) & (gi < _dims[None, :])).all(1)
    inreg = np.zeros(len(xyz), bool)
    inreg[ok] = _mask[gi[ok, 0], gi[ok, 1], gi[ok, 2]]

    return {
        "n": len(xyz),
        "region_n": int(inreg.sum()),
        "region_visible": int((inreg & (opac > 0.3)).sum()),
        "region_contrib_pct": float(contrib[inreg].sum() / contrib.sum() * 100),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    print(f"{'run':<58}{'N':>9}{'region_n':>9}{'가시':>6}{'기여%':>8}")
    for p in sys.argv[1:]:
        r = region_metric(p)
        name = Path(p).parts[-4] if "point_cloud" in str(p) else Path(p).name
        print(f"{name[:56]:<58}{r['n']:>9,}{r['region_n']:>9,}{r['region_visible']:>6,}"
              f"{r['region_contrib_pct']:>7.2f}%")


if __name__ == "__main__":
    main()
