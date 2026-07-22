"""exp55 carve-loss verification (2026-07-22): offline floater score for VIGS incremental
output PLYs, reusing the SAME field-building algorithm as 3dgs-custom/eval/carve_loss.py
(transit/terminal ray-cast voxel field -> rho -> w = rho * min(d5nn_slam/tau, 1)), scored
against depth-anchor points exported directly from VIGS's own BA-refined tracked depth
(independent of the trained gaussians -- see gs_backend.py::_export_depth_anchors).
Standalone numpy/scipy reimplementation (no torch/cuda needed, point counts are small).
"""
import sys
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter
from plyfile import PlyData

# CarveLossConfig defaults (3dgs-custom/eval/carve_loss.py)
VOXEL = 0.10
RAY_STEP = 0.06
SURF_MARGIN = 0.20
MIN_T = 0.15
MAX_DEPTH = 15.0
TERM_K = 3.0
SMOOTH = 3
D5_TAU = 0.25

FX = FY = 226.5625
CX = CY = 232.0
IMG_W = IMG_H = 464


def load_images_txt(path):
    Rs, ts = [], []
    for line in open(path):
        p = line.strip().split()
        if len(p) < 9 or p[0].startswith("#"):
            continue
        qw, qx, qy, qz = [float(x) for x in p[1:5]]
        t = np.array([float(x) for x in p[5:8]])
        # qvec -> rotmat (w,x,y,z order, matches carve_loss.py's _qvec2rotmat)
        R = np.array([
            [1 - 2*qy*qy - 2*qz*qz, 2*qx*qy - 2*qw*qz,     2*qx*qz + 2*qw*qy],
            [2*qx*qy + 2*qw*qz,     1 - 2*qx*qx - 2*qz*qz, 2*qy*qz - 2*qw*qx],
            [2*qx*qz - 2*qw*qy,     2*qy*qz + 2*qw*qx,     1 - 2*qx*qx - 2*qy*qy]])
        Rs.append(R)
        ts.append(t)
    return np.array(Rs, np.float32), np.array(ts, np.float32)


def load_points3d_txt(path):
    pts = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        tok = line.split()
        if len(tok) >= 7:
            pts.append([float(tok[1]), float(tok[2]), float(tok[3])])
    return np.array(pts, np.float32)


def build_fields(Rs, ts, slam, lo, dims):
    n_vox = int(np.prod(dims))
    transit = np.zeros(n_vox, dtype=np.float32)
    terminal = np.zeros(n_vox, dtype=np.float32)
    max_steps = int(MAX_DEPTH / RAY_STEP)
    step_d = np.arange(max_steps, dtype=np.float32) * RAY_STEP + MIN_T

    def deposit(pts, acc):
        idx = np.floor((pts - lo) / VOXEL).astype(np.int64)
        inb = ((idx >= 0) & (idx < dims[None, :])).all(1)
        idx = idx[inb]
        flat = (idx[:, 0] * dims[1] + idx[:, 1]) * dims[2] + idx[:, 2]
        acc += np.bincount(flat, minlength=n_vox).astype(np.float32)

    for ci in range(len(Rs)):
        R, t = Rs[ci], ts[ci]
        C = (-R.T @ t).astype(np.float32)
        pc = slam @ R.T + t
        z = pc[:, 2]
        ok = z > 0.2
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 0) & (u < IMG_W) & (v >= 0) & (v < IMG_H) & (z < MAX_DEPTH)
        P = slam[ok]
        if len(P) == 0:
            continue
        dvec = P - C
        dist = np.linalg.norm(dvec, axis=1)
        dirs = dvec / dist[:, None]
        valid = step_d[None, :] < (dist - SURF_MARGIN)[:, None]
        pts = C[None, None, :] + step_d[None, :, None] * dirs[:, None, :]
        deposit(pts[valid], transit)
        term_off = np.linspace(-SURF_MARGIN, SURF_MARGIN, 5, dtype=np.float32)
        tpts = C[None, None, :] + (dist[:, None] + term_off[None, :])[:, :, None] * dirs[:, None, :]
        deposit(tpts.reshape(-1, 3), terminal)
    return transit.reshape(tuple(dims)), terminal.reshape(tuple(dims))


