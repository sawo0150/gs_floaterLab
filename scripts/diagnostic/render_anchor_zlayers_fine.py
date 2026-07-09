#!/usr/bin/env python3
"""Very fine Z-layer breakdown of where the anchors actually are, correlated
with (a) ray-observation coverage and (b) where ray-density pruning removed
Gaussians -- to diagnose whether a Z band that gets pruned a lot is simply
an unobserved/no-anchor region (e.g. "above the ceiling", not a visually
obvious floater) versus a genuine surface-adjacent floater band.

Page 1: 1D Z-profile (fine bins) overlaying ray-visited fraction, anchor
        point density (general + high-confidence sets), and pruned-Gaussian
        count (summed across all 8 runs) on a shared Z axis.
Pages 2+: per-Z-layer (voxel-aligned, 0.15m) XY scatter of both anchor sets
        over the ray-unvisited-fraction background, same style as the
        rayprune Z-layer PDF.
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
from plyfile import PlyData

DATASET = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full")
IMG_TXT = DATASET / "sparse/0/images.txt"

GENERAL_ANCHOR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/native_anchors_neworb_v4_20260709_204706/anchors_all_depth_pro.npy"
HIGHCONF_ANCHOR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/native_anchors_neworb_highconf_20260709_205327/anchors_all_depth_pro.npy"

RUNS = [
    "exp30_orbfull_baseline_20260709_210151",
    "exp31_orbfull_anchorinit_20260709_211736",
    "exp32_orbfull_plateau_basetau_20260709_213513",
    "exp33_orbfull_plateau_bigtau_20260709_221147",
    "exp34_orbfull_highconf_anchorinit_20260709_223856",
    "exp35_orbfull_plateau_highconf_basetau_20260709_224841",
    "exp36_orbfull_plateau_highconf_bigtau_20260709_230121",
    "exp37_orbfull_dense_confmono_init_20260709_231355",
]

FINE_BIN = 0.05   # 1D Z-profile bin size (m)


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
    ap.add_argument("rayprune_dir", type=str)
    args = ap.parse_args()
    prune_dir = Path(args.rayprune_dir)

    grid = np.load(prune_dir / "ray_grid.npz")
    visited, lo, dims, voxel_size = grid["visited"], grid["lo"], grid["dims"], float(grid["voxel_size"])
    hi = lo + dims * voxel_size
    xmin, xmax = float(lo[0]), float(hi[0])
    ymin, ymax = float(lo[1]), float(hi[1])
    zmin, zmax = float(lo[2]), float(hi[2])
    print(f"Z range: [{zmin:.2f}, {zmax:.2f}]  ({zmax-zmin:.2f}m)")

    cams = load_camera_centers()
    general = np.load(GENERAL_ANCHOR).astype(np.float32)
    highconf = np.load(HIGHCONF_ANCHOR).astype(np.float32)

    # ray-visited fraction per Z-voxel-layer (fraction of XY cells visited)
    vis_frac_by_zvoxel = visited.mean(axis=(0, 1))  # (nz,)
    z_voxel_centers = lo[2] + (np.arange(dims[2]) + 0.5) * voxel_size

    # pruned Gaussians, all runs combined -- both raw removed-Z and the
    # TOTAL-Z (from the original point cloud) so we can compute a
    # normalized prune RATE per Z-bin, not just raw removed counts (a Z
    # band with more total Gaussians will have more removed in absolute
    # terms even if the underlying prune fraction there is unremarkable).
    exp_dir = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments")
    removed_all_z = []
    total_all_z = []
    for name in RUNS:
        rp = prune_dir / name / "removed.ply"
        tp = exp_dir / name / "point_cloud/iteration_30000/point_cloud.ply"
        if not rp.exists() or not tp.exists():
            continue
        removed_all_z.append(np.array(PlyData.read(str(rp))["vertex"]["z"], dtype=np.float64))
        total_all_z.append(np.array(PlyData.read(str(tp))["vertex"]["z"], dtype=np.float64))
    removed_all_z = np.concatenate(removed_all_z)
    total_all_z = np.concatenate(total_all_z)

    fine_edges = np.arange(zmin, zmax + FINE_BIN, FINE_BIN)
    fine_centers = (fine_edges[:-1] + fine_edges[1:]) / 2

    pdf_path = prune_dir / "anchor_zlayers_fine.pdf"
    with PdfPages(pdf_path) as pdf:
        # ---- Page 1: 1D correlated Z-profile ----
        fig, axes = plt.subplots(4, 1, figsize=(13, 14), sharex=True, facecolor="white")
        fig.suptitle("Z-profile 상관관계: ray 관측 · anchor 밀도 · 잘려나간(pruned) Gaussian",
                     fontsize=15, fontweight="bold", y=0.995)

        ax = axes[0]
        ax.plot(z_voxel_centers, 1 - vis_frac_by_zvoxel, color="#374151", lw=1.6)
        ax.fill_between(z_voxel_centers, 1 - vis_frac_by_zvoxel, color="#374151", alpha=0.15)
        ax.set_ylabel("ray 미관측 비율\n(XY 전체 중)", fontsize=9)
        ax.set_title("① Z 레이어별 '카메라가 한 번도 안 본 비율' — 높을수록 관측 공백", fontsize=10, color="#444")
        ax.grid(alpha=0.2)

        ax = axes[1]
        gc, _ = np.histogram(general[:, 2], bins=fine_edges)
        hc, _ = np.histogram(highconf[:, 2], bins=fine_edges)
        ax.plot(fine_centers, gc, color="#2563EB", lw=1.3, label=f"일반 anchor (obs≥3, {len(general):,})")
        ax.plot(fine_centers, hc, color="#DC2626", lw=1.3, label=f"고confidence anchor (obs≥10&fr≥0.5, {len(highconf):,})")
        ax.set_ylabel(f"anchor 개수\n(bin={FINE_BIN}m)", fontsize=9)
        ax.set_title("② Z 레이어별 anchor 밀도 — 0이면 그 높이에 당기는 힘이 아예 없음", fontsize=10, color="#444")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=0.2)

        ax = axes[2]
        rc, _ = np.histogram(removed_all_z, bins=fine_edges)
        ax.bar(fine_centers, rc, width=FINE_BIN * 0.9, color="#EA580C", alpha=0.85)
        ax.set_ylabel(f"제거된 Gaussian 수\n(8개 run 합산, bin={FINE_BIN}m)", fontsize=9)
        ax.set_title("③ Z 레이어별 ray-density pruning으로 잘려나간 Gaussian 수 (원시 개수, 8개 run 합산)", fontsize=10, color="#444")
        ax.grid(alpha=0.2)

        ax = axes[3]
        tc, _ = np.histogram(total_all_z, bins=fine_edges)
        rate = np.divide(rc, tc, out=np.zeros_like(rc, dtype=float), where=tc > 0) * 100
        ax.bar(fine_centers, rate, width=FINE_BIN * 0.9, color="#B91C1C", alpha=0.9)
        overall_rate = 100 * removed_all_z.size / total_all_z.size
        ax.axhline(overall_rate, color="#374151", ls="--", lw=1, alpha=0.7)
        ax.text(zmax - 0.1, overall_rate, f" scene 평균 {overall_rate:.2f}%", fontsize=7.5,
                color="#374151", va="bottom", ha="right")
        ax.set_ylabel(f"prune 비율(%)\n(제거/전체, bin={FINE_BIN}m)", fontsize=9)
        ax.set_xlabel("Z (m)", fontsize=10)
        ax.set_title("④ Z 레이어별 prune 비율 (③을 그 구간의 전체 Gaussian 수로 정규화 — 진짜 '이 높이가 위험한가' 지표)",
                     fontsize=10, color="#444")
        ax.grid(alpha=0.2)

        for ax in axes:
            ax.set_xlim(zmin, zmax)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
        print("[page 1] 1D correlated profile done")

        # ---- Pages 2+: per-Z-voxel-layer (0.15m, voxel-aligned) anchor XY maps ----
        unvisited = ~visited
        n_layers = int(dims[2])
        per_page = 8
        n_pages = (n_layers + per_page - 1) // per_page

        for pg in range(n_pages):
            fig = plt.figure(figsize=(15, 8.5), facecolor="white")
            fig.suptitle(f"Anchor 위치 — 세밀 Z-layer ({voxel_size}m/layer)  [{pg+1}/{n_pages}]",
                        fontsize=13, fontweight="bold", y=0.98)
            for k in range(per_page):
                li = pg * per_page + k
                if li >= n_layers:
                    break
                z_lo = lo[2] + li * voxel_size
                z_hi = z_lo + voxel_size
                bg = unvisited[:, :, li].T.astype(float)

                ax = fig.add_subplot(2, 4, k + 1)
                ax.set_facecolor("#0d0d0d")
                ax.imshow(bg, origin="lower", extent=[xmin, xmax, ymin, ymax],
                           cmap="Greys", vmin=0, vmax=1, aspect="equal", alpha=0.85)
                ax.plot(cams[:, 0], cams[:, 1], color="#D97706", lw=0.7, alpha=0.5, zorder=3)

                mg = (general[:, 2] >= z_lo) & (general[:, 2] < z_hi)
                mh = (highconf[:, 2] >= z_lo) & (highconf[:, 2] < z_hi)
                if mg.any():
                    ax.scatter(general[mg, 0], general[mg, 1], c="#3B82F6", s=10, alpha=0.8,
                               linewidths=0, zorder=4, label="일반anchor")
                if mh.any():
                    ax.scatter(highconf[mh, 0], highconf[mh, 1], c="#EF4444", s=16, alpha=0.9,
                               linewidths=0.3, edgecolors="white", zorder=5, label="고conf anchor")

                ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
                ax.set_title(f"Z[{z_lo:.2f},{z_hi:.2f})  일반={int(mg.sum())} 고conf={int(mh.sum())}",
                            fontsize=8.5, color="#333")
                ax.tick_params(labelsize=6)
                if k == 0:
                    ax.legend(fontsize=6, loc="upper right", framealpha=0.7)

            pdf.savefig(fig, dpi=140, bbox_inches="tight")
            plt.close(fig)
            print(f"  [page {pg+2}] layers {pg*per_page}-{min((pg+1)*per_page,n_layers)-1} done")

    print(f"\n[done] -> {pdf_path}")


if __name__ == "__main__":
    main()
