#!/usr/bin/env python3
"""
carve_psnr_check.py
===================
carve prune 변형들의 렌더 품질 영향을 GPU 렌더링으로 직접 검증 (학습 없음).
각 변형에 대해 view subset을 렌더하고:
  - PSNR(GT, 변형)          : 절대 품질
  - PSNR(원본렌더, 변형렌더) : prune이 바꾼 픽셀량 (시각 변화 격리)
를 계산한다. PNG를 디스크에 쓰지 않고 메모리에서 처리.

실행: conda env 3dgs, GPU 필요 (~2GB)
  python scripts/analysis/carve_psnr_check.py [--stride 10]
"""
import argparse
import sys
from pathlib import Path

import torch

REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom")
sys.path.insert(0, str(REPO))

from argparse import Namespace  # noqa: E402
from gaussian_renderer import render  # noqa: E402
from scene import Scene, GaussianModel  # noqa: E402
from arguments import ModelParams, PipelineParams  # noqa: E402
from utils.image_utils import psnr  # noqa: E402

BASE = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp32_lineage_diag")
VARIANTS = ["A_safe", "A_mid", "A_orig", "user_cleaned"]


def load_model(model_path, source_path, parser):
    lp = ModelParams(parser, sentinel=True)
    pp = PipelineParams(parser)
    args = parser.parse_args([
        "-m", str(model_path), "-s", str(source_path),
        "--data_device", "cpu",
    ])
    dataset = lp.extract(args)
    pipe = pp.extract(args)
    gaussians = GaussianModel(dataset.sh_degree)
    scene = Scene(dataset, gaussians, load_iteration=30000, shuffle=False)
    return scene, gaussians, pipe


@torch.no_grad()
def render_views(scene, gaussians, pipe, stride):
    bg = torch.tensor([0., 0., 0.], device="cuda")
    views = scene.getTrainCameras()[::stride]
    outs, gts = [], []
    for view in views:
        img = render(view, gaussians, pipe, bg)["render"].clamp(0, 1)
        outs.append(img.cpu())
        gts.append(view.original_image[0:3].cpu().clamp(0, 1))
    return outs, gts


def mean_psnr(a_list, b_list):
    vals = []
    for a, b in zip(a_list, b_list):
        vals.append(psnr(a.unsqueeze(0).cuda(), b.unsqueeze(0).cuda()).mean().item())
    return sum(vals) / len(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stride", type=int, default=10)
    known, _ = ap.parse_known_args()
    stride = known.stride

    src = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full"

    print(f"[orig] rendering (stride={stride}) ...")
    scene, g, pipe = load_model(BASE, src, argparse.ArgumentParser())
    orig_out, gts = render_views(scene, g, pipe, stride)
    p_orig = mean_psnr(orig_out, gts)
    print(f"  PSNR(GT, 원본) = {p_orig:.3f}  ({len(orig_out)} views, N={g.get_xyz.shape[0]:,})")
    del scene, g
    torch.cuda.empty_cache()

    results = {"orig": {"psnr_gt": p_orig}}
    for name in VARIANTS:
        mdir = BASE / "carve_prune_variants" / name
        scene, g, pipe = load_model(mdir, src, argparse.ArgumentParser())
        out, _ = render_views(scene, g, pipe, stride)
        p_gt = mean_psnr(out, gts)
        p_delta = mean_psnr(out, orig_out)
        results[name] = {"psnr_gt": p_gt, "psnr_vs_orig_render": p_delta,
                         "n_gauss": int(g.get_xyz.shape[0])}
        print(f"  {name:<14} PSNR(GT)={p_gt:.3f} (Δ{p_gt-p_orig:+.3f})  "
              f"PSNR(vs 원본렌더)={p_delta:.2f}  N={g.get_xyz.shape[0]:,}")
        del scene, g
        torch.cuda.empty_cache()

    import json
    outp = BASE / "carve_psnr_check.json"
    json.dump(results, open(outp, "w"), indent=2)
    print(f"[saved] {outp}")


if __name__ == "__main__":
    main()
