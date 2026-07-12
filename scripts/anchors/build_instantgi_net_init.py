#!/usr/bin/env python3
"""
build_instantgi_net_init.py — exp44e2
=====================================
진짜 Instant-GI 사전학습 네트워크(ConvNeXt UNet)의 **학습된 Position Probability
Map**을 keyframe에 추론해 내용-적응 샘플링 → 보정 depth lift → 착색 init 생성.

- 무거운 의존성(gsplat/ellipse_fit/torch_kdtree)은 only_get_pf 경로에서 불필요 → 스텁.
- 체크포인트: scratchpad/Instant-GI/checkpoints/epoch_best_ks_4.pth (kernel_size=4)
- 출력: results/datasets/orb_instantgi_net_scene
"""
import sys
import types
import shutil
from pathlib import Path

import numpy as np
import torch
from PIL import Image

GI = Path("/tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/a18dbc8f-4cce-4ad0-a1ea-8f9bb38b1ea6/scratchpad/Instant-GI")
sys.path.insert(0, str(GI))

# ── 미사용 무거운 의존성 스텁 (only_get_pf 경로에선 호출 안 됨) ──
def _stub(*a, **k):
    raise RuntimeError("stub called — only_get_pf 경로 밖 사용 금지")
for name in ("gsplat", "gsplat.project_gaussians_2d_scale_rot", "gsplat.rasterize_sum",
             "gsplat.rasterize", "ellipse_fit", "torch_kdtree"):
    mod = types.ModuleType(name)
    mod.__path__ = []  # 패키지 흉내
    for attr in ("project_gaussians_2d_scale_rot", "rasterize_gaussians_sum", "fit_ellipses", "build_kd_tree"):
        setattr(mod, attr, _stub)
    sys.modules[name] = mod

sys.path.insert(0, "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/scripts/analysis")
from design_floater_loss_candidates import (
    BASE, VOXEL, load_slam, load_cameras, FX, FY, CX, CY, IMG_W, IMG_H)
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter
from sklearn.linear_model import HuberRegressor

from generalizable_model.init_net import InitNet  # noqa: E402 (스텁 이후 import)

DEPTH_DIR = Path("results/diagnostic/depth_maps_neworb_301_1253/depth_pro")
IMGDIR = Path("data/03_rgb_3dgs_full/images")
DST = Path("results/datasets/orb_instantgi_net_scene")
SRC = Path("results/datasets/orb_dense_confmono_init_scene")
CKPT = GI / "checkpoints/epoch_best_ks_4.pth"
PTS_PER_FRAME = 4000


def main():
    device = "cuda"
    net = InitNet(kernel_size=4).to(device).eval()
    ck = torch.load(CKPT, map_location=device)
    state = ck.get("model", ck)
    missing, unexpected = net.load_state_dict(state, strict=False)
    print(f"[ckpt] missing={len(missing)} unexpected={len(unexpected)}")

    Rs, ts = load_cameras()
    slam = load_slam()
    img_paths = sorted(IMGDIR.glob("*.jpg"))
    name2idx = {p.stem: i for i, p in enumerate(img_paths)}

    rng = np.random.default_rng(0)
    all_pts, all_rgb = [], []
    files = sorted(DEPTH_DIR.glob("*.npy"))
    for fi, df in enumerate(files):
        ci = name2idx.get(df.stem)
        if ci is None:
            continue
        im = np.asarray(Image.open(img_paths[ci])).astype(np.float32) / 255.0
        H, W = im.shape[:2]
        with torch.no_grad():
            timg = torch.tensor(im.transpose(2, 0, 1)[None], device=device)
            ppm, _ = net(timg, only_get_pf=True)          # [1, h, w] 학습된 확률맵
            p = ppm[0].float().clamp(min=0).cpu().numpy()
        # PPM 해상도 → 원본 해상도 (feature map이 다운샘플일 수 있음)
        if p.shape != (H, W):
            p = np.array(Image.fromarray(p).resize((W, H), Image.BILINEAR))
        p = p.ravel(); p = p - p.min(); p = p + p.mean() * 0.05 + 1e-9
        p /= p.sum()
        sel = rng.choice(len(p), PTS_PER_FRAME, replace=False, p=p)
        py, px = np.unravel_index(sel, (H, W))

        # 보정 depth lift (44e와 동일)
        depth = np.load(df).astype(np.float32)
        R, t = Rs[ci], ts[ci]
        pc = slam @ R.T + t
        z = pc[:, 2]
        ok = (z > 0.3) & (z < 12)
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 1) & (u < W - 1) & (v >= 1) & (v < H - 1)
        if ok.sum() < 10:
            continue
        zm = depth[v[ok].astype(int), u[ok].astype(int)]
        good = (zm > 0.1) & (zm < 20)
        if good.sum() < 10:
            continue
        reg = HuberRegressor(epsilon=1.35, max_iter=500).fit(zm[good, None], z[ok][good])
        depth_cal = np.maximum(reg.coef_[0] * depth + reg.intercept_, 0.15)
        zc = depth_cal[py, px]
        keep = (zc > 0.3) & (zc < 12)
        px, py, zc = px[keep], py[keep], zc[keep]
        xc = (px - CX) / FX * zc
        yc = (py - CY) / FY * zc
        Pw = (np.stack([xc, yc, zc], 1) - t) @ R
        all_pts.append(Pw.astype(np.float32))
        all_rgb.append((im[py, px] * 255).astype(np.uint8))
        if fi % 10 == 0:
            print(f"  frame {fi}/{len(files)}", flush=True)

    pts = np.concatenate(all_pts); rgb = np.concatenate(all_rgb)
    print(f"raw: {len(pts):,}")
    key = np.floor(pts / 0.05).astype(np.int64)
    _, uidx = np.unique(key, axis=0, return_index=True)
    pts, rgb = pts[uidx], rgb[uidx]
    print(f"5cm dedupe: {len(pts):,}")

    z0 = np.load(BASE / "carve_fields.npz")
    ts2 = uniform_filter(z0["transit"], 3); es2 = uniform_filter(z0["terminal"], 3)
    ratio = ts2 / (ts2 + 3 * es2 + 1e-6); lo = z0["lo"]; dims = z0["dims"]
    gi = np.floor((pts - lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
    rho = np.zeros(len(pts), np.float32); rho[inb] = ratio[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    d5, _ = cKDTree(slam).query(pts, k=5, workers=-1)
    w = rho * np.clip(d5.mean(1) / 0.25, 0, 1)
    keep = w <= 0.5
    pts, rgb = pts[keep], rgb[keep]
    print(f"carve 재필터: {len(pts):,}")

    slam_rgb = np.full((len(slam), 3), 128, np.uint8)
    pts = np.concatenate([slam, pts]); rgb = np.concatenate([slam_rgb, rgb])
    DST.mkdir(parents=True, exist_ok=True); (DST / "sparse/0").mkdir(parents=True, exist_ok=True)
    if not (DST / "images").exists():
        (DST / "images").symlink_to((SRC / "images").resolve())
    for f in ("cameras.txt", "images.txt"):
        shutil.copy(SRC / f"sparse/0/{f}", DST / f"sparse/0/{f}")
    with open(DST / "sparse/0/points3D.txt", "w") as fo:
        for i, (p, c) in enumerate(zip(pts, rgb)):
            fo.write(f"{i} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {c[0]} {c[1]} {c[2]} 0\n")
    print(f"최종 GI-net init {len(pts):,} → {DST}")


if __name__ == "__main__":
    main()
