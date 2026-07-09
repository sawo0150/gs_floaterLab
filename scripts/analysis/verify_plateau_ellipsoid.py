import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from sklearn.linear_model import HuberRegressor
from sklearn.neighbors import NearestNeighbors

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data")
BATCH_DIR = DATA_DIR / "rgb_3dgs_openmavis_keyframes_301_1253"
PTS_TXT = BATCH_DIR / "sparse/0/points3D.txt"
IMG_TXT = BATCH_DIR / "sparse/0/images.txt"
CAM_TXT = BATCH_DIR / "sparse/0/cameras.txt"
MAP_PTS_JSONL = Path(
    "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/results/runs"
    "/customdata_fisheye624_v2_30000"
    "/aria_0416_data_0416_301_1253_0416_301_1253_stereo_fisheye624_v2"
    "/orb_export/map_points.jsonl"
)
DEPTH_MAPS_DIR = DATA_DIR / "depth_maps"
OUT_PDF = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/plateau_ellipsoid_verification_report.pdf")
os.makedirs(OUT_PDF.parent, exist_ok=True)

# ── Hyperparameters ──────────────────────────────────────────────────────────────
KNN_K = 5
ALPHA_N = 0.4
ALPHA_T = 0.9
TAU_MIN = 0.03
TAU_N_MAX = 0.30
TAU_T_MAX = 0.60
KNN_ISO_MULT = 3.0
VOXEL_SIZE = 0.30  # 30cm voxel size
STRIDE = 16       # 16px scanning stride
MIN_HITS = 2       # multi-view verification hits
D_TARGET = 0.50    # Poisson-disk spacing constraint (50cm)

# ── Rotation conversion ────────────────────────────────────────────────────────
def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])

def check_distance_constraint(pos, G_occ, voxel_size, d_target):
    key = tuple(np.floor(pos / voxel_size).astype(int))
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                neighbor_key = (key[0] + dx, key[1] + dy, key[2] + dz)
                if neighbor_key in G_occ:
                    other_pos = G_occ[neighbor_key]
                    dist = np.linalg.norm(pos - other_pos)
                    if dist < d_target:
                        return False
    return True

# ── Colmap Loaders ─────────────────────────────────────────────────────────────
def load_colmap_cameras(cameras_txt_path):
    cameras = {}
    with open(cameras_txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cid = int(parts[0])
            model = parts[1]
            w = int(parts[2])
            h = int(parts[3])
            params = [float(p) for p in parts[4:]]
            cameras[cid] = {
                "model": model,
                "width": w,
                "height": h,
                "params": params
            }
    return cameras

def load_colmap_images(images_txt_path):
    images = {}
    with open(images_txt_path, "r") as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        parts = line.split()
        image_id = int(parts[0])
        qvec = np.array([float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])
        tvec = np.array([float(parts[5]), float(parts[6]), float(parts[7])])
        camera_id = int(parts[8])
        image_name = parts[9]
        
        line2 = lines[i+1].strip()
        parts2 = line2.split()
        points2d = []
        point3d_ids = []
        for j in range(0, len(parts2), 3):
            u = float(parts2[j])
            v = float(parts2[j+1])
            pid = int(parts2[j+2])
            points2d.append([u, v])
            point3d_ids.append(pid)
            
        images[image_id] = {
            "qvec": qvec,
            "tvec": tvec,
            "camera_id": camera_id,
            "name": image_name,
            "points2d": np.array(points2d, dtype=np.float32).reshape(-1, 2),
            "point3d_ids": np.array(point3d_ids, dtype=np.int32)
        }
        i += 2
    return images

def load_colmap_points3d(points3d_txt_path):
    points = {}
    with open(points3d_txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            pid = int(parts[0])
            xyz = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
            points[pid] = xyz
    return points

# ── Load and filter SLAM points (Stage 3) ──────────────────────────────────────────
def load_and_filter_slam_points():
    print("Loading and filtering SLAM points...")
    conf = {}
    if MAP_PTS_JSONL.exists():
        with open(MAP_PTS_JSONL) as f:
            for line in f:
                d = json.loads(line)
                conf[d["map_point_id"]] = d["observations"]

    pts_list, obs_list = [], []
    with open(PTS_TXT) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            pid = int(p[0])
            x, y, z = float(p[1]), float(p[2]), float(p[3])
            pts_list.append([x, y, z])
            obs_list.append(conf.get(pid, 1))

    pts = np.array(pts_list, dtype=np.float32)
    obs = np.array(obs_list, dtype=np.int32)

    cams = []
    with open(IMG_TXT) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 9: continue
            try:
                q = np.array([float(p[i]) for i in range(1, 5)])
                t = np.array([float(p[i]) for i in range(5, 8)])
            except ValueError: continue
            cams.append(-np.transpose(_qvec2rotmat(q)) @ t)
    cams = np.array(cams, dtype=np.float32)

    lo = cams.min(0) - np.maximum((cams.max(0) - cams.min(0)) * 1.0, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0) - cams.min(0)) * 1.0, [2., 2., 3.])
    valid = (
        (pts[:, 0] >= lo[0]) & (pts[:, 0] <= hi[0]) &
        (pts[:, 1] >= lo[1]) & (pts[:, 1] <= hi[1]) &
        (pts[:, 2] >= lo[2]) & (pts[:, 2] <= hi[2])
    )
    pts, obs = pts[valid], obs[valid]

    valid_obs = obs >= 3
    pts, obs = pts[valid_obs], obs[valid_obs]

    nbrs = NearestNeighbors(n_neighbors=KNN_K + 1, algorithm="ball_tree").fit(pts)
    dists, _ = nbrs.kneighbors(pts)
    knn_dist = dists[:, KNN_K]
    threshold = KNN_ISO_MULT * np.median(knn_dist)
    mask = knn_dist <= threshold
    pts_stage3 = pts[mask]
    obs_stage3 = obs[mask]
    
    return pts_stage3, obs_stage3, cams, lo, hi

