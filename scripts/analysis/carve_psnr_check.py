#!/usr/bin/env python3
"""
carve_psnr_check.py
===================
carve prune 변형들의 렌더 품질 영향을 GPU 렌더링으로 직접 검증 (학습 없음).
Scene(이미지 1303장)은 1회만 로드하고, 변형별로 gaussians만 교체(load_ply).

각 변형에 대해 view subset을 렌더:
  - PSNR(GT, 변형)          : 절대 품질
  - PSNR(원본렌더, 변형렌더) : prune이 바꾼 픽셀량 (시각 변화 격리)

사전 등록 판정 (rounds/round8_carve_loss_design.md):
  A_safe 하락 ≤ 0.05dB → PASS

실행: conda env 3dgs, GPU (~2GB)
  python scripts/analysis/carve_psnr_check.py [--stride 10]
"""
import argparse
import json
import sys
from pathlib import Path

import torch

REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom")
sys.path.insert(0, str(REPO))

from gaussian_renderer import render  # noqa: E402
from scene import Scene, GaussianModel  # noqa: E402
from arguments import ModelParams, PipelineParams  # noqa: E402
from utils.image_utils import psnr  # noqa: E402

BASE = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp32_lineage_diag")
VARIANTS = ["A_safe", "A_mid", "A_orig", "user_cleaned", "rulebase_balanced", "region_cleaned"]
SRC = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full"


@torch.no_grad()
def render_views(views, gaussians, pipe):
    bg = torch.tensor([0., 0., 0.], device="cuda")
    outs = []
    for view in views:
        outs.append(render(view, gaussians, pipe, bg)["render"].clamp(0, 1).cpu())
    return outs


def mean_psnr(a_list, b_list):
    vals = []
    for a, b in zip(a_list, b_list):
        vals.append(psnr(a.unsqueeze(0).cuda(), b.unsqueeze(0).cuda()).mean().item())
    return sum(vals) / len(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stride", type=int, default=10)
    known, _ = ap.parse_known_args()

    parser = argparse.ArgumentParser()
    lp = ModelParams(parser)
    pp = PipelineParams(parser)
    args = parser.parse_args(["-m", str(BASE), "-s", SRC, "--data_device", "cpu"])
    dataset = lp.extract(args)
    pipe = pp.extract(args)

    gaussians = GaussianModel(dataset.sh_degree)
    scene = Scene(dataset, gaussians, load_iteration=30000, shuffle=False)
    views = scene.getTrainCameras()[::known.stride]
    gts = [v.original_image[0:3].cpu().clamp(0, 1) for v in views]
    print(f"[scene] {len(views)} views (stride {known.stride})")

    print("[orig] rendering ...")
    orig_out = render_views(views, gaussians, pipe)
    p_orig = mean_psnr(orig_out, gts)
    results = {"orig": {"psnr_gt": p_orig, "n_gauss": int(gaussians.get_xyz.shape[0])}}
    print(f"  orig            PSNR(GT)={p_orig:.3f}  N={gaussians.get_xyz.shape[0]:,}")

    for name in VARIANTS:
        ply = BASE / "carve_prune_variants" / name / "point_cloud/iteration_30000/point_cloud.ply"
        gaussians.load_ply(str(ply))
        out = render_views(views, gaussians, pipe)
        p_gt = mean_psnr(out, gts)
        p_delta = mean_psnr(out, orig_out)
        results[name] = {"psnr_gt": p_gt, "delta_vs_orig": p_gt - p_orig,
                         "psnr_vs_orig_render": p_delta,
                         "n_gauss": int(gaussians.get_xyz.shape[0])}
        print(f"  {name:<16} PSNR(GT)={p_gt:.3f} (Δ{p_gt-p_orig:+.3f})  "
              f"vs원본렌더={p_delta:.2f}dB  N={gaussians.get_xyz.shape[0]:,}", flush=True)
        torch.cuda.empty_cache()

    outp = BASE / "carve_psnr_check.json"
    json.dump(results, open(outp, "w"), indent=2)
    print(f"[saved] {outp}")


if __name__ == "__main__":
    main()
