#!/usr/bin/env python3
"""
design_floater_loss_round2.py
=============================
Round 1 승자(carve × d_slam)를 기반으로 한 공격적 개선 라운드.

추가 후보:
  R1 carve_ratio      : transit / (transit + k·terminal) — "이 voxel을 지나간 ray" 대
                        "이 voxel에서 끝난 ray"의 증거비 → 빈 공간 확률화 (NeRF 스타일)
  R2 carve_smooth     : 3³ 이웃 평균으로 voxel 양자화 완화
  R3 ratio_x_d        : R1 × d_slam_5nn (rank 곱)
  R4 triple           : carve × d_slam_5nn × plane_normal (3중 rank 곱)
  R5 logit_oracle     : [carve, d5, plane_n, ddp] 로지스틱 회귀 (이 장면 재대입 AUC —
                        결합의 이론적 상한 가늠용, loss 설계엔 직접 사용 불가)
  R6 ratio_smooth_x_d : R1+R2 결합 × d5 — 최종 후보

실전 지표: "가시(opacity>0.3) floater recall" & "가시 표면 오삭제율" — 사용자가
실제로 보고 지운 대상 기준.
"""
import json
from pathlib import Path
import sys

import numpy as np
from plyfile import PlyData
from scipy.spatial import KDTree
from scipy.ndimage import uniform_filter
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).parent))
from design_floater_loss_candidates import (
    ROOT, BASE, DP_ANCHORS, VOXEL, RAY_STEP, SURF_MARGIN, MIN_T,
    IMG_W, IMG_H, FX, FY, CX, CY,
    load_cameras, load_slam, match_deleted, build_field, plane_normal_dist, rankn,
)


def build_carve_and_terminal(Rs, ts, slam, lo, dims):
    """transit(통과) + terminal(종단: anchor 주변 ±margin 구간) 두 field 동시 구축."""
    n_vox = int(np.prod(dims))
    transit = np.zeros(n_vox, dtype=np.float32)
    terminal = np.zeros(n_vox, dtype=np.float32)
    max_steps = int(15.0 / RAY_STEP)
    step_d = (np.arange(max_steps, dtype=np.float32) * RAY_STEP + MIN_T)

    def deposit(pts, acc):
        idx = np.floor((pts - lo) / VOXEL).astype(np.int64)
        inb = ((idx >= 0) & (idx < dims[None, :])).all(1)
        idx = idx[inb]
        flat = (idx[:, 0] * dims[1] + idx[:, 1]) * dims[2] + idx[:, 2]
        acc += np.bincount(flat, minlength=n_vox).astype(np.float32)

    for ci in range(len(Rs)):
        R, t = Rs[ci], ts[ci]
        C = (-R.T @ t).astype(np.float32)
        pc = slam @ R.T + t
        z = pc[:, 2]
        ok = z > 0.2
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 0) & (u < IMG_W) & (v >= 0) & (v < IMG_H) & (z < 15.0)
        P = slam[ok]
        if len(P) == 0:
            continue
        dvec = P - C
        dist = np.linalg.norm(dvec, axis=1)
        dirs = dvec / dist[:, None]
        # 통과 구간: MIN_T .. dist-margin
        valid = step_d[None, :] < (dist - SURF_MARGIN)[:, None]
        pts = C[None, None, :] + step_d[None, :, None] * dirs[:, None, :]
        deposit(pts[valid], transit)
        # 종단 구간: dist-margin .. dist+margin (표면 증거)
        term_off = np.linspace(-SURF_MARGIN, SURF_MARGIN, 5, dtype=np.float32)
        tpts = C[None, None, :] + (dist[:, None] + term_off[None, :])[:, :, None] * dirs[:, None, :]
        deposit(tpts.reshape(-1, 3), terminal)
        if ci % 300 == 0:
            print(f"  cam {ci}/{len(Rs)}")
    return transit.reshape(tuple(dims)), terminal.reshape(tuple(dims))


