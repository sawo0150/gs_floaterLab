#!/usr/bin/env python3
"""
make_carve_prune_variants.py
============================
carve score 기반 prune 규칙 변형들을 exp32 30k ply에 적용해 렌더 검증용
모델 디렉토리(cfg_args + cameras.json + pruned ply)를 생성한다.
렌더/PSNR 검증은 GPU가 빌 때 run_carve_psnr_check.sh로 실행.

변형:
  A_safe : w>0.9 & op<0.1 & contrib<p90   (recall 69.4%, 표면 기여손실 0.393%, 구멍 0)
  A_mid  : w>0.9 & op<0.1                 (recall 72.2%, 표면 기여손실 0.880%, 구멍 0)
  A_orig : thr_max=0.2 선형 규칙(폐기 후보) (recall 89.6%, 표면 기여손실 3.83% — 대조용)
"""
import shutil
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from design_floater_loss_candidates import BASE, match_deleted
from plyfile import PlyData, PlyElement

OUT_ROOT = BASE / "carve_prune_variants"


def write_pruned(ply, keep, out_ply):
    v = ply["vertex"]
    data = v.data[keep]
    el = PlyElement.describe(data, "vertex")
    out_ply.parent.mkdir(parents=True, exist_ok=True)
    PlyData([el]).write(str(out_ply))


def main():
    ply = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud.ply"))
    v = ply["vertex"]
    vc = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud_cleaned.ply"))["vertex"]
    deleted = match_deleted(v, vc)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1).astype(np.float64))
    vis = np.asarray(v["accum_visibility"]).astype(np.float64)
    w = np.load(BASE / "final_score_w_phys.npz")["w"]
    contrib = opac * np.sort(scales, 1)[:, 1:].prod(1) * vis
    c90 = np.quantile(contrib, 0.90)

    variants = {
        "A_safe": (w > 0.9) & (opac < 0.1) & (contrib < c90),
        "A_mid": (w > 0.9) & (opac < 0.1),
        "A_orig": opac < (0.01 + w * 0.19),
    }
    nf = int(deleted.sum())
    for name, mask in variants.items():
        out_dir = OUT_ROOT / name
        out_dir.mkdir(parents=True, exist_ok=True)
        for f in ("cfg_args", "cameras.json", "exposure.json", "input.ply"):
            src = BASE / f
            if src.exists():
                shutil.copy(src, out_dir / f)
        write_pruned(ply, ~mask, out_dir / "point_cloud/iteration_30000/point_cloud.ply")
        rec = int((mask & deleted).sum()) / nf
        print(f"{name}: prune {int(mask.sum()):,}  floater recall {rec*100:.1f}%  → {out_dir}")

    # 사용자 수동 편집본도 렌더 비교 대상으로 복사
    out_dir = OUT_ROOT / "user_cleaned"
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in ("cfg_args", "cameras.json", "exposure.json", "input.ply"):
        src = BASE / f
        if src.exists():
            shutil.copy(src, out_dir / f)
    dst = out_dir / "point_cloud/iteration_30000/point_cloud.ply"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(BASE / "point_cloud/iteration_30000/point_cloud_cleaned.ply", dst)
    print(f"user_cleaned: → {out_dir}")


if __name__ == "__main__":
    main()