def load_ply(path):
    v = PlyData.read(str(path))["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    return xyz, opac


def score_run(images_txt, points3d_txt, ply_path, label):
    Rs, ts = load_images_txt(images_txt)
    slam = load_points3d_txt(points3d_txt)
    print(f"[{label}] {len(Rs)} cams, {len(slam)} anchor pts")

    centers = np.stack([-R.T @ t for R, t in zip(Rs, ts)]).astype(np.float32)
    lo = centers.min(0) - np.maximum(centers.max(0) - centers.min(0), [2., 2., 3.])
    hi = centers.max(0) + np.maximum(centers.max(0) - centers.min(0), [2., 2., 3.])
    dims = np.ceil((hi - lo) / VOXEL).astype(int) + 1
    print(f"[{label}] field grid {tuple(dims)} ({np.prod(dims):,} voxels)")

    transit, terminal = build_fields(Rs, ts, slam, lo, dims)
    transit = uniform_filter(transit, size=SMOOTH)
    terminal = uniform_filter(terminal, size=SMOOTH)
    rho = transit / (transit + TERM_K * terminal + 1e-6)

    slam_tree = cKDTree(slam)

    xyz, opac = load_ply(ply_path)
    gi = np.floor((xyz - lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
    rho_at = np.zeros(len(xyz), dtype=np.float32)
    rho_at[inb] = rho[gi[inb, 0], gi[inb, 1], gi[inb, 2]]

    d5, _ = slam_tree.query(xyz, k=5, workers=-1)
    d5 = d5.mean(1)
    w = rho_at * np.clip(d5 / D5_TAU, None, 1.0)
    score = w  # offline diagnostic: skip the training-time "1 - max_opacity nearby"
               # neighbourhood-protection term, use opacity-gated visible score instead

    n = len(xyz)
    visible = opac > 0.3
    high_score = score > 0.3  # matches carve_loss.py's score_min/prune_score_min convention
    visible_floater = visible & high_score
    return {
        "label": label,
        "n": n,
        "mean_score": float(score.mean()),
        "mean_score_visible": float(score[visible].mean()) if visible.sum() else 0.0,
        "n_visible": int(visible.sum()),
        "n_visible_floater": int(visible_floater.sum()),
        "visible_floater_pct": float(visible_floater.sum() / max(1, visible.sum()) * 100),
    }


# Usage: python exp55_score_carve_vigs.py <label1>=<run_dir1> [<label2>=<run_dir2> ...]
# Each run_dir must contain images.txt/points3D.txt (from a VIGS run launched with
# VIGS_DEPTH_ANCHOR_LOG=<run_dir>/points3D.txt VIGS_DEPTH_ANCHOR_CAM_LOG=<run_dir>/images.txt)
# and 3dgs_before_final.ply (the run's own output). FX/FY/CX/CY/IMG_W/IMG_H at the top of
# this file are hardcoded to the 1253 scene's intrinsics -- update them for other scenes.
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("Usage: python exp55_score_carve_vigs.py <label>=<run_dir> [<label>=<run_dir> ...]")
        sys.exit(1)
    runs = []
    for arg in sys.argv[1:]:
        label, d = arg.split("=", 1)
        runs.append((label, Path(d)))

    results = []
    for label, d in runs:
        r = score_run(d / "images.txt", d / "points3D.txt", d / "3dgs_before_final.ply", label)
        results.append(r)
        print(r)

    print("\n=== summary ===")
    print(f"{'run':<12}{'N':>9}{'visible':>9}{'vis_floater':>13}{'vis_floater%':>14}{'mean_score':>12}{'mean_score_vis':>16}")
    for r in results:
        print(f"{r['label']:<12}{r['n']:>9,}{r['n_visible']:>9,}{r['n_visible_floater']:>13,}"
              f"{r['visible_floater_pct']:>13.2f}%{r['mean_score']:>12.4f}{r['mean_score_visible']:>16.4f}")
