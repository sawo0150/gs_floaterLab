#!/usr/bin/env python3
"""
design_floater_loss_candidates.py
=================================
수동 라벨(SuperSplat 삭제 2,817개)을 ground truth로, 학습 없이 후보 3D loss들의
"겨냥 신호"를 채점한다. 각 후보는 per-Gaussian 스칼라 score(=loss가 그 점을
밀어내는 세기)를 만들고, floater vs 표면 판별력(AUC)과 운영점(FP 고정) 재현율,
prune 시뮬레이션 결과를 리그 테이블로 출력한다.

후보:
  S1  d_slam_1nn      : SLAM 포인트 1-NN 유클리드 거리 (고정 tau plateau와 동치)
  S2  d_slam_5nn      : SLAM 5-NN 평균 거리 (SLAM outlier에 강건)
  S3  d_dp_1nn        : DepthPro anchor 1-NN 거리
  S4  ellip_cap_*     : 기존 ellipsoidal에서 tau 상한만 줄인 변형 (0.5x, 0.25x)
  S5  carve           : free-space ray transit (카메라→frustum 내 SLAM 포인트 ray가
                        해당 voxel을 '표면 앞 허공'으로 통과한 횟수) — 공간 조각 신호
  S6  carve_x_d       : carve rank × d_slam_5nn rank (곱 결합)
  S7  carve_x_op      : carve × opacity (보이는 dust 겨냥 — prune 후보)
  S8  plane_normal    : 최근접 SLAM anchor 국소 평면의 법선방향 거리 (적응 스케일 제거판)
"""
import json
from pathlib import Path

import numpy as np
import torch
from plyfile import PlyData
from scipy.spatial import KDTree
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors

ROOT = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
BASE = ROOT / "results/experiments/exp32_lineage_diag"
DATASET = ROOT / "data/03_rgb_3dgs_full"
DP_ANCHORS = ROOT / "results/diagnostic/native_anchors_neworb_v4_20260709_204706/anchors_all_depth_pro.npy"

IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 511.5, 511.5

VOXEL = 0.10          # carve voxel size (m)
RAY_STEP = 0.06       # carve ray sampling step (m)
SURF_MARGIN = 0.20    # 표면 anchor 앞 margin — 이 안쪽은 free space로 안 침
MIN_T = 0.15          # 카메라 바로 앞 제외


def qvec2rotmat(q):
    w, x, y, z = q
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y]])


def load_cameras():
    Rs, ts = [], []
    for line in open(DATASET / "sparse/0/images.txt"):
        p = line.strip().split()
        if len(p) < 9 or p[0].startswith("#"):
            continue
        q = np.array([float(x) for x in p[1:5]])
        t = np.array([float(x) for x in p[5:8]])
        Rs.append(qvec2rotmat(q))     # world→cam
        ts.append(t)
    return np.array(Rs, np.float32), np.array(ts, np.float32)


def load_slam():
    pts = []
    for line in open(DATASET / "sparse/0/points3D.txt"):
        if line.startswith("#") or not line.strip():
            continue
        tok = line.split()
        if len(tok) >= 7:
            pts.append([float(tok[1]), float(tok[2]), float(tok[3])])
    return np.array(pts, np.float32)


