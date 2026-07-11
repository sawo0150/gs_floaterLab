#!/usr/bin/env python3
"""
analyze_floater_lineage_grad.py
Analyzes the saved PLY file with lineage and decoupled gradient history to uncover 
how visible floaters (Pop 2) originate, get densified, and behave under RGB vs Plateau gradients.
"""
import numpy as np
from pathlib import Path
from plyfile import PlyData
import json
import os

# Paths and Configs
DATASET = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full")
IMG_TXT = DATASET / "sparse/0/images.txt"

IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 511.5, 511.5

VOXEL_SIZE = 0.15
PIXEL_STEP = 48          # 441 rays/cam
MAX_DEPTH = 15.0
DEPTH_STEP = 0.15

def qvec2rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z,     2*x*z + 2*w*y],
        [2*x*y + 2*w*z,     1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
        [2*x*z - 2*w*y,     2*y*z + 2*w*x,     1 - 2*x*x - 2*y*y],
    ])

def load_cameras():
    centers, rotmats = [], []
    if not IMG_TXT.exists():
        raise FileNotFoundError(f"Images description not found at {IMG_TXT}")
    for line in open(IMG_TXT):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) < 9:
            continue
        q = np.array([float(x) for x in p[1:5]])
        t = np.array([float(x) for x in p[5:8]])
        R_wc = qvec2rotmat(q).T   # cam->world rotation
        C = -R_wc @ t
        centers.append(C)
        rotmats.append(R_wc)
    return np.array(centers, dtype=np.float32), np.array(rotmats, dtype=np.float32)

