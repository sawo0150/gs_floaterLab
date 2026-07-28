#!/usr/bin/env python3
"""exp56 Phase 9 후속 -- frustum pre-filter를 만들 가치가 있는지 먼저 확인:
exp56 최종 체크포인트(90,770 gaussians)에 대해, 실제 keyframe 궤적의 여러
지점(카메라)에서 실제로 몇 %가 render()의 visibility_filter(radii>0)로
"보인다"고 판정되는지 측정. 낮으면(예: <30%) coarse pre-filter로 유효 N을
크게 줄일 여지가 있다는 뜻 -- 구현 전에 먼저 ROI를 가늠.
"""
import sys, os
sys.path.append("/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM/vigs")
import numpy as np
import torch
from plyfile import PlyData
from scipy.spatial.transform import Rotation as R

from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.renderer import render

PLY = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp56_ax8_camcache/3dgs_before_final.ply"
RUN_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp56_ax8_camcache"


def load_gaussians(ply_path):
    p = PlyData.read(ply_path)
    v = p.elements[0]
    xyz = np.stack([np.asarray(v["x"]), np.asarray(v["y"]), np.asarray(v["z"])], axis=1)
    opacities = np.asarray(v["opacity"])[..., np.newaxis]
    features_dc = np.zeros((xyz.shape[0], 3, 1))
    features_dc[:, 0, 0] = np.asarray(v["f_dc_0"]); features_dc[:, 1, 0] = np.asarray(v["f_dc_1"]); features_dc[:, 2, 0] = np.asarray(v["f_dc_2"])
    scale_names = sorted([pr.name for pr in v.properties if pr.name.startswith("scale_")], key=lambda x: int(x.split("_")[-1]))
    scales = np.stack([np.asarray(v[n]) for n in scale_names], axis=1)
    rot_names = sorted([pr.name for pr in v.properties if pr.name.startswith("rot")], key=lambda x: int(x.split("_")[-1]))
    rots = np.stack([np.asarray(v[n]) for n in rot_names], axis=1)
    class G: pass
    g = G()
    g._xyz = torch.tensor(xyz, dtype=torch.float, device="cuda")
    g._features_dc = torch.tensor(features_dc, dtype=torch.float, device="cuda").transpose(1, 2).contiguous()
    g._features_rest = torch.zeros((g._xyz.shape[0], 0, 3), dtype=torch.float, device="cuda")
    g._opacity = torch.tensor(opacities, dtype=torch.float, device="cuda")
    g._scaling = torch.tensor(scales, dtype=torch.float, device="cuda")
    g._rotation = torch.tensor(rots, dtype=torch.float, device="cuda")
    g.max_sh_degree = 0; g.active_sh_degree = 0
    g.scaling_activation = torch.exp; g.opacity_activation = torch.sigmoid; g.rotation_activation = torch.nn.functional.normalize
    type(g).get_xyz = property(lambda self: self._xyz)
    type(g).get_scaling = property(lambda self: self.scaling_activation(self._scaling))
    type(g).get_rotation = property(lambda self: self.rotation_activation(self._rotation))
    type(g).get_opacity = property(lambda self: self.opacity_activation(self._opacity))
    type(g).get_features = property(lambda self: torch.cat((self._features_dc, self._features_rest), dim=1))
    return g


def build_camera_from_row(row, K, W=1024, H=1024):
    tx, ty, tz, qx, qy, qz, qw = row[1:8]
    T_c2w = np.eye(4)
    T_c2w[:3, :3] = R.from_quat([qx, qy, qz, qw]).as_matrix()
    T_c2w[:3, 3] = [tx, ty, tz]
    pose = torch.tensor(np.linalg.inv(T_c2w), dtype=torch.float32, device="cuda")
    fx, fy, cx, cy = float(K[0]), float(K[1]), float(K[2]), float(K[3])
    Kfull = [fx, fy, cx, cy, W, H]
    projection_matrix = getProjectionMatrix2(znear=0.01, zfar=100.0, fx=fx, fy=fy, cx=cx, cy=cy, W=W, H=H).transpose(0, 1).cuda()
    return Camera.init_from_tracking(None, None, None, pose, 0, projection_matrix, Kfull), T_c2w