# ── Scale-Shift Fitting ────────────────────────────────────────────────────────
def fit_scale_shift_quadratic_2d(u, v, z_mono, z_slam, W, H):
    N = len(z_slam)
    if N < 15:
        if N < 2:
            return None
        X = np.array(z_mono).reshape(-1, 1)
        y = np.array(z_slam)
        reg = HuberRegressor(epsilon=1.35, max_iter=1000).fit(X, y)
        s = reg.coef_[0]
        t = reg.intercept_
        return np.array([s, 0, 0, 0, 0, 0, t, 0, 0, 0, 0, 0])
    
    u_norm = (np.array(u) - W/2) / (W/2)
    v_norm = (np.array(v) - H/2) / (H/2)
    z_m = np.array(z_mono)
    z_s = np.array(z_slam)
    
    M = np.stack([
        z_m, z_m * u_norm, z_m * v_norm, z_m * (u_norm**2), z_m * (v_norm**2), z_m * u_norm * v_norm,
        np.ones_like(z_m), u_norm, v_norm, u_norm**2, v_norm**2, u_norm * v_norm
    ], axis=1)
    
    reg = HuberRegressor(epsilon=1.35, max_iter=1000).fit(M, z_s)
    return reg.coef_

def calibrate_depth_map(depth_map, coeffs, W, H):
    if coeffs is None:
        return depth_map
    
    uu, vv = np.meshgrid(np.arange(W), np.arange(H))
    u_norm = (uu - W/2) / (W/2)
    v_norm = (vv - H/2) / (H/2)
    
    s_0, s_1, s_2, s_3, s_4, s_5, t_0, t_1, t_2, t_3, t_4, t_5 = coeffs
    
    scale_field = s_0 + s_1 * u_norm + s_2 * v_norm + s_3 * (u_norm**2) + s_4 * (v_norm**2) + s_5 * u_norm * v_norm
    shift_field = t_0 + t_1 * u_norm + t_2 * v_norm + t_3 * (u_norm**2) + t_4 * (v_norm**2) + t_5 * u_norm * v_norm
    
    calibrated_depth = scale_field * depth_map + shift_field
    return np.maximum(calibrated_depth, 0.1)