def build_ray_dirs_cam(step):
    us = np.arange(step // 2, IMG_W, step, dtype=np.float32)
    vs = np.arange(step // 2, IMG_H, step, dtype=np.float32)
    uu, vv = np.meshgrid(us, vs)
    dx = (uu.ravel() - CX) / FX
    dy = (vv.ravel() - CY) / FY
    dz = np.ones_like(dx)
    dirs = np.stack([dx, dy, dz], axis=1)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    return dirs.astype(np.float32)

def camera_bound(centers):
    lo = centers.min(0) - np.maximum((centers.max(0) - centers.min(0)) * 1.0, [2., 2., 3.])
    hi = centers.max(0) + np.maximum((centers.max(0) - centers.min(0)) * 1.0, [2., 2., 3.])
    return lo, hi

def analyze_run(ply_path, visited, lo, dims):
    print(f"\n[Load] Reading PLY from {ply_path}...")
    if not ply_path.exists():
        print(f"Error: {ply_path} does not exist.")
        return None
    
    ply_data = PlyData.read(str(ply_path))
    v = ply_data["vertex"]
    
    # Extract standard geometry and opacity
    xyz = np.stack([np.array(v["x"]), np.array(v["y"]), np.array(v["z"])], axis=1).astype(np.float32)
    opacity = 1.0 / (1.0 + np.exp(-np.array(v["opacity"], dtype=np.float64)))
    
    # Calculate ray-visited overlap
    idx = np.floor((xyz - lo) / VOXEL_SIZE).astype(np.int64)
    inb = ((idx >= 0) & (idx < dims[None, :])).all(axis=1)
    zero_ray = np.zeros(len(xyz), dtype=bool)
    zero_ray[inb] = ~visited[idx[inb, 0], idx[inb, 1], idx[inb, 2]]
    zero_ray[~inb] = True   # Outside grid is unseen
    
    # Extract tracking attributes (if present)
    prop_names = [p.name for p in v.properties]
    has_tracking = 'ancestor_idx' in prop_names
    
    if not has_tracking:
        print("Warning: PLY file does not contain lineage tracking attributes.")
        return None
        
    ancestor_idx = np.array(v["ancestor_idx"]).astype(np.int64)
    birth_step = np.array(v["birth_step"]).astype(np.int32)
    generation = np.array(v["generation"]).astype(np.int32)
    num_splits = np.array(v["num_splits"]).astype(np.int32)
    num_clones = np.array(v["num_clones"]).astype(np.int32)
    accum_visibility = np.array(v["accum_visibility"]).astype(np.int32)
    accum_rgb_grad = np.array(v["accum_rgb_grad"]).astype(np.float32)
    accum_plateau_grad = np.array(v["accum_plateau_grad"]).astype(np.float32)
    
    total_gaussians = len(xyz)
    
    # Filter groups
    # Group 1: Explicit Floatlers (Ray unseen & opacity > 0.5)
    floater_mask = zero_ray & (opacity > 0.5)
    # Group 2: Ground Truth Surface / Clean geometry (Ray visited & opacity > 0.5)
    surface_mask = (~zero_ray) & (opacity > 0.5)
    # Group 3: Total ray unseen
    unseen_mask = zero_ray
    
    num_floaters = int(floater_mask.sum())
    num_surface = int(surface_mask.sum())
    num_unseen = int(unseen_mask.sum())
    
    print(f"  Total Gaussians: {total_gaussians:,}")
    print(f"  Explicit Floaters (unseen & op>0.5): {num_floaters:,} ({100*num_floaters/total_gaussians:.2f}%)")
    print(f"  Surface Gaussians (seen & op>0.5): {num_surface:,} ({100*num_surface/total_gaussians:.2f}%)")
    print(f"  Total Unseen Gaussians (any opacity): {num_unseen:,} ({100*num_unseen/total_gaussians:.2f}%)")
    
    if num_floaters == 0:
        print("  No explicit floaters found to analyze.")
        return None
        
    # Analyze Lineage
    f_births = birth_step[floater_mask]
    f_ancestors = ancestor_idx[floater_mask]
    f_generations = generation[floater_mask]
    f_splits = num_splits[floater_mask]
    f_clones = num_clones[floater_mask]
    f_vis = accum_visibility[floater_mask]
    f_rgb_grad = accum_rgb_grad[floater_mask]
    f_plat_grad = accum_plateau_grad[floater_mask]
    
    s_rgb_grad = accum_rgb_grad[surface_mask]
    s_plat_grad = accum_plateau_grad[surface_mask]
    
    # Statistics dict
    stats = {
        "summary": {
            "total_gaussians": total_gaussians,
            "explicit_floaters": num_floaters,
            "surface_gaussians": num_surface,
            "unseen_gaussians": num_unseen
        },
        "floaters": {
            "birth_step": {
                "mean": float(f_births.mean()),
                "median": float(np.median(f_births)),
                "min": int(f_births.min()),
                "max": int(f_births.max()),
                "histogram_5k": list(map(int, np.histogram(f_births, bins=[0, 1000, 3000, 5000, 7000, 15000, 30000])[0]))
            },
            "generation": {
                "mean": float(f_generations.mean()),
                "median": float(np.median(f_generations)),
                "max": int(f_generations.max())
            },
            "splits": {
                "mean": float(f_splits.mean()),
                "median": float(np.median(f_splits)),
                "max": int(f_splits.max())
            },
            "clones": {
                "mean": float(f_clones.mean()),
                "median": float(np.median(f_clones)),
                "max": int(f_clones.max())
            },
            "accum_visibility": {
                "mean": float(f_vis.mean()),
                "median": float(np.median(f_vis)),
                "max": int(f_vis.max()),
                "zero_vis_count": int((f_vis == 0).sum()),
                "zero_vis_ratio": float((f_vis == 0).sum() / num_floaters)
            },
            "accum_rgb_grad": {
                "mean": float(f_rgb_grad.mean()),
                "median": float(np.median(f_rgb_grad)),
                "max": float(f_rgb_grad.max())
            },
            "accum_plateau_grad": {
                "mean": float(f_plat_grad.mean()),
                "median": float(np.median(f_plat_grad)),
                "max": float(f_plat_grad.max())
            }
        },
        "surface": {
            "accum_rgb_grad": {
                "mean": float(s_rgb_grad.mean()),
                "median": float(np.median(s_rgb_grad))
            },
            "accum_plateau_grad": {
                "mean": float(s_plat_grad.mean()),
                "median": float(np.median(s_plat_grad))
            }
        }
    }
    
    # Find top ancestors
    ancestors, counts = np.unique(f_ancestors, return_counts=True)
    sort_idx = np.argsort(-counts)
    top_ancestors = []
    for idx_rank in range(min(10, len(sort_idx))):
        top_ancestors.append({
            "ancestor_idx": int(ancestors[sort_idx[idx_rank]]),
            "count": int(counts[sort_idx[idx_rank]]),
            "ratio_of_floaters": float(counts[sort_idx[idx_rank]] / num_floaters)
        })
    stats["top_floaters_ancestors"] = top_ancestors
    
    # Print out results cleanly
    print("\n--- RESULTS ANALYSIS ---")
    print(f"Decoupled Gradient Profile:")
    print(f"  RGB Gradient: Floater Mean = {stats['floaters']['accum_rgb_grad']['mean']:.4e} vs Surface Mean = {stats['surface']['accum_rgb_grad']['mean']:.4e}")
    print(f"                Ratio (Floater / Surface) = {stats['floaters']['accum_rgb_grad']['mean'] / (stats['surface']['accum_rgb_grad']['mean'] + 1e-12):.4f}")
    print(f"  Plateau Gradient: Floater Mean = {stats['floaters']['accum_plateau_grad']['mean']:.4e} vs Surface Mean = {stats['surface']['accum_plateau_grad']['mean']:.4e}")
    print(f"                    Ratio (Floater / Surface) = {stats['floaters']['accum_plateau_grad']['mean'] / (stats['surface']['accum_plateau_grad']['mean'] + 1e-12):.4f}")
    print(f"Lineage & Densification Profile:")
    print(f"  Mean Generation: {stats['floaters']['generation']['mean']:.2f} (Median: {stats['floaters']['generation']['median']:.1f})")
    print(f"  Mean Splits: {stats['floaters']['splits']['mean']:.2f}, Mean Clones: {stats['floaters']['clones']['mean']:.2f}")
    print(f"  Birth Steps Histogram [0-1k, 1-3k, 3-5k, 5-7k, 7-15k, 15k-30k]: {stats['floaters']['birth_step']['histogram_5k']}")
    print(f"Visibility & Observation Profile:")
    print(f"  Total Visibility (observations): Mean = {stats['floaters']['accum_visibility']['mean']:.1f} (Median: {stats['floaters']['accum_visibility']['median']:.1f})")
    print(f"  Never-observed Floaters (visible=0): {stats['floaters']['accum_visibility']['zero_vis_count']} ({stats['floaters']['accum_visibility']['zero_vis_ratio']*100:.2f}%)")
    
    print("\nTop 5 Ancestors producing floaters:")
    for rank, ancestor in enumerate(top_ancestors[:5]):
        print(f"  Rank {rank+1}: Seed index {ancestor['ancestor_idx']} produced {ancestor['count']} floaters ({ancestor['ratio_of_floaters']*100:.1f}%)")
        
    return stats

def main():
    print("[Load] cameras to build ray-density map...")
    centers, rotmats = load_cameras()
    lo, hi = camera_bound(centers)
    dims = np.ceil((hi - lo) / VOXEL_SIZE).astype(int) + 1
    
    visited = np.zeros(tuple(dims), dtype=bool)
    ray_dirs_cam = build_ray_dirs_cam(PIXEL_STEP)
    n_ray = len(ray_dirs_cam)
    depths = np.arange(DEPTH_STEP, MAX_DEPTH + 1e-6, DEPTH_STEP, dtype=np.float32)
    n_depth = len(depths)
    
    for ci, (C, Rw) in enumerate(zip(centers, rotmats)):
        dirs_world = ray_dirs_cam @ Rw.T
        pts = C[None, None, :] + depths[None, :, None] * dirs_world[:, None, :]
        pts = pts.reshape(-1, 3)
        idx = np.floor((pts - lo) / VOXEL_SIZE).astype(np.int64)
        ok = ((idx >= 0) & (idx < dims[None, :])).all(axis=1)
        idx = idx[ok]
        visited[idx[:, 0], idx[:, 1], idx[:, 2]] = True
        
    # Set the target run path (Run exp32 with lineage diagnostic)
    run_dir = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp32_lineage_diag")
    ply_path = run_dir / "point_cloud/iteration_30000/point_cloud.ply"
    
    if not ply_path.exists():
        # Fallback to check if user specified another path
        print(f"Target diagnostic run path not found at {ply_path}.")
        print("Please run the diagnostic training first using option 1 command.")
        return
        
    stats = analyze_run(ply_path, visited, lo, dims)
    
    if stats is not None:
        out_json = run_dir / "floater_lineage_grad_stats.json"
        with open(out_json, "w") as f:
            json.dump(stats, f, indent=4)
        print(f"\n[Saved] Analysis report saved to {out_json}")

if __name__ == "__main__":
    main()
