#!/usr/bin/env python3
"""
auto_prune_floaters.py
Automatically prunes explicit floaters (ray-unseen & opacity > threshold) from 3DGS point cloud
and outputs a cleaned PLY file preserving all other attributes (including lineage/gradients).
"""
import numpy as np
from pathlib import Path
from plyfile import PlyData, PlyElement
import argparse

# Cameras & Voxel Configs
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

def load_cameras(dataset_path):
    img_txt = Path(dataset_path) / "sparse/0/images.txt"
    centers, rotmats = [], []
    if not img_txt.exists():
        raise FileNotFoundError(f"Images description not found at {img_txt}")
    for line in open(img_txt):
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

def main():
    parser = argparse.ArgumentParser(description="Auto prune explicit floaters from PLY.")
    parser.add_argument("--orig", type=str, required=True, 
                        help="Path to original point_cloud.ply")
    parser.add_argument("--out", type=str, required=True, 
                        help="Path to save the auto-cleaned point_cloud.ply")
    parser.add_argument("--dataset", type=str, default="/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full",
                        help="Path to dataset containing images.txt")
    parser.add_argument("--opacity_threshold", type=float, default=0.5,
                        help="Opacity threshold to classify as explicit floater (default: 0.5)")
    args = parser.parse_args()

    orig_path = Path(args.orig)
    out_path = Path(args.out)
    
    if not orig_path.exists():
        print(f"Error: Original PLY path not found at {orig_path}")
        return

    print("[1/3] Building Ray-density map from dataset cameras...")
    centers, rotmats = load_cameras(args.dataset)
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
        
    print(f"      Visited voxels: {int(visited.sum()):,} / {dims.prod():,}")

    print("[2/3] Loading original PLY and mapping points to voxel grid...")
    ply_data = PlyData.read(str(orig_path))
    v = ply_data["vertex"]
    
    xyz = np.stack([np.array(v["x"]), np.array(v["y"]), np.array(v["z"])], axis=1).astype(np.float32)
    opacity = 1.0 / (1.0 + np.exp(-np.array(v["opacity"], dtype=np.float64)))
    
    # Check visited vs unseen
    idx = np.floor((xyz - lo) / VOXEL_SIZE).astype(np.int64)
    inb = ((idx >= 0) & (idx < dims[None, :])).all(axis=1)
    zero_ray = np.zeros(len(xyz), dtype=bool)
    zero_ray[inb] = ~visited[idx[inb, 0], idx[inb, 1], idx[inb, 2]]
    zero_ray[~inb] = True   # Outside grid is unseen
    
    # Classify floaters to prune
    floater_mask = zero_ray & (opacity > args.opacity_threshold)
    num_floaters = int(floater_mask.sum())
    
    print(f"      Original Gaussians: {len(xyz):,}")
    print(f"      Detected Floaters to prune: {num_floaters:,} ({100*num_floaters/len(xyz):.3f}%)")
    
    if num_floaters == 0:
        print("      No floaters detected with current threshold. Copying original file directly...")
        ply_data.write(str(out_path))
        return

    print("[3/3] Slicing PLY and saving cleaned point cloud...")
    # Slicing the structural array directly keeps the exact attributes and header in tact
    # valid_points are those that are NOT labeled as floaters
    valid_points_mask = ~floater_mask
    
    # Extract only valid vertices
    clean_vertices = v.data[valid_points_mask]
    
    # Create new PlyData structure
    new_el = PlyElement.describe(clean_vertices, 'vertex')
    new_ply_data = PlyData([new_el], text=ply_data.text, byte_order=ply_data.byte_order)
    
    # Write to file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    new_ply_data.write(str(out_path))
    print(f"[Done] Cleaned PLY saved successfully to {out_path} ({len(clean_vertices):,} Gaussians remaining)")

if __name__ == "__main__":
    main()