# ── Anisotropic PCA Normal Estimation ──────────────────────────────────────────
def compute_aniso_properties(pts, k=5):
    N = len(pts)
    nbrs = NearestNeighbors(n_neighbors=k+1, algorithm="ball_tree").fit(pts)
    dists, inds = nbrs.kneighbors(pts)

    h_j = dists[:, k].astype(np.float32)
    frames = np.zeros((N, 3, 3), dtype=np.float32)
    planarity = np.zeros(N, dtype=np.float32)

    for i in range(N):
        neigh = pts[inds[i, 1:]]
        centroid = neigh.mean(0)
        X = neigh - centroid
        cov = (X.T @ X) / max(k - 1, 1)

        eigvals, eigvecs = np.linalg.eigh(cov)
        u_n  = eigvecs[:, 0]
        u_t1 = eigvecs[:, 1]
        u_t2 = eigvecs[:, 2]

        frames[i] = np.stack([u_t1, u_t2, u_n], axis=1)

        lam = eigvals.clip(0)
        denom = lam[2] if lam[2] > 1e-9 else 1e-9
        planarity[i] = float((lam[1] - lam[0]) / denom)

    tau_n = np.clip(ALPHA_N * h_j, TAU_MIN, TAU_N_MAX)
    tau_t = np.clip(ALPHA_T * h_j, TAU_MIN, TAU_T_MAX)

    return frames, h_j, planarity, tau_n, tau_t

# ── Anisotropic Coverage Calculation ───────────────────────────────────────────
def calculate_aniso_coverage(anchor_pts, frames, tau_n, tau_t, z_lo, z_hi, filt_lo, filt_hi, nx=60, ny=60, chunk=64):
    mask = (anchor_pts[:, 2] >= z_lo) & (anchor_pts[:, 2] < z_hi)
    b_pts = anchor_pts[mask].copy()
    if len(b_pts) == 0:
        return 0.0
    
    b_fr = frames[mask]
    b_tn = tau_n[mask]
    b_tt = tau_t[mask]
    
    xmin, xmax = filt_lo[0], filt_hi[0]
    ymin, ymax = filt_lo[1], filt_hi[1]
    z_mid = 0.5 * (z_lo + z_hi)
    
    xg = np.linspace(xmin, xmax, nx)
    yg = np.linspace(ymin, ymax, ny)
    XX, YY = np.meshgrid(xg, yg)
    Zg  = np.full(XX.size, z_mid, dtype=np.float32)
    grid_3d = np.stack([XX.ravel().astype(np.float32), YY.ravel().astype(np.float32), Zg], axis=1)
    N_grid = len(grid_3d)
    M = len(b_pts)
    
    covered = np.zeros(N_grid, dtype=bool)
    
    for start in range(0, M, chunk):
        end = min(start + chunk, M)
        sub_pts = b_pts[start:end].copy()
        sub_pts[:, 2] = z_mid
        sub_fr = b_fr[start:end]
        sub_tn = b_tn[start:end]
        sub_tt = b_tt[start:end]
        
        delta = grid_3d[np.newaxis] - sub_pts[:, np.newaxis]  # (C, N_grid, 3)
        c_coord = np.einsum('cjk,cnj->cnk', sub_fr, delta)   # (C, N_grid, 3)
        
        d2 = ((c_coord[:,:,0] / sub_tt[:,np.newaxis])**2 +
              (c_coord[:,:,1] / sub_tt[:,np.newaxis])**2 +
              (c_coord[:,:,2] / sub_tn[:,np.newaxis])**2)     # (C, N_grid)
              
        covered |= (d2 <= 1.0).any(axis=0)
        
    return float(covered.mean()) * 100.0