def lookup(field, xyz, lo, dims):
    gi = np.floor((xyz - lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
    out = np.zeros(len(xyz), np.float32)
    out[inb] = field[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    return out


def evaluate(name, s, y, opac, table):
    auc = roc_auc_score(y, s)
    neg = s[y == 0]
    vis_f = (y == 1) & (opac > 0.3)          # 가시 floater
    vis_s = (y == 0) & (opac > 0.3)          # 가시 표면
    row = {"name": name, "auc": auc, "recall_at_fp": {}, "visible_recall_at_visfp": {}}
    for fp in (0.005, 0.01, 0.02, 0.05):
        thr = np.quantile(neg, 1 - fp)
        row["recall_at_fp"][f"{fp*100:.1f}%"] = float((s[y == 1] > thr).mean())
    # 가시 기준: 가시 표면 오삭제율을 고정하고 가시 floater recall 측정
    for fp in (0.005, 0.01, 0.02):
        thr = np.quantile(s[vis_s], 1 - fp)
        row["visible_recall_at_visfp"][f"{fp*100:.1f}%"] = float((s[vis_f] > thr).mean())
    table.append(row)
    r, vr = row["recall_at_fp"], row["visible_recall_at_visfp"]
    print(f"  {name:<18} AUC={auc:.4f}  recall@FP 0.5/1/2/5%= "
          f"{r['0.5%']*100:5.1f} {r['1.0%']*100:5.1f} {r['2.0%']*100:5.1f} {r['5.0%']*100:5.1f}"
          f"  | 가시 recall@visFP 0.5/1/2%= {vr['0.5%']*100:5.1f} {vr['1.0%']*100:5.1f} {vr['2.0%']*100:5.1f}")
    return row


def main():
    print("[load]")
    v = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud.ply"))["vertex"]
    vc = PlyData.read(str(BASE / "point_cloud/iteration_30000/point_cloud_cleaned.ply"))["vertex"]
    deleted = match_deleted(v, vc)
    y = deleted.astype(int)
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1.0 / (1.0 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))

    slam = load_slam()
    dp = np.load(DP_ANCHORS).astype(np.float32)
    Rs, ts = load_cameras()
    centers = np.stack([-R.T @ t for R, t in zip(Rs, ts)]).astype(np.float32)
    lo = centers.min(0) - np.maximum((centers.max(0) - centers.min(0)), [2., 2., 3.])
    hi = centers.max(0) + np.maximum((centers.max(0) - centers.min(0)), [2., 2., 3.])
    dims = (np.ceil((hi - lo) / VOXEL).astype(int) + 1)

    cache = BASE / "carve_fields.npz"
    if cache.exists():
        z = np.load(cache)
        transit, terminal = z["transit"], z["terminal"]
        print("  carve fields loaded from cache")
    else:
        print("[carve] building transit+terminal fields ...")
        transit, terminal = build_carve_and_terminal(Rs, ts, slam, lo, dims)
        np.savez_compressed(cache, transit=transit, terminal=terminal, lo=lo, dims=dims)
        print(f"  cached → {cache}")

    # 거리 신호
    d5, _ = KDTree(slam).query(xyz, k=5, workers=-1)
    d5 = d5.mean(1)
    ddp, _ = KDTree(dp).query(xyz, workers=-1)
    _, _, frS = build_field(slam, 0.4, 0.9, 0.03, 0.30, 0.60)
    pn = plane_normal_dist(xyz, slam, frS)

    carve_raw = lookup(transit, xyz, lo, dims)
    term_raw = lookup(terminal, xyz, lo, dims)

    # R1: 증거비 (k=3: 종단 5샘플 촘촘함 보정)
    ratio = carve_raw / (carve_raw + 3.0 * term_raw + 1e-6)
    # R2: smoothing
    transit_s = uniform_filter(transit, size=3)
    terminal_s = uniform_filter(terminal, size=3)
    carve_sm = lookup(transit_s, xyz, lo, dims)
    term_sm = lookup(terminal_s, xyz, lo, dims)
    ratio_sm = carve_sm / (carve_sm + 3.0 * term_sm + 1e-6)

    scores = {
        "S6_carve_x_d(재현)": rankn(carve_raw) * rankn(d5),
        "R1_carve_ratio": ratio,
        "R2_ratio_smooth": ratio_sm,
        "R3_ratio_x_d": rankn(ratio) * rankn(d5),
        "R4_triple": rankn(carve_raw) * rankn(d5) * rankn(pn),
        "R6_ratioSm_x_d": rankn(ratio_sm) * rankn(d5),
        "R7_ratioSm_x_carve_x_d": rankn(ratio_sm) * rankn(carve_sm) * rankn(d5),
    }

    # R5: oracle logistic (재대입 — 상한 가늠)
    X = np.stack([rankn(carve_sm), rankn(ratio_sm), rankn(d5), rankn(pn), rankn(ddp)], 1)
    lr = LogisticRegression(max_iter=1000, class_weight="balanced").fit(X, y)
    scores["R5_logit_oracle"] = lr.decision_function(X)
    print(f"  [oracle] logit coefs: {dict(zip(['carve','ratio','d5','plane_n','ddp'], lr.coef_[0].round(2)))}")

    print("\n=== ROUND 2 LEAGUE ===")
    table = []
    for name, sc in scores.items():
        evaluate(name, sc, y, opac, table)

    # 최고 비-oracle 후보로 prune 시뮬레이션 (가시 기준)
    best = max((r for r in table if "oracle" not in r["name"]), key=lambda r: r["auc"])
    sc = scores[best["name"]]
    print(f"\n=== PRUNE SIM: {best['name']} (가시 기준) ===")
    vis_s = (y == 0) & (opac > 0.3)
    sims = []
    for fp in (0.002, 0.005, 0.01, 0.02):
        thr = np.quantile(sc[vis_s], 1 - fp)
        mask = sc > thr
        tp_vis = int((mask & deleted & (opac > 0.3)).sum())
        n_vis_f = int((deleted & (opac > 0.3)).sum())
        fp_vis = int((mask & ~deleted & (opac > 0.3)).sum())
        sims.append({"score": best["name"], "vis_fp": fp, "pruned_total": int(mask.sum()),
                     "visible_floater_recall": tp_vis / n_vis_f,
                     "visible_surface_deleted": fp_vis})
        print(f"  visFP={fp*100:.1f}%: prune {int(mask.sum()):>6,}  가시 floater recall "
              f"{tp_vis/n_vis_f*100:5.1f}% ({tp_vis}/{n_vis_f})  가시 표면 오삭제 {fp_vis:,}")

    out = BASE / "loss_candidate_round2.json"
    json.dump({"league": table, "prune_sim": sims}, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()
