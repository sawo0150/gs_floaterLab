#!/usr/bin/env python3
"""Z-layer PDF of where the ray-density-pruned ("removed") Gaussians are
concentrated, for each run in a rayprune_<ts>/ output directory.

Background per Z-slab: fraction of that slab's voxel column never visited
by any camera ray (grayscale -- darker = more of that column is unseen).
Foreground: scatter of the removed Gaussians that fall in that slab,
colored by opacity (near-zero opacity = harmless residue, high opacity =
a real visible floater).
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
for _f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    fm.fontManager.addfont(_f)
matplotlib.rcParams["font.family"] = "Noto Sans CJK JP"
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
from plyfile import PlyData

DATASET = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full")
IMG_TXT = DATASET / "sparse/0/images.txt"

RUNS = [
    ("exp30_orbfull_baseline_20260709_210151", "exp30 baseline"),
    ("exp31_orbfull_anchorinit_20260709_211736", "exp31 general-anchor init"),
    ("exp32_orbfull_plateau_basetau_20260709_213513", "exp32 plateau base-tau"),
    ("exp33_orbfull_plateau_bigtau_20260709_221147", "exp33 plateau enlarged-tau"),
    ("exp34_orbfull_highconf_anchorinit_20260709_223856", "exp34 highconf-anchor init"),
    ("exp35_orbfull_plateau_highconf_basetau_20260709_224841", "exp35 highconf plateau base-tau"),
    ("exp36_orbfull_plateau_highconf_bigtau_20260709_230121", "exp36 highconf plateau enlarged-tau"),
    ("exp37_orbfull_dense_confmono_init_20260709_231355", "exp37 dense confmono init"),
]

N_Z_LAYERS = 8


def qvec2rotmat(q):
    w, x, y, z = q
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])


def load_camera_centers():
    centers = []
    for line in open(IMG_TXT):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) < 9:
            continue
        q = np.array([float(x) for x in p[1:5]])
        t = np.array([float(x) for x in p[5:8]])
        centers.append(-qvec2rotmat(q).T @ t)
    return np.array(centers, dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rayprune_dir", type=str, help="results/diagnostic/rayprune_<ts>/ directory")
    args = ap.parse_args()

    prune_dir = Path(args.rayprune_dir)
    grid = np.load(prune_dir / "ray_grid.npz")
    visited, lo, dims, voxel_size = grid["visited"], grid["lo"], grid["dims"], float(grid["voxel_size"])
    hi = lo + dims * voxel_size
    print(f"grid dims={tuple(dims)} lo={lo.round(2)} hi={hi.round(2)}")

    cams = load_camera_centers()
    xmin, xmax = float(lo[0]), float(hi[0])
    ymin, ymax = float(lo[1]), float(hi[1])
    z_edges = np.linspace(float(lo[2]), float(hi[2]), N_Z_LAYERS + 1)
    z_layer_idx = np.clip(((z_edges[:-1] + z_edges[1:]) / 2 - lo[2]) / voxel_size, 0, dims[2] - 1).astype(int)
    # voxel index ranges per layer along Z
    z_vox_edges = np.linspace(0, dims[2], N_Z_LAYERS + 1).astype(int)

    # background: fraction of each Z-slab's voxel column that's unvisited
    unvisited = ~visited  # (nx, ny, nz)
    bg_layers = []
    for li in range(N_Z_LAYERS):
        z0, z1 = z_vox_edges[li], z_vox_edges[li + 1]
        slab = unvisited[:, :, z0:z1]  # (nx, ny, dz)
        frac = slab.mean(axis=2)       # (nx, ny) fraction unvisited
        bg_layers.append(frac.T)       # transpose so [y, x] for imshow origin='lower'

    pdf_path = prune_dir / "rayprune_zlayers.pdf"
    with PdfPages(pdf_path) as pdf:
        # cover
        fig = plt.figure(figsize=(13, 9.5), facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
        ax.text(0.5, 0.75, "Ray-Density Pruning — Z-Layer 위치 분석", ha="center", fontsize=22,
                 fontweight="bold", color="#1A202C")
        ax.text(0.5, 0.67, "제거된(unseen-voxel) Gaussian이 Z 레이어별로 어디에 몰려있는가",
                 ha="center", fontsize=13, color="#555")
        ax.text(0.5, 0.55,
                 "배경(회색 농도) = 그 Z-슬랩 voxel 컬럼 중 ray가 한 번도 안 지나간 비율\n"
                 "점(색) = 제거된 Gaussian, opacity로 색칠 (진할수록 실제로 보이는 floater)",
                 ha="center", fontsize=10.5, color="#666")
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        for name, label in RUNS:
            run_dir = prune_dir / name
            removed_ply = run_dir / "removed.ply"
            if not removed_ply.exists():
                continue
            v = PlyData.read(str(removed_ply))["vertex"]
            xyz = np.stack([np.array(v["x"]), np.array(v["y"]), np.array(v["z"])], axis=1)
            opacity = 1.0 / (1.0 + np.exp(-np.array(v["opacity"], dtype=np.float64)))

            fig = plt.figure(figsize=(15, 8.5), facecolor="white")
            fig.suptitle(f"{label}  —  removed={len(xyz)}  (op>0.5: {int((opacity>0.5).sum())})",
                         fontsize=14, fontweight="bold", color="#1A202C", y=0.98)

            for li in range(N_Z_LAYERS):
                ax = fig.add_subplot(2, 4, li + 1)
                ax.set_facecolor("#0d0d0d")
                ax.imshow(bg_layers[li], origin="lower", extent=[xmin, xmax, ymin, ymax],
                           cmap="Greys", vmin=0, vmax=1, aspect="equal", alpha=0.85)
                ax.plot(cams[:, 0], cams[:, 1], color="#D97706", lw=0.8, alpha=0.6, zorder=3)

                z_lo, z_hi = z_edges[li], z_edges[li + 1]
                m = (xyz[:, 2] >= z_lo) & (xyz[:, 2] < z_hi)
                if m.any():
                    sc = ax.scatter(xyz[m, 0], xyz[m, 1], c=opacity[m], cmap="YlOrRd",
                                      norm=Normalize(0, 1), s=22, edgecolors="white",
                                      linewidths=0.3, zorder=5)
                ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
                ax.set_title(f"Z[{z_lo:.2f},{z_hi:.2f})  n={int(m.sum())}", fontsize=9, color="#333")
                ax.tick_params(labelsize=6)

            pdf.savefig(fig, dpi=140, bbox_inches="tight")
            plt.close(fig)
            print(f"  {label}: {len(xyz)} removed points plotted")

    print(f"\n[done] -> {pdf_path}")


if __name__ == "__main__":
    main()