def match_deleted(v_orig, v_clean):
    fo = np.stack([np.asarray(v_orig[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    fc = np.stack([np.asarray(v_clean[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    d, _ = KDTree(fc).query(fo, workers=-1)
    return d > 1e-5


# ---------------------------------------------------------------------------
# S5: free-space carve field
# ---------------------------------------------------------------------------
def build_carve_field(Rs, ts, slam, lo, dims):
    """모든 카메라에 대해 frustum 내 SLAM 포인트로 ray를 쏘고,
    (MIN_T .. 표면-margin) 구간을 지나는 voxel에 통과 횟수를 누적."""
    transit = np.zeros(int(np.prod(dims)), dtype=np.float32)
    n_cam = len(Rs)
    n_rays_total = 0
    max_steps = int(15.0 / RAY_STEP)
    step_d = (np.arange(max_steps, dtype=np.float32) * RAY_STEP + MIN_T)  # (K,)

    for ci in range(n_cam):
        R, t = Rs[ci], ts[ci]
        C = (-R.T @ t).astype(np.float32)
        pc = slam @ R.T + t                       # (M,3) cam coords
        z = pc[:, 2]
        ok = z > 0.2
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 0) & (u < IMG_W) & (v >= 0) & (v < IMG_H) & (z < 15.0)
        P = slam[ok]                              # (m,3) observed-ish points
        if len(P) == 0:
            continue
        n_rays_total += len(P)
        dvec = P - C
        dist = np.linalg.norm(dvec, axis=1)
        dirs = dvec / dist[:, None]
        t_max = dist - SURF_MARGIN                # 표면 margin 앞까지만 free space
        # samples: (m, K, 3), 유효 = step_d < t_max
        valid = step_d[None, :] < t_max[:, None]  # (m,K)
        pts = C[None, None, :] + step_d[None, :, None] * dirs[:, None, :]
        pts = pts[valid]                          # (n_valid,3)
        idx = np.floor((pts - lo) / VOXEL).astype(np.int64)
        inb = ((idx >= 0) & (idx < dims[None, :])).all(1)
        idx = idx[inb]
        flat = (idx[:, 0] * dims[1] + idx[:, 1]) * dims[2] + idx[:, 2]
        transit += np.bincount(flat, minlength=len(transit)).astype(np.float32)
        if ci % 200 == 0:
            print(f"  cam {ci}/{n_cam}  rays so far {n_rays_total:,}")
    print(f"  total rays {n_rays_total:,}")
    return transit.reshape(tuple(dims))


# ---------------------------------------------------------------------------
# S4/S8: ellipsoidal 변형
# ---------------------------------------------------------------------------
def build_field(anchors, alpha_n, alpha_t, tmin, tnmax, ttmax, k=5):
    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="ball_tree").fit(anchors)
    dists, inds = nbrs.kneighbors(anchors)
    h = dists[:, k].astype(np.float32)
    tn = np.clip(alpha_n * h, tmin, tnmax).astype(np.float32)
    tt = np.clip(alpha_t * h, tmin, ttmax).astype(np.float32)
    fr = np.empty((len(anchors), 3, 3), dtype=np.float32)
    for i in range(len(anchors)):
        X = anchors[inds[i, 1:k + 1]] - anchors[inds[i, 1:k + 1]].mean(0)
        _, ev = np.linalg.eigh((X.T @ X) / max(k - 1, 1))
        fr[i] = np.stack([ev[:, 1], ev[:, 2], ev[:, 0]], 1)
    return tn, tt, fr


def ellip_dmin(xyz, anchors, tn, tt, fr, chunk=2048):
    xt, at = torch.from_numpy(xyz), torch.from_numpy(anchors)
    frt, tnt, ttt = torch.from_numpy(fr), torch.from_numpy(tn), torch.from_numpy(tt)
    out = torch.full((len(xyz),), float("inf"))
    for s in range(0, len(xyz), chunk):
        delta = xt[s:s + chunk][:, None, :] - at[None, :, :]
        c = torch.einsum("cjk,scj->sck", frt, delta)
        d2 = (c[..., 0] / ttt) ** 2 + (c[..., 1] / ttt) ** 2 + (c[..., 2] / tnt) ** 2
        out[s:s + chunk] = d2.sqrt().min(1).values
    return out.numpy()


def plane_normal_dist(xyz, anchors, fr, chunk=4096):
    """최근접 anchor의 국소 평면 법선방향 |거리| (스케일 정규화 없음)."""
    tree = KDTree(anchors)
    _, nn = tree.query(xyz, workers=-1)
    out = np.empty(len(xyz), np.float32)
    for s in range(0, len(xyz), chunk):
        d = xyz[s:s + chunk] - anchors[nn[s:s + chunk]]
        n = fr[nn[s:s + chunk]][:, :, 2]          # 법선 = 3번째 열
        out[s:s + chunk] = np.abs((d * n).sum(1))
    return out


def rankn(x):
    """0..1 rank 정규화."""
    r = np.empty(len(x), np.float64)
    r[np.argsort(x)] = np.arange(len(x))
    return r / (len(x) - 1)


def evaluate(name, score, y, opac, table, higher_is_floater=True):
    s = score if higher_is_floater else -score
    auc = roc_auc_score(y, s)
    row = {"name": name, "auc": auc, "recall_at_fp": {}}
    neg = s[y == 0]
    for fp in (0.005, 0.01, 0.02, 0.05):
        thr = np.quantile(neg, 1 - fp)
        row["recall_at_fp"][f"{fp*100:.1f}%"] = float((s[y == 1] > thr).mean())
    table.append(row)
    r = row["recall_at_fp"]
    print(f"  {name:<16} AUC={auc:.4f}  recall@FP 0.5%={r['0.5%']*100:5.1f}  1%={r['1.0%']*100:5.1f}"
          f"  2%={r['2.0%']*100:5.1f}  5%={r['5.0%']*100:5.1f}")
    return row


def main():
    print("[load] gaussians + labels")
    v = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud.ply"))["vertex"]
    vc = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud_cleaned.ply"))["vertex"]
    deleted = match_deleted(v, vc)
    y = deleted.astype(int)
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1.0 / (1.0 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    print(f"  N={len(xyz):,}  floaters={int(deleted.sum()):,}")

    slam = load_slam()
    dp = np.load(DP_ANCHORS).astype(np.float32)
    Rs, ts = load_cameras()
    centers = np.stack([-R.T @ t for R, t in zip(Rs, ts)]).astype(np.float32)

    scores = {}

    # S1/S2/S3: 거리 계열
    d1, _ = KDTree(slam).query(xyz, workers=-1)
    d5, _ = KDTree(slam).query(xyz, k=5, workers=-1)
    d5 = d5.mean(1)
    ddp, _ = KDTree(dp).query(xyz, workers=-1)
    scores["S1_d_slam_1nn"] = d1
    scores["S2_d_slam_5nn"] = d5
    scores["S3_d_dp_1nn"] = ddp

    # S4: tau 상한 축소 ellipsoidal (음수화: D 클수록 floater)
    for tag, (tn_m, tt_m) in {"cap50": (0.15, 0.30), "cap25": (0.075, 0.15)}.items():
        tn, tt, fr = build_field(dp, 0.4, 0.9, 0.03, tn_m, tt_m)
        scores[f"S4_ellip_{tag}"] = ellip_dmin(xyz, dp, tn, tt, fr)

    # S8: 법선방향 절대거리 (SLAM 기준)
    tnS, ttS, frS = build_field(slam, 0.4, 0.9, 0.03, 0.30, 0.60)
    scores["S8_plane_normal"] = plane_normal_dist(xyz, slam, frS)

    # S5: carve field
    print("[carve] building free-space transit field ...")
    lo = centers.min(0) - np.maximum((centers.max(0) - centers.min(0)), [2., 2., 3.])
    hi = centers.max(0) + np.maximum((centers.max(0) - centers.min(0)), [2., 2., 3.])
    dims = (np.ceil((hi - lo) / VOXEL).astype(int) + 1)
    print(f"  grid {tuple(dims)} ({np.prod(dims):,} voxels)")
    transit = build_carve_field(Rs, ts, slam, lo, dims)
    gi = np.floor((xyz - lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
    carve = np.zeros(len(xyz), np.float32)
    carve[inb] = transit[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    scores["S5_carve"] = carve

    # S6/S7: 결합
    scores["S6_carve_x_d"] = rankn(carve) * rankn(d5)
    scores["S7_carve_x_op"] = rankn(carve) * opac

    # ── 리그 테이블 ────────────────────────────────────────────────────────
    print("\n=== LEAGUE TABLE (floater=positive) ===")
    table = []
    for name, sc in scores.items():
        evaluate(name, sc, y, opac, table)

    # ── prune 시뮬레이션: 상위 3개 score, FP 1%/2% 운영점 ────────────────
    print("\n=== PRUNE SIMULATION ===")
    top3 = sorted(table, key=lambda r: -r["auc"])[:3]
    sims = []
    for row in top3:
        sc = scores[row["name"]]
        for fp in (0.01, 0.02):
            thr = np.quantile(sc[y == 0], 1 - fp)
            mask = sc > thr
            n_del = int(mask.sum())
            tp = int((mask & deleted).sum())
            fpn = int((mask & ~deleted).sum())
            missed = deleted & ~mask
            vis_missed = int((opac[missed] > 0.3).sum())
            fp_op = float(opac[mask & ~deleted].mean()) if fpn else 0.0
            sims.append({"score": row["name"], "fp_budget": fp, "threshold": float(thr),
                         "pruned": n_del, "floater_recall": tp / int(deleted.sum()),
                         "surface_deleted": fpn, "surface_deleted_mean_opacity": fp_op,
                         "missed_visible_floaters(op>0.3)": vis_missed})
            print(f"  {row['name']:<16} FP={fp*100:.0f}%: prune {n_del:>6,}  "
                  f"floater recall {tp/int(deleted.sum())*100:5.1f}%  표면 오삭제 {fpn:,} "
                  f"(mean op {fp_op:.3f})  놓친 가시 floater {vis_missed}")

    out = BASE / "loss_candidate_league.json"
    json.dump({"league": table, "prune_sim": sims}, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()
