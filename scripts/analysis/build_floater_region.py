#!/usr/bin/env python3
"""
build_floater_region.py
=======================
수동 라벨 floater들의 xyz + covariance로 3D "삭제 영역"(voxel 볼륨 + 폴리곤 메시)을
조각한다. 같은 좌표계의 다른 run에 스탬프처럼 재사용 가능.

구성:
 1. 각 라벨 floater를 2σ ellipsoid로 dilate해 voxel 점유 마스크 생성
 2. 안전 깎기: 가시(op>0.3) 생존 점이 든 voxel + 그 이웃(마진)을 영역에서 제거
 3. morphological closing으로 무리 내부 구멍 메움
 4. marching cubes → 검수용 폴리곤 메시 (.ply)

출력 (--out-dir):
  region_mask.npz    (mask, lo, voxel)  ← 적용 시 이걸 로드
  region_mesh.ply    검수용 메시 (MeshLab/CloudCompare 등)
  report.json

적용 (다른 run):
  python build_floater_region.py --apply <다른run>/point_cloud.ply --region <region_mask.npz>
"""
import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree
from scipy import ndimage

VOX = 0.075   # 영역 해상도 (7.5cm)


def load_gauss(ply_path):
    v = PlyData.read(str(ply_path))["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1).astype(np.float64))
    return v, xyz, opac, scales


def match_deleted(v_orig, cleaned_path):
    vc = PlyData.read(str(cleaned_path))["vertex"]
    fo = np.stack([np.asarray(v_orig[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    fc = np.stack([np.asarray(vc[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    d, _ = cKDTree(fc).query(fo, workers=-1)
    return d > 1e-5


def build_tetra(orig_ply, cleaned_ply, out_dir, max_iter=3, grow_tol=0.05):
    """Delaunay 사면체 채움 방식:
    floater 점들의 사면체 중 '가시 표면 점이 하나도 없는' 것만 영역으로 채움.
    채워진 영역 안의 저op 생존점(=floater 후보)을 꼭짓점에 추가해 반복 확장."""
    from scipy.spatial import Delaunay

    v, xyz, opac, scales = load_gauss(orig_ply)
    deleted = match_deleted(v, cleaned_ply)
    keep_vis_xyz = xyz[~deleted & (opac > 0.3)]
    verts_f = xyz[deleted].astype(np.float64)
    print(f"floaters {deleted.sum():,}, 가시 생존점 {len(keep_vis_xyz):,}")

    lo = xyz[deleted].min(0) - 0.5
    hi = xyz[deleted].max(0) + 0.5
    dims = np.ceil((hi - lo) / VOX).astype(int) + 1
    # voxel 중심 좌표 (한 번만 생성)
    gx, gy, gz = np.meshgrid(*[np.arange(d) for d in dims], indexing="ij")
    centers = lo + (np.stack([gx, gy, gz], -1).reshape(-1, 3) + 0.5) * VOX

    mask = np.zeros(int(np.prod(dims)), bool)
    prev_vol = 0.0
    for it in range(max_iter):
        tri = Delaunay(verts_f)
        n_tet = len(tri.simplices)
        # 가시 표면 점이 든 사면체는 기각
        s_vis = tri.find_simplex(keep_vis_xyz.astype(np.float64))
        bad = np.zeros(n_tet, bool)
        bad[np.unique(s_vis[s_vis >= 0])] = True
        # voxel 중심 → 사면체 귀속 (기각 안 된 사면체만 채움)
        s_vox = tri.find_simplex(centers)
        fill = (s_vox >= 0) & ~bad[np.clip(s_vox, 0, n_tet - 1)]
        mask |= fill
        vol = mask.sum() * VOX ** 3
        print(f"  iter {it+1}: verts {len(verts_f):,}, tets {n_tet:,} (기각 {int(bad.sum()):,})"
              f" → 영역 {vol:.2f} m³")
        if prev_vol > 0 and (vol - prev_vol) / prev_vol < grow_tol:
            break
        prev_vol = vol
        # 확장: 영역 안 저op 생존점을 꼭짓점에 추가
        gi = np.floor((xyz - lo) / VOX).astype(int)
        ok = ((gi >= 0) & (gi < dims[None, :])).all(1)
        flat = (gi[:, 0] * dims[1] + gi[:, 1]) * dims[2] + gi[:, 2]
        inreg = np.zeros(len(xyz), bool)
        inreg[ok] = mask[flat[ok]]
        cand = inreg & ~deleted & (opac <= 0.3)
        new_verts = np.vstack([verts_f, xyz[cand].astype(np.float64)])
        if len(new_verts) == len(verts_f):
            break
        verts_f = np.unique(new_verts, axis=0)

    mask = mask.reshape(tuple(dims))
    # 안전 깎기: 가시 생존점 voxel + 1-이웃 제거 (경계 보호)
    gi = np.floor((keep_vis_xyz - lo) / VOX).astype(int)
    ok = ((gi >= 0) & (gi < dims[None, :])).all(1)
    carve = np.zeros(tuple(dims), bool)
    carve[gi[ok, 0], gi[ok, 1], gi[ok, 2]] = True
    carve = ndimage.binary_dilation(carve, structure=np.ones((3, 3, 3)))
    mask &= ~carve
    print(f"  깎기 후 {int(mask.sum()):,} voxels ({mask.sum()*VOX**3:.2f} m³)")

    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "region_mask.npz", mask=mask, lo=lo, voxel=VOX)

    from skimage import measure
    verts_m, faces, _, _ = measure.marching_cubes(mask.astype(np.float32), level=0.5, spacing=(VOX,) * 3)
    verts_m = verts_m + lo
    vert_el = np.array([tuple(p) for p in verts_m], dtype=[("x", "f4"), ("y", "f4"), ("z", "f4")])
    face_el = np.array([(list(f),) for f in faces], dtype=[("vertex_indices", "i4", (3,))])
    PlyData([PlyElement.describe(vert_el, "vertex"),
             PlyElement.describe(face_el, "face")]).write(str(out_dir / "region_mesh.ply"))
    print(f"[mesh] {len(verts_m):,} verts → region_mesh.ply")

    rep = evaluate(orig_ply, out_dir / "region_mask.npz", label_cleaned=cleaned_ply)
    json.dump(rep, open(out_dir / "report.json", "w"), indent=2, ensure_ascii=False)
    return out_dir / "region_mask.npz"


def build(orig_ply, cleaned_ply, out_dir):
    v, xyz, opac, scales = load_gauss(orig_ply)
    deleted = match_deleted(v, cleaned_ply)
    f_xyz, f_scale = xyz[deleted], scales[deleted]
    keep_vis = xyz[~deleted & (opac > 0.3)]
    print(f"floaters {deleted.sum():,}, 가시 생존점 {len(keep_vis):,}")

    lo = f_xyz.min(0) - 0.5
    hi = f_xyz.max(0) + 0.5
    dims = np.ceil((hi - lo) / VOX).astype(int) + 1
    mask = np.zeros(tuple(dims), bool)

    # 1) floater 2σ ellipsoid 점유 (축정렬 근사 — max scale 기준 구형 dilate)
    r2 = np.clip(2.0 * f_scale.max(1), VOX, 0.20)     # 2σ, 상한 20cm
    for p, r in zip(f_xyz, r2):
        g0 = np.floor((p - r - lo) / VOX).astype(int)
        g1 = np.ceil((p + r - lo) / VOX).astype(int) + 1
        g0 = np.clip(g0, 0, dims - 1); g1 = np.clip(g1, 1, dims)
        xs, ys, zs = np.meshgrid(*[np.arange(a, b) for a, b in zip(g0, g1)], indexing="ij")
        centers = lo + (np.stack([xs, ys, zs], -1) + 0.5) * VOX
        inside = np.linalg.norm(centers - p, axis=-1) <= r
        sub = mask[g0[0]:g1[0], g0[1]:g1[1], g0[2]:g1[2]]
        sub |= inside
        mask[g0[0]:g1[0], g0[1]:g1[1], g0[2]:g1[2]] = sub

    n_before = int(mask.sum())
    # 2) 내부 구멍 메움 (closing)
    mask = ndimage.binary_closing(mask, structure=np.ones((3, 3, 3)))

    # 3) 안전 깎기: 가시 생존점 voxel + 1-이웃 제거
    gi = np.floor((keep_vis - lo) / VOX).astype(int)
    ok = ((gi >= 0) & (gi < dims[None, :])).all(1)
    carve = np.zeros(tuple(dims), bool)
    carve[gi[ok, 0], gi[ok, 1], gi[ok, 2]] = True
    carve = ndimage.binary_dilation(carve, structure=np.ones((3, 3, 3)))
    mask &= ~carve
    print(f"voxels: 점유 {n_before:,} → closing/깎기 후 {int(mask.sum()):,} "
          f"(부피 {mask.sum()*VOX**3:.2f} m³)")

    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "region_mask.npz", mask=mask, lo=lo, voxel=VOX)

    # 4) 검수 메시
    from skimage import measure
    verts, faces, _, _ = measure.marching_cubes(mask.astype(np.float32), level=0.5, spacing=(VOX,) * 3)
    verts = verts + lo
    vert_el = np.array([tuple(p) for p in verts], dtype=[("x", "f4"), ("y", "f4"), ("z", "f4")])
    face_el = np.array([(list(f),) for f in faces], dtype=[("vertex_indices", "i4", (3,))])
    PlyData([PlyElement.describe(vert_el, "vertex"),
             PlyElement.describe(face_el, "face")]).write(str(out_dir / "region_mesh.ply"))
    print(f"[mesh] {len(verts):,} verts / {len(faces):,} faces → region_mesh.ply")

    rep = evaluate(orig_ply, out_dir / "region_mask.npz", label_cleaned=cleaned_ply)
    json.dump(rep, open(out_dir / "report.json", "w"), indent=2, ensure_ascii=False)
    return out_dir / "region_mask.npz"


def points_in_region(xyz, region_npz):
    z = np.load(region_npz)
    mask, lo, vox = z["mask"], z["lo"], float(z["voxel"])
    dims = np.array(mask.shape)
    gi = np.floor((xyz - lo) / vox).astype(int)
    ok = ((gi >= 0) & (gi < dims[None, :])).all(1)
    out = np.zeros(len(xyz), bool)
    out[ok] = mask[gi[ok, 0], gi[ok, 1], gi[ok, 2]]
    return out


def evaluate(ply_path, region_npz, label_cleaned=None, write_outputs=False):
    v, xyz, opac, scales = load_gauss(ply_path)
    try:
        visn = np.clip(np.asarray(v["accum_visibility"]).astype(np.float64), 1, None)
    except Exception:
        visn = np.ones(len(xyz))
    contrib = opac * np.sort(scales, 1)[:, 1:].prod(1) * visn
    inreg = points_in_region(xyz, region_npz)
    rep = {"ply": str(ply_path), "n": len(xyz), "in_region": int(inreg.sum()),
           "in_region_visible(op>0.3)": int((inreg & (opac > 0.3)).sum()),
           "in_region_contrib_pct": float(contrib[inreg].sum() / contrib.sum() * 100)}
    if label_cleaned:
        gt = match_deleted(v, label_cleaned)
        rep["recall_vs_labels"] = float((inreg & gt).sum() / gt.sum())
        rep["kept_points_in_region"] = int((inreg & ~gt).sum())
        rep["kept_visible_in_region"] = int((inreg & ~gt & (opac > 0.3)).sum())
    print(f"[eval] {Path(ply_path).parts[-4] if 'point_cloud' in str(ply_path) else ply_path}")
    for k, val in rep.items():
        if k != "ply":
            print(f"    {k}: {val:,}" if isinstance(val, int) else f"    {k}: {val}")
    if write_outputs:
        out_dir = Path(ply_path).parent / "region_floaters"
        out_dir.mkdir(exist_ok=True)
        np.save(out_dir / "floater_mask.npy", inreg)
        PlyData([PlyElement.describe(v.data[~inreg], "vertex")]).write(str(out_dir / "point_cloud_cleaned.ply"))
        PlyData([PlyElement.describe(v.data[inreg], "vertex")]).write(str(out_dir / "floaters_only.ply"))
        print(f"    → {out_dir}")
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-from", help="라벨 원본 ply (build 모드)")
    ap.add_argument("--cleaned", help="수동 cleaned ply (build 모드)")
    ap.add_argument("--apply", help="영역을 적용할 다른 run의 ply")
    ap.add_argument("--region", help="region_mask.npz (apply 모드)")
    ap.add_argument("--labels", help="apply 대상의 라벨 cleaned ply (있으면 recall)")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--method", choices=["dilate", "tetra"], default="dilate",
                    help="dilate=점 주변 부풀림, tetra=Delaunay 사면체 채움(점 사이 공간 포함)")
    args = ap.parse_args()

    if args.build_from:
        out = Path(args.out_dir) if args.out_dir else Path(args.build_from).parent / "floater_region"
        if args.method == "tetra":
            build_tetra(Path(args.build_from), Path(args.cleaned), out)
        else:
            build(Path(args.build_from), Path(args.cleaned), out)
    elif args.apply:
        evaluate(Path(args.apply), Path(args.region), label_cleaned=args.labels, write_outputs=True)


if __name__ == "__main__":
    main()
