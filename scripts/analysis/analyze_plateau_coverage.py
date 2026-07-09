#!/usr/bin/env python3
"""
Plateau coverage analysis:
For each Gaussian in a saved PLY, compute anisotropic distance to nearest anchor
and report % inside / outside plateau (D_aniso < 1 = inside = zero-loss).
"""
import sys
import glob
import argparse
import numpy as np
from pathlib import Path
from sklearn.neighbors import NearestNeighbors
from plyfile import PlyData

# ── Config ────────────────────────────────────────────────────────────────────
ANCHOR_PATH = Path(
    "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab"
    "/results/diagnostic/plateau_ellipsoid_v4_20260705_041132/anchors_all_depth_pro.npy"
)
RESULTS_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results")

# Ellipsoid params (same as mps_depthpro_v4.yaml)
KNN_K   = 5
ALPHA_N = 0.4
ALPHA_T = 0.9
TAU_MIN = 0.03
TAU_N_MAX = 0.30
TAU_T_MAX = 0.60


def load_gaussian_xyz(ply_path: Path) -> np.ndarray:
    data = PlyData.read(str(ply_path))
    el = data["vertex"]
    xyz = np.stack([el["x"], el["y"], el["z"]], axis=1).astype(np.float32)
    return xyz


def build_ellipsoid_params(anchors: np.ndarray):
    N = len(anchors)
    nbrs = NearestNeighbors(n_neighbors=KNN_K + 1, algorithm="ball_tree").fit(anchors)
    dists, inds = nbrs.kneighbors(anchors)
    h_j = dists[:, KNN_K].astype(np.float32)

    tau_n = np.clip(ALPHA_N * h_j, TAU_MIN, TAU_N_MAX).astype(np.float32)
    tau_t = np.clip(ALPHA_T * h_j, TAU_MIN, TAU_T_MAX).astype(np.float32)

    frames = np.empty((N, 3, 3), dtype=np.float32)
    for i in range(N):
        neigh = anchors[inds[i, 1:KNN_K + 1]]
        X = neigh - neigh.mean(0)
        cov = (X.T @ X) / max(KNN_K - 1, 1)
        _, evec = np.linalg.eigh(cov)
        frames[i] = np.stack([evec[:, 1], evec[:, 2], evec[:, 0]], axis=1)

    return tau_n, tau_t, frames


def compute_d_aniso_batch(xyz: np.ndarray, anchors: np.ndarray,
                           tau_n: np.ndarray, tau_t: np.ndarray,
                           frames: np.ndarray,
                           top_k: int = 4) -> np.ndarray:
    """For each Gaussian, compute D_aniso to nearest anchor (approximate via top-k Euclidean)."""
    # Step 1: find top-k Euclidean nearest anchors
    nbrs = NearestNeighbors(n_neighbors=top_k, algorithm="ball_tree").fit(anchors)
    _, nn_idx = nbrs.kneighbors(xyz)   # (N_gauss, top_k)

    N = len(xyz)
    D_min = np.full(N, np.inf, dtype=np.float32)

    for k in range(top_k):
        idx = nn_idx[:, k]                         # (N,)
        delta = xyz - anchors[idx]                 # (N, 3)
        fr = frames[idx]                           # (N, 3, 3)
        tn = tau_n[idx]                            # (N,)
        tt = tau_t[idx]                            # (N,)

        # Project delta into anchor frame: c = fr^T @ delta  →  einsum
        c = np.einsum("ijk,ik->ij", fr.transpose(0, 2, 1), delta)  # (N, 3)
        d2 = (c[:, 0] / tt)**2 + (c[:, 1] / tt)**2 + (c[:, 2] / tn)**2
        D_min = np.minimum(D_min, np.sqrt(d2))

    return D_min


def analyze(exp_dir: Path, anchors: np.ndarray,
            tau_n: np.ndarray, tau_t: np.ndarray, frames: np.ndarray):
    ply = exp_dir / "point_cloud" / "iteration_30000" / "point_cloud.ply"
    if not ply.exists():
        ply7 = exp_dir / "point_cloud" / "iteration_7000" / "point_cloud.ply"
        if ply7.exists():
            ply = ply7
            print(f"  (30k not found, using 7k)")
        else:
            print(f"  PLY not found: {ply}")
            return

    print(f"\n{'='*60}")
    print(f"  {exp_dir.name}")
    print(f"{'='*60}")

    xyz = load_gaussian_xyz(ply)
    print(f"  Gaussians: {len(xyz):,}")

    D = compute_d_aniso_batch(xyz, anchors, tau_n, tau_t, frames)

    inside = (D < 1.0).sum()
    pct_inside = 100.0 * inside / len(D)
    print(f"  Inside plateau  (D<1):  {inside:,}  ({pct_inside:.1f}%)")
    print(f"  Outside plateau (D>=1): {len(D)-inside:,}  ({100-pct_inside:.1f}%)")
    print(f"  D_aniso stats:  min={D.min():.3f}  median={np.median(D):.3f}  "
          f"p75={np.percentile(D,75):.3f}  p90={np.percentile(D,90):.3f}  max={D.max():.3f}")

    # Euclidean distance to nearest anchor
    nbrs = NearestNeighbors(n_neighbors=1, algorithm="ball_tree").fit(anchors)
    euc_dists, _ = nbrs.kneighbors(xyz)
    euc = euc_dists[:, 0]
    print(f"  Euclidean to nearest anchor:  median={np.median(euc):.3f}m  "
          f"p90={np.percentile(euc,90):.3f}m  max={euc.max():.3f}m")

    # Breakdown by D threshold
    for thr in [0.5, 1.0, 2.0, 5.0]:
        n = (D < thr).sum()
        print(f"    D < {thr:.1f}: {100*n/len(D):.1f}%")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exps", nargs="*", default=None,
                        help="Experiment prefixes (e.g. exp08 exp19). Default: exp08 + latest exp19.")
    args = parser.parse_args()

    print(f"Loading anchors from {ANCHOR_PATH.name}...")
    anchors = np.load(ANCHOR_PATH).astype(np.float32)
    print(f"  Anchors: {len(anchors):,}")
    print(f"Building ellipsoid params (kNN k={KNN_K})...")
    tau_n, tau_t, frames = build_ellipsoid_params(anchors)
    print(f"  tau_n: median={np.median(tau_n):.3f}m  tau_t: median={np.median(tau_t):.3f}m")

    if args.exps:
        prefixes = args.exps
    else:
        prefixes = ["exp08", "exp19"]

    for prefix in prefixes:
        matches = sorted(RESULTS_DIR.glob(f"{prefix}_*/"), key=lambda p: p.name)
        matches = [m for m in matches if m.is_dir()]
        if not matches:
            print(f"\nNo directory found for prefix: {prefix}")
            continue
        exp_dir = matches[-1]
        analyze(exp_dir, anchors, tau_n, tau_t, frames)


if __name__ == "__main__":
    main()