if __name__ == "__main__":
    g = load_gaussians(PLY)
    N = g._xyz.shape[0]
    K = np.load(os.path.join(RUN_DIR, "intrinsics.npy"))
    traj = np.loadtxt(os.path.join(RUN_DIR, "traj_kf_beforeBA.txt"))
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")

    print(f"total gaussians N={N}")
    print(f"{'idx':>5s} {'frac_visible':>14s} {'frac_within_5m':>16s} {'frac_within_10m':>17s}")
    fracs = []
    # sample keyframes across the whole trajectory (every ~10th) for a representative spread
    idxs = list(range(0, len(traj), max(1, len(traj)//25)))
    for i in idxs:
        cam, T_c2w = build_camera_from_row(traj[i], K)
        with torch.no_grad():
            pkg = render(cam, g, bg)
        vis = (pkg["radii"] > 0)
        frac_vis = vis.float().mean().item()
        cam_pos = T_c2w[:3, 3]
        dist = np.linalg.norm(g._xyz.detach().cpu().numpy() - cam_pos, axis=1)
        frac_5m = (dist < 5.0).mean()
        frac_10m = (dist < 10.0).mean()
        fracs.append(frac_vis)
        print(f"{i:5d} {frac_vis:14.4f} {frac_5m:16.4f} {frac_10m:17.4f}")
    print(f"\nmean visible fraction across {len(idxs)} sampled keyframes: {np.mean(fracs):.4f}")


def frustum_prefilter(xyz, world_view_transform, tanfovx, tanfovy, margin=1.3):
    """Coarse Python-side frustum test (no custom CUDA) -- project gaussian
    centers into camera space via the SAME world_view_transform render() uses,
    keep points in front of the camera and within an expanded FOV cone.
    margin>1 gives slack since actual splats have nonzero screen-space radius
    (a center just outside the strict FOV can still splat partially into frame)."""
    ones = torch.ones((xyz.shape[0], 1), device=xyz.device, dtype=xyz.dtype)
    xyz_h = torch.cat([xyz, ones], dim=1)  # (N,4)
    cam_pts = xyz_h @ world_view_transform  # (N,4), world_view_transform already row-vector convention used by renderer
    z = cam_pts[:, 2]
    x = cam_pts[:, 0]
    y = cam_pts[:, 1]
    in_front = z > 0.01
    within_x = x.abs() < (margin * tanfovx * z)
    within_y = y.abs() < (margin * tanfovy * z)
    return in_front & within_x & within_y


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "filter_check":
    g = load_gaussians(PLY)
    K = np.load(os.path.join(RUN_DIR, "intrinsics.npy"))
    traj = np.loadtxt(os.path.join(RUN_DIR, "traj_kf_beforeBA.txt"))
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    idxs = list(range(0, len(traj), max(1, len(traj)//25)))
    print(f"{'idx':>5s} {'true_vis%':>10s} {'filt_keep%':>11s} {'recall':>8s} {'precision':>10s}")
    recalls, keeps = [], []
    for i in idxs:
        cam, T_c2w = build_camera_from_row(traj[i], K)
        with torch.no_grad():
            pkg = render(cam, g, bg)
            true_vis = (pkg["radii"] > 0)
            keep = frustum_prefilter(g._xyz, cam.world_view_transform, np.tan(cam.FoVx*0.5), np.tan(cam.FoVy*0.5), margin=1.3)
        recall = (true_vis & keep).float().sum() / true_vis.float().sum().clamp(min=1)
        keep_frac = keep.float().mean()
        precision = (true_vis & keep).float().sum() / keep.float().sum().clamp(min=1)
        recalls.append(recall.item()); keeps.append(keep_frac.item())
        print(f"{i:5d} {true_vis.float().mean().item()*100:10.2f} {keep_frac.item()*100:11.2f} {recall.item():8.4f} {precision.item():10.4f}")
    print(f"\nmean recall(진짜 visible을 놓치지 않는 비율)={np.mean(recalls):.4f}  mean keep_frac(필터 통과 비율)={np.mean(keeps):.4f}")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "margin_sweep":
    g = load_gaussians(PLY)
    K = np.load(os.path.join(RUN_DIR, "intrinsics.npy"))
    traj = np.loadtxt(os.path.join(RUN_DIR, "traj_kf_beforeBA.txt"))
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    idxs = list(range(0, len(traj), max(1, len(traj)//25)))
    print(f"{'margin':>8s} {'mean_recall':>12s} {'mean_keep%':>11s} {'min_recall':>11s}")
    for margin in [1.3, 1.6, 2.0, 2.5, 3.0, 4.0]:
        recalls, keeps = [], []
        for i in idxs:
            cam, T_c2w = build_camera_from_row(traj[i], K)
            with torch.no_grad():
                pkg = render(cam, g, bg)
                true_vis = (pkg["radii"] > 0)
                keep = frustum_prefilter(g._xyz, cam.world_view_transform, np.tan(cam.FoVx*0.5), np.tan(cam.FoVy*0.5), margin=margin)
            recall = ((true_vis & keep).float().sum() / true_vis.float().sum().clamp(min=1)).item()
            keeps.append(keep.float().mean().item())
            recalls.append(recall)
        print(f"{margin:8.1f} {np.mean(recalls):12.4f} {np.mean(keeps)*100:11.2f} {np.min(recalls):11.4f}")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "window_union":
    g = load_gaussians(PLY)
    K = np.load(os.path.join(RUN_DIR, "intrinsics.npy"))
    traj = np.loadtxt(os.path.join(RUN_DIR, "traj_kf_beforeBA.txt"))
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    WIN = 17  # window_size(10)+1+n_global_views(6) 근사
    margin = 3.0
    N = g._xyz.shape[0]
    starts = list(range(0, len(traj) - WIN, max(1, (len(traj) - WIN) // 15)))
    print(f"{'start':>6s} {'union_true_vis%':>16s} {'union_filt_keep%':>17s} {'union_recall':>13s}")
    keeps, recalls = [], []
    for s in starts:
        window_idxs = list(range(s, min(s + WIN, len(traj))))
        true_union = torch.zeros(N, dtype=torch.bool, device="cuda")
        keep_union = torch.zeros(N, dtype=torch.bool, device="cuda")
        for i in window_idxs:
            cam, T_c2w = build_camera_from_row(traj[i], K)
            with torch.no_grad():
                pkg = render(cam, g, bg)
                true_union |= (pkg["radii"] > 0)
                keep_union |= frustum_prefilter(g._xyz, cam.world_view_transform, np.tan(cam.FoVx*0.5), np.tan(cam.FoVy*0.5), margin=margin)
        recall = ((true_union & keep_union).float().sum() / true_union.float().sum().clamp(min=1)).item()
        keeps.append(keep_union.float().mean().item())
        recalls.append(recall)
        print(f"{s:6d} {true_union.float().mean().item()*100:16.2f} {keep_union.float().mean().item()*100:17.2f} {recall:13.4f}")
    print(f"\nmean union true_vis%={np.mean([true_union.float().mean().item() for _ in [0]])}")  # placeholder
    print(f"mean union keep%={np.mean(keeps)*100:.2f}  mean union recall={np.mean(recalls):.4f}")
