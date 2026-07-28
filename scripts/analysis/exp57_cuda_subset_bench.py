#!/usr/bin/env python3
"""exp57 CUDA-native visible-subset rasterizer microbenchmark.

Measures a realistic L1 RGB + small depth backward pass on the same fixed map
and camera. The subset timing includes frustum mask construction and nonzero()
so the reported gain is end-to-end rather than kernel-only.
"""
import time

import numpy as np
import torch

from exp56_phase10_render_filtered_check import (
    build_camera,
    load_gaussians,
    PLY,
    zero_grads,
)
from gaussian.renderer import render, render_filtered, frustum_prefilter


def one_step(g, cam, bg, gt, subset, cached_ids=None):
    if subset:
        if cached_ids is None:
            keep = frustum_prefilter(
                g.get_xyz,
                cam.world_view_transform,
                np.tan(cam.FoVx * 0.5),
                np.tan(cam.FoVy * 0.5),
                margin=3.0,
            )
        else:
            keep = cached_ids
        pkg = render_filtered(cam, g, bg, keep)
    else:
        keep = None
        pkg = render(cam, g, bg)
    image = torch.clamp(pkg["render"], 0.0, 1.0)
    loss = torch.abs(image - gt).mean() + 0.01 * torch.abs(pkg["depth"]).mean()
    loss.backward()
    zero_grads(g)
    return keep, pkg


def bench(g, cam, bg, gt, subset, cached_ids=None, warmup=20, repeats=200):
    for _ in range(warmup):
        one_step(g, cam, bg, gt, subset, cached_ids)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    keep = pkg = None
    for _ in range(repeats):
        keep, pkg = one_step(g, cam, bg, gt, subset, cached_ids)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - t0
    return {
        "mode": "cuda_subset_cached" if cached_ids is not None else ("cuda_subset" if subset else "full"),
        "ms_per_step": elapsed * 1000.0 / repeats,
        "keep_frac": (
            float(keep.numel() / g.get_xyz.shape[0])
            if keep is not None and keep.dtype != torch.bool
            else (float(keep.float().mean()) if keep is not None else 1.0)
        ),
        "visible": int(pkg["visibility_filter"].sum()),
        "gaussians": int(g.get_xyz.shape[0]),
    }


if __name__ == "__main__":
    torch.manual_seed(0)
    g = load_gaussians(PLY)
    cam = build_camera()
    bg = torch.zeros(3, dtype=torch.float32, device="cuda")
    gt = torch.rand(3, 1024, 1024, device="cuda")
    full = bench(g, cam, bg, gt, subset=False)
    subset = bench(g, cam, bg, gt, subset=True)
    keep = frustum_prefilter(
        g.get_xyz,
        cam.world_view_transform,
        np.tan(cam.FoVx * 0.5),
        np.tan(cam.FoVy * 0.5),
        margin=3.0,
    )
    cached_ids = keep.nonzero(as_tuple=True)[0].to(dtype=torch.int32).contiguous()
    cached = bench(g, cam, bg, gt, subset=True, cached_ids=cached_ids)
    print(full)
    print(subset)
    print(cached)
    for result in (subset, cached):
        speedup = full["ms_per_step"] / result["ms_per_step"]
        saving = 100.0 * (1.0 - result["ms_per_step"] / full["ms_per_step"])
        print({"mode": result["mode"], "speedup": speedup, "saving_pct": saving})
