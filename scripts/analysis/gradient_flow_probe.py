#!/usr/bin/env python3
"""
gradient_flow_probe.py
======================
exp32 30k 체크포인트에서 뷰별 backward를 돌려 라벨 floater들의 gradient를
뷰 단위로 분해한다 (round8_gpu_queue_plan.md 단계 ②).

측정:
  - coherence ratio ‖Σ_v g‖ / Σ_v ‖g‖  (xyz) — 진동 vs 줄다리기 판정
  - opacity gradient의 뷰별 부호 분해 — 부양(음수=키우려 함) 뷰 집중도
  - 표면 대조군 동일 측정

출력: results/experiments/exp32_lineage_diag/gradient_probe.npz + 콘솔 요약
실행: cd 3dgs-custom && python .../gradient_flow_probe.py [--stride 2]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom")
sys.path.insert(0, str(REPO))

from gaussian_renderer import render  # noqa: E402
from scene import Scene, GaussianModel  # noqa: E402
from arguments import ModelParams, PipelineParams  # noqa: E402
from utils.loss_utils import l1_loss, ssim  # noqa: E402

BASE = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp32_lineage_diag")
SRC = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full"
N_CTRL = 3000


def deleted_mask():
    from plyfile import PlyData
    from scipy.spatial import cKDTree
    v = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud.ply"))["vertex"]
    vc = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud_cleaned.ply"))["vertex"]
    fo = np.stack([np.asarray(v[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    fc = np.stack([np.asarray(vc[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    d, _ = cKDTree(fc).query(fo, workers=-1)
    return d > 1e-5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stride", type=int, default=2)
    known, _ = ap.parse_known_args()

    parser = argparse.ArgumentParser()
    lp = ModelParams(parser)
    pp = PipelineParams(parser)
    args = parser.parse_args(["-m", str(BASE), "-s", SRC, "--data_device", "cpu"])
    gaussians = GaussianModel(lp.extract(args).sh_degree)
    scene = Scene(lp.extract(args), gaussians, load_iteration=30000, shuffle=False)
    pipe = pp.extract(args)
    views = scene.getTrainCameras()[::known.stride]
    print(f"[scene] {len(views)} views, N={gaussians.get_xyz.shape[0]:,}")

    deleted = deleted_mask()
    fl_idx = np.where(deleted)[0]
    rng = np.random.default_rng(0)
    ctrl_idx = rng.choice(np.where(~deleted)[0], N_CTRL, replace=False)
    fl_t = torch.tensor(fl_idx, device="cuda")
    ct_t = torch.tensor(ctrl_idx, device="cuda")

    V = len(views)
    fl_xyz = np.zeros((len(fl_idx), V, 3), np.float16)
    fl_op = np.zeros((len(fl_idx), V), np.float16)
    ct_xyz = np.zeros((N_CTRL, V, 3), np.float16)
    ct_op = np.zeros((N_CTRL, V), np.float16)

    bg = torch.tensor([0., 0., 0.], device="cuda")
    for vi, view in enumerate(views):
        img = render(view, gaussians, pipe, bg)["render"]
        gt = view.original_image.cuda()
        loss = 0.8 * l1_loss(img, gt) + 0.2 * (1.0 - ssim(img, gt))
        loss.backward()
        with torch.no_grad():
            gx = gaussians._xyz.grad
            go = gaussians._opacity.grad
            fl_xyz[:, vi] = gx[fl_t].cpu().numpy().astype(np.float16)
            fl_op[:, vi] = go[fl_t, 0].cpu().numpy().astype(np.float16)
            ct_xyz[:, vi] = gx[ct_t].cpu().numpy().astype(np.float16)
            ct_op[:, vi] = go[ct_t, 0].cpu().numpy().astype(np.float16)
            gaussians._xyz.grad = None
            gaussians._opacity.grad = None
            for p in (gaussians._features_dc, gaussians._features_rest,
                      gaussians._scaling, gaussians._rotation):
                p.grad = None
        if vi % 100 == 0:
            print(f"  view {vi}/{V}", flush=True)

    np.savez_compressed(BASE / "gradient_probe.npz",
                        fl_idx=fl_idx, ctrl_idx=ctrl_idx,
                        fl_xyz=fl_xyz, fl_op=fl_op, ct_xyz=ct_xyz, ct_op=ct_op)
    print(f"[saved] {BASE/'gradient_probe.npz'}")

    # ── 요약 통계 ──
    def coherence(g):   # (N,V,3) f16
        g = g.astype(np.float32)
        num = np.linalg.norm(g.sum(1), axis=1)
        den = np.linalg.norm(g, axis=2).sum(1) + 1e-12
        return num / den

    for name, gx, go in (("floater", fl_xyz, fl_op), ("surface", ct_xyz, ct_op)):
        c = coherence(gx)
        go32 = go.astype(np.float32)
        lift = np.clip(-go32, 0, None)      # 음수 grad = opacity 올리려는 힘(부양)
        supp = np.clip(go32, 0, None)       # 양수 = 낮추려는 힘
        net = go32.sum(1)
        lift_sum = lift.sum(1) + 1e-12
        # 부양 집중도: 상위 10뷰가 부양 질량에서 차지하는 비율
        top10 = np.sort(lift, axis=1)[:, -10:].sum(1) / lift_sum
        print(f"\n[{name}] n={len(gx):,}")
        print(f"  xyz coherence ‖Σg‖/Σ‖g‖: p50={np.median(c):.3f}  p90={np.percentile(c,90):.3f}")
        print(f"  opacity net grad<0(순부양) 비율: {(net<0).mean()*100:.1f}%")
        print(f"  부양/억압 질량비 p50: {np.median(lift.sum(1)/(supp.sum(1)+1e-12)):.2f}")
        print(f"  부양 상위10뷰 집중도 p50: {np.median(top10)*100:.1f}%  p90: {np.percentile(top10,90)*100:.1f}%")


if __name__ == "__main__":
    main()
