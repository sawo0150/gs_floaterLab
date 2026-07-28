#!/usr/bin/env python3
"""exp56 Phase 11 -- render_kernel_batch() 검증: sequential render() B-loop과
forward bit-exact / backward gradient-diff(atomic noise 수준)인지 확인.
realistic loss 사용(Phase 10 디버깅에서 .sum() 같은 비현실적 loss가 render()
자체의 atomic 비결정성을 증폭시켜 가짜 "버그"처럼 보이게 한다는 걸 배웠음).
"""
import sys, os
sys.path.append("/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM/vigs")
import numpy as np
import torch
from plyfile import PlyData
from scipy.spatial.transform import Rotation as R

from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.renderer import render, render_kernel_batch

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
    g._xyz = torch.tensor(xyz, dtype=torch.float, device="cuda", requires_grad=True)
    g._features_dc = torch.tensor(features_dc, dtype=torch.float, device="cuda").transpose(1, 2).contiguous().requires_grad_(True)
    g._features_rest = torch.zeros((g._xyz.shape[0], 0, 3), dtype=torch.float, device="cuda")
    g._opacity = torch.tensor(opacities, dtype=torch.float, device="cuda", requires_grad=True)
    g._scaling = torch.tensor(scales, dtype=torch.float, device="cuda", requires_grad=True)
    g._rotation = torch.tensor(rots, dtype=torch.float, device="cuda", requires_grad=True)
    g.max_sh_degree = 0; g.active_sh_degree = 0
    g.scaling_activation = torch.exp; g.opacity_activation = torch.sigmoid; g.rotation_activation = torch.nn.functional.normalize
    type(g).get_xyz = property(lambda self: self._xyz)
    type(g).get_scaling = property(lambda self: self.scaling_activation(self._scaling))
    type(g).get_rotation = property(lambda self: self.rotation_activation(self._rotation))
    type(g).get_opacity = property(lambda self: self.opacity_activation(self._opacity))
    type(g).get_features = property(lambda self: torch.cat((self._features_dc, self._features_rest), dim=1))
    return g


def build_camera(row_idx, K, traj):
    row = traj[row_idx]
    tx, ty, tz, qx, qy, qz, qw = row[1:8]
    T_c2w = np.eye(4)
    T_c2w[:3, :3] = R.from_quat([qx, qy, qz, qw]).as_matrix()
    T_c2w[:3, 3] = [tx, ty, tz]
    pose = torch.tensor(np.linalg.inv(T_c2w), dtype=torch.float32, device="cuda")
    W, H = 1024, 1024
    fx, fy, cx, cy = float(K[0]), float(K[1]), float(K[2]), float(K[3])
    projection_matrix = getProjectionMatrix2(znear=0.01, zfar=100.0, fx=fx, fy=fy, cx=cx, cy=cy, W=W, H=H).transpose(0, 1).cuda()
    return Camera.init_from_tracking(None, None, None, pose, 0, projection_matrix, [fx, fy, cx, cy, W, H])


def zero_grads(g):
    for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
        t.grad = None


if __name__ == "__main__":
    g = load_gaussians(PLY)
    N = g._xyz.shape[0]
    K = np.load(os.path.join(RUN_DIR, "intrinsics.npy"))
    traj = np.loadtxt(os.path.join(RUN_DIR, "traj_kf_beforeBA.txt"))
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")

    B = 6
    idxs = np.linspace(0, len(traj) - 1, B).astype(int)
    cams = [build_camera(i, K, traj) for i in idxs]
    torch.manual_seed(0)
    gt_images = [torch.rand(3, 1024, 1024, device="cuda") for _ in range(B)]

    # --- sequential render() loop (ground truth path) ---
    loss_seq = 0
    for cam, gt in zip(cams, gt_images):
        pkg = render(cam, g, bg)
        image = torch.clamp(pkg["render"], 0.0, 1.0)
        loss_seq = loss_seq + torch.abs(image - gt).mean() + torch.abs(pkg["depth"]).mean() * 0.01
    loss_seq.backward()
    grads_seq = {k: getattr(g, f"_{k}" if k != "features_dc" else "_features_dc").grad.clone() for k in ["xyz", "opacity", "scaling", "rotation", "features_dc"]}
    render_seq = [torch.clamp(render(cam, g, bg)["render"], 0.0, 1.0).detach().clone() for cam in cams]
    zero_grads(g)

    # --- render_kernel_batch() (Phase 11 path) ---
    pkgs = render_kernel_batch(cams, g, bg)
    loss_batch = 0
    for pkg, gt in zip(pkgs, gt_images):
        image = torch.clamp(pkg["render"], 0.0, 1.0)
        loss_batch = loss_batch + torch.abs(image - gt).mean() + torch.abs(pkg["depth"]).mean() * 0.01
    loss_batch.backward()
    grads_batch = {k: getattr(g, f"_{k}" if k != "features_dc" else "_features_dc").grad.clone() for k in ["xyz", "opacity", "scaling", "rotation", "features_dc"]}
    render_batch_imgs = [torch.clamp(pkg["render"], 0.0, 1.0).detach().clone() for pkg in pkgs]
    zero_grads(g)

    print(f"B={B} cameras, N={N} gaussians\n")
    print("=== forward ===")
    for b in range(B):
        diff = (render_seq[b] - render_batch_imgs[b]).abs().max().item()
        print(f"  cam{b}: render max abs diff = {diff:.3e}")

    print("\n=== backward (summed over all B cameras, matches how loss accumulates in gs_backend.py) ===")
    for k in grads_seq:
        gs_, gb_ = grads_seq[k], grads_batch[k]
        diff = (gs_ - gb_).abs()
        rel = diff.max().item() / (gs_.abs().max().item() + 1e-12)
        print(f"  grad[{k}] max abs diff: {diff.max().item():.3e}  rel: {rel:.3e}")

    print("\n=== per-camera dL_dmeans2D (viewspace_points, used for densification) sanity ===")
    for b in range(B):
        vpt = pkgs[b]["viewspace_points"]
        print(f"  cam{b}: viewspace_points.grad is None? {vpt.grad is None}, shape={None if vpt.grad is None else tuple(vpt.grad.shape)}")