def main():
    cameras = load_colmap_cameras(CAM_TXT)
    images = load_colmap_images(IMG_TXT)
    points3d = load_colmap_points3d(PTS_TXT)
    
    pts_slam, obs_slam, cams, filt_lo, filt_hi = load_and_filter_slam_points()
    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), 9)
    
    results = {}
    
    for model_name in ["depth_anything_v2", "depth_pro", "metric3d"]:
        print(f"\n================= Processing model (Ellipsoid): {model_name} =================")
        depth_dir = DEPTH_MAPS_DIR / model_name
        
        calibrated_depthmaps = {}
        for image_id, img_data in images.items():
            img_stem = os.path.splitext(img_data["name"])[0]
            npy_path = depth_dir / f"{img_stem}.npy"
            if not npy_path.exists(): continue
                
            depth_mono = np.load(npy_path)
            cam_info = cameras[img_data["camera_id"]]
            W, H = cam_info["width"], cam_info["height"]
            
            R = _qvec2rotmat(img_data["qvec"])
            t = img_data["tvec"]
            
            visible_pts_slam_z = []
            visible_pts_mono_z = []
            visible_pts_u = []
            visible_pts_v = []
            
            for u, v, pid in zip(img_data["points2d"][:, 0], img_data["points2d"][:, 1], img_data["point3d_ids"]):
                if pid == -1 or pid not in points3d: continue
                xyz_world = points3d[pid]
                xyz_cam = R @ xyz_world + t
                z_slam = xyz_cam[2]
                
                u_idx, v_idx = int(np.round(u)), int(np.round(v))
                if 0 <= u_idx < W and 0 <= v_idx < H:
                    z_mono = depth_mono[v_idx, u_idx]
                    if z_mono > 0:
                        visible_pts_slam_z.append(z_slam)
                        visible_pts_mono_z.append(z_mono)
                        visible_pts_u.append(u)
                        visible_pts_v.append(v)
            
            coeffs = fit_scale_shift_quadratic_2d(
                visible_pts_u, visible_pts_v, visible_pts_mono_z, visible_pts_slam_z, W, H
            )
            calibrated_depthmaps[image_id] = calibrate_depth_map(depth_mono, coeffs, W, H)
            
        # Voxel Seeding
        G_occ = {}
        for pt in pts_slam:
            key = tuple(np.floor(pt / VOXEL_SIZE).astype(int))
            if key not in G_occ: G_occ[key] = pt
                
        G_cand = {}
        virtual_points = []
        
        for image_id, img_data in images.items():
            if image_id not in calibrated_depthmaps: continue
            depth_calib = calibrated_depthmaps[image_id]
            cam_info = cameras[img_data["camera_id"]]
            W, H = cam_info["width"], cam_info["height"]
            fx, fy, cx, cy = cam_info["params"][0:4]
            R = _qvec2rotmat(img_data["qvec"])
            t = img_data["tvec"]
            
            for v in range(0, H, STRIDE):
                for u in range(0, W, STRIDE):
                    z = depth_calib[v, u]
                    if z <= 0.1 or z > 15.0: continue
                    x_cam = np.array([(u - cx) / fx * z, (v - cy) / fy * z, z])
                    x_world = np.transpose(R) @ (x_cam - t)
                    
                    if not (filt_lo[0] <= x_world[0] <= filt_hi[0] and
                            filt_lo[1] <= x_world[1] <= filt_hi[1] and
                            filt_lo[2] <= x_world[2] <= filt_hi[2]):
                        continue
                        
                    key = tuple(np.floor(x_world / VOXEL_SIZE).astype(int))
                    if key in G_occ: continue
                        
                    if key not in G_cand:
                        G_cand[key] = {"sum_coords": x_world, "hits": 1, "frames": {image_id}}
                    else:
                        if image_id not in G_cand[key]["frames"]:
                            G_cand[key]["sum_coords"] += x_world
                            G_cand[key]["hits"] += 1
                            G_cand[key]["frames"].add(image_id)
                            
                    if G_cand[key]["hits"] >= MIN_HITS:
                        mean_pos = G_cand[key]["sum_coords"] / G_cand[key]["hits"]
                        if check_distance_constraint(mean_pos, G_occ, VOXEL_SIZE, D_TARGET):
                            G_occ[key] = mean_pos
                            virtual_points.append(mean_pos)
                        del G_cand[key]
                        
        if len(virtual_points) > 0:
            pts_virtual = np.array(virtual_points, dtype=np.float32)
            pts_all = np.vstack([pts_slam, pts_virtual])
        else:
            pts_virtual = np.zeros((0, 3), dtype=np.float32)
            pts_all = pts_slam.copy()
            
        n_virtual = len(pts_virtual)
        
        # PCA normal & anisotropic scale calculation
        print("Computing anisotropic (ellipsoidal) properties...")
        frames, h_j, planarity, tau_n, tau_t = compute_aniso_properties(pts_all, k=KNN_K)
        
        # Calculate coverage layer-by-layer
        print("Evaluating layer anisotropic coverages...")
        coverages = []
        for i in range(8):
            z_lo, z_hi = z_edges[i], z_edges[i+1]
            cov = calculate_aniso_coverage(pts_all, frames, tau_n, tau_t, z_lo, z_hi, filt_lo, filt_hi)
            coverages.append(cov)
            print(f"  Layer {i+1} anisotropic coverage: {cov:.2f}%")
            
        results[model_name] = {
            "pts_all": pts_all,
            "pts_virtual": pts_all[len(pts_slam):],
            "coverages": coverages,
            "n_virtual": n_virtual
        }

    # Evaluate baseline SLAM with ellipsoidal coverage
    print("\nEvaluating baseline SLAM anisotropic coverages...")
    frames_slam, _, _, tau_n_slam, tau_t_slam = compute_aniso_properties(pts_slam, k=KNN_K)
    baseline_coverages = []
    for i in range(8):
        cov = calculate_aniso_coverage(pts_slam, frames_slam, tau_n_slam, tau_t_slam, z_edges[i], z_edges[i+1], filt_lo, filt_hi)
        baseline_coverages.append(cov)

    # ══════════════════════════════════════════════════════════════════════════════
    # Generate Report PDF
    # ══════════════════════════════════════════════════════════════════════════════
    print(f"\nGenerating PDF report at {OUT_PDF}...")
    with PdfPages(OUT_PDF) as pdf:
        fig, ax = plt.subplots(figsize=(12, 8), facecolor="white")
        ax.axis("off")
        ax.text(0.5, 0.95, "3D Plateau Anisotropic Ellipsoidal Coverage Analysis", ha="center", fontsize=18, fontweight="bold")
        
        # Count table
        table_data = [
            ["Model / Metric", "Original SLAM Pts", "Spawned Virtual Pts", "Total Anchors"],
            ["Baseline (SLAM Only)", f"{len(pts_slam):,}", "0", f"{len(pts_slam):,}"],
            ["Depth-Anything-V2", f"{len(pts_slam):,}", f"{results['depth_anything_v2']['n_virtual']:,}", f"{len(results['depth_anything_v2']['pts_all']):,}"],
            ["Depth Pro (Apple)", f"{len(pts_slam):,}", f"{results['depth_pro']['n_virtual']:,}", f"{len(results['depth_pro']['pts_all']):,}"],
            ["Metric3D (ViT-S)", f"{len(pts_slam):,}", f"{results['metric3d']['n_virtual']:,}", f"{len(results['metric3d']['pts_all']):,}"]
        ]
        t = ax.table(cellText=table_data, loc="center", cellLoc="center", bbox=[0.05, 0.60, 0.90, 0.25])
        t.auto_set_font_size(False)
        t.set_fontsize(10)
        
        # Coverage table
        table_cov = [
            ["Layer Index", "Z Range (m)", "Baseline (SLAM)", "Depth-Anything-V2", "Depth Pro", "Metric3D"]
        ]
        for i in range(8):
            z_lo = z_edges[i]
            z_hi = z_edges[i+1]
            table_cov.append([
                f"Layer {i+1}",
                f"[{z_lo:.2f}, {z_hi:.2f})",
                f"{baseline_coverages[i]:.1f}%",
                f"{results['depth_anything_v2']['coverages'][i]:.1f}%",
                f"{results['depth_pro']['coverages'][i]:.1f}%",
                f"{results['metric3d']['coverages'][i]:.1f}%"
            ])
        t2 = ax.table(cellText=table_cov, loc="center", cellLoc="center", bbox=[0.05, 0.05, 0.90, 0.45])
        t2.auto_set_font_size(False)
        t2.set_fontsize(9)
        
        pdf.savefig(fig)
        plt.close(fig)

    print("Anisotropic Ellipsoidal Verification report generated successfully!")

if __name__ == '__main__':
    main()
