#!/usr/bin/env python3
"""
verify_plateau_capability.py
============================
학습 없이 순수 분석으로, 사용자가 SuperSplat으로 직접 삭제한 2,817개 manual floater를
현재 plateau loss 방식(및 그 변형들)이 원리적으로 해결할 수 있는지 검증한다.

검증 항목:
 1. 실제 학습에 쓰인 plateau field(DepthPro anchor + ellipsoidal per-anchor tau)를
    PlateauLoss.__init__와 동일하게 재구성하고, floater별 정규화 거리 D_min 계산.
 2. floater가 plateau 경계(D=1)까지 이동해야 하는 실제 유클리드 거리(gap) 계산.
 3. Adam LR 스케줄 적분으로 "이론상 최대 변위" (λ→∞에서도 넘을 수 없는 상한) 계산.
 4. 측정된 per-step plateau:RGB gradient 비율로 현실적 drift 추정 → gap과 비교.
 5. Counterfactual: enlarged tau / λ 스케일 / exp_loss kernel / opacity_weight 각각의
    도달 가능성 재계산.

사용 예:
  python scripts/analysis/verify_plateau_capability.py \
    --orig results/experiments/exp32_lineage_diag/point_cloud/iteration_30000/point_cloud.ply \
    --cleaned results/experiments/exp32_lineage_diag/point_cloud/iteration_30000/point_cloud_cleaned.ply \
    --anchors results/diagnostic/native_anchors_neworb_v4_20260709_204706/anchors_all_depth_pro.npy \
    --cameras results/experiments/exp32_lineage_diag/cameras.json \
    --out results/experiments/exp32_lineage_diag/plateau_capability_report.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from plyfile import PlyData
from scipy.spatial import KDTree
from sklearn.neighbors import NearestNeighbors

# ---------------------------------------------------------------------------
# exp32 실제 학습 설정 (configs/plateau_loss/orb_depthpro_v4_native.yaml)
# ---------------------------------------------------------------------------
BASE_CFG = dict(knn_k=5, alpha_n=0.4, alpha_t=0.9,
                tau_min=0.03, tau_n_max=0.30, tau_t_max=0.60,
                start_iter=5000, lam=0.01, sample_size=8192)
# exp33 (orb_depthpro_tau_enlarged_native.yaml)
ENLARGED_CFG = dict(knn_k=5, alpha_n=0.8, alpha_t=1.8,
                    tau_min=0.03, tau_n_max=0.80, tau_t_max=2.00,
                    start_iter=7000, lam=0.10, sample_size=8192)

# 3DGS optimizer defaults (arguments/__init__.py)
POS_LR_INIT, POS_LR_FINAL, LR_MAX_STEPS = 0.00016, 0.0000016, 30000
OPACITY_LR = 0.025
TOTAL_ITERS = 30000


def load_ply(path):
    return PlyData.read(str(path))["vertex"]


def match_deleted(v_orig, v_clean):
    """SuperSplat 편집 후 남은 점과 색-feature KD-tree 매칭 → 삭제된 점 마스크."""
    fo = np.stack([np.asarray(v_orig[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    fc = np.stack([np.asarray(v_clean[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
    d, _ = KDTree(fc).query(fo, workers=-1)
    return d > 1e-5


def build_plateau_field(anchors, cfg):
    """PlateauLoss.__init__ + _compute_ellipsoid 재현 (knn_iso_mult=0)."""
    k = cfg["knn_k"]
    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="ball_tree").fit(anchors)
    dists, inds = nbrs.kneighbors(anchors)
    h_j = dists[:, k].astype(np.float32)
    tau_n = np.clip(cfg["alpha_n"] * h_j, cfg["tau_min"], cfg["tau_n_max"]).astype(np.float32)
    tau_t = np.clip(cfg["alpha_t"] * h_j, cfg["tau_min"], cfg["tau_t_max"]).astype(np.float32)
    N = len(anchors)
    frames = np.empty((N, 3, 3), dtype=np.float32)
    for i in range(N):
        neigh = anchors[inds[i, 1:k + 1]]
        X = neigh - neigh.mean(0)
        cov = (X.T @ X) / max(k - 1, 1)
        _, evec = np.linalg.eigh(cov)
        frames[i] = np.stack([evec[:, 1], evec[:, 2], evec[:, 0]], axis=1)
    return tau_n, tau_t, frames


def ellipsoidal_dmin(xyz, anchors, frames, tau_n, tau_t, chunk=2048):
    """모든 Gaussian에 대해 D_min, argmin anchor, ||dD/dx||, 유클리드 d_min 계산."""
    xyz_t = torch.from_numpy(xyz)
    a_t = torch.from_numpy(anchors)
    fr_t = torch.from_numpy(frames)
    tn_t = torch.from_numpy(tau_n)
    tt_t = torch.from_numpy(tau_t)

    n = xyz.shape[0]
    D_min = torch.full((n,), float("inf"))
    argmin = torch.zeros(n, dtype=torch.long)
    for s in range(0, n, chunk):
        xs = xyz_t[s:s + chunk]                          # (S,3)
        delta = xs[:, None, :] - a_t[None, :, :]         # (S,M,3)
        c = torch.einsum("cjk,scj->sck", fr_t, delta)    # (S,M,3) proj [u_t1,u_t2,u_n]
        d2 = (c[..., 0] / tt_t) ** 2 + (c[..., 1] / tt_t) ** 2 + (c[..., 2] / tn_t) ** 2
        d = d2.sqrt()                                    # (S,M)
        mn, am = d.min(dim=1)
        D_min[s:s + chunk] = mn
        argmin[s:s + chunk] = am

    # argmin anchor 기준의 grad norm / 유클리드 거리 (chunked)
    grad_norm = torch.zeros(n)
    d_euc = torch.zeros(n)
    for s in range(0, n, chunk):
        xs = xyz_t[s:s + chunk]
        am = argmin[s:s + chunk]
        a_sel = a_t[am]                                   # (S,3)
        delta = xs - a_sel                                # (S,3)
        d_euc[s:s + chunk] = delta.norm(dim=1)
        fr_sel = fr_t[am]                                 # (S,3,3) cols [u_t1,u_t2,u_n]
        c = torch.einsum("sjk,sj->sk", fr_sel, delta)     # (S,3)
        tau = torch.stack([tt_t[am], tt_t[am], tn_t[am]], dim=1)  # (S,3)
        D = D_min[s:s + chunk].clamp(min=1e-12)
        # dD/dx = (1/D) * Σ_k (c_k/τ_k²) u_k → norm = (1/D)·||c/τ²||
        grad_norm[s:s + chunk] = (c / tau ** 2).norm(dim=1) / D
    return D_min.numpy(), argmin.numpy(), grad_norm.numpy(), d_euc.numpy()


def lr_at(t, spatial_scale):
    """3DGS get_expon_lr_func (delay_steps=0) 재현."""
    frac = np.clip(t / LR_MAX_STEPS, 0, 1)
    return spatial_scale * np.exp(np.log(POS_LR_INIT) * (1 - frac) + np.log(POS_LR_FINAL) * frac)


def cameras_extent(cameras_json):
    cams = json.loads(Path(cameras_json).read_text())
    pos = np.array([c["position"] for c in cams], dtype=np.float64)
    center = pos.mean(0)
    return float(1.1 * np.linalg.norm(pos - center, axis=1).max())


def pct(x):
    return float(100.0 * x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", required=True)
    ap.add_argument("--cleaned", required=True)
    ap.add_argument("--anchors", required=True)
    ap.add_argument("--cameras", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    v_orig = load_ply(args.orig)
    v_clean = load_ply(args.cleaned)
    deleted = match_deleted(v_orig, v_clean)
    n_del = int(deleted.sum())
    print(f"[match] deleted floaters: {n_del:,} / {len(v_orig):,}")

    xyz = np.stack([np.asarray(v_orig[k]) for k in "xyz"], 1).astype(np.float32)
    birth = np.asarray(v_orig["birth_step"]).astype(np.int32)
    acc_rgb = np.asarray(v_orig["accum_rgb_grad"]).astype(np.float64)
    acc_plat = np.asarray(v_orig["accum_plateau_grad"]).astype(np.float64)
    opac = 1.0 / (1.0 + np.exp(-np.asarray(v_orig["opacity"], dtype=np.float64)))

    anchors = np.load(args.anchors).astype(np.float32)
    extent = cameras_extent(args.cameras)
    print(f"[scene] anchors={len(anchors):,}  cameras_extent={extent:.3f} m")

    N_total = len(xyz)
    report = {"n_total": N_total, "n_floaters": n_del, "cameras_extent_m": extent,
              "fields": {}}

    # ── Adam 이동량 상한: Σ lr(t), t=start_iter..30k ───────────────────────
    # Adam step 크기 상한 ≈ lr (m̂/√v̂ ≤ ~1, 완전히 일관된 gradient일 때).
    # 즉 λ를 아무리 키워도 plateau가 floater를 끌 수 있는 최대 거리.
    iters = np.arange(0, TOTAL_ITERS)
    lr_curve = lr_at(iters, extent)
    for name, cfg in (("base", BASE_CFG), ("enlarged", ENLARGED_CFG)):
        s = cfg["start_iter"]
        cfg["_max_disp"] = float(lr_curve[s:].sum())
    print(f"[adam] max coherent displacement  base(5k→30k)={BASE_CFG['_max_disp']:.3f} m"
          f"  enlarged(7k→30k)={ENLARGED_CFG['_max_disp']:.3f} m")

    # ── plateau field별 분석 ────────────────────────────────────────────────
    for name, cfg in (("base", BASE_CFG), ("enlarged", ENLARGED_CFG)):
        print(f"\n[field:{name}] building tau field...")
        tau_n, tau_t, frames = build_plateau_field(anchors, cfg)
        print(f"  tau_n: median={np.median(tau_n):.3f} max={tau_n.max():.3f} | "
              f"tau_t: median={np.median(tau_t):.3f} max={tau_t.max():.3f}")
        D, am, gnorm, d_euc = ellipsoidal_dmin(xyz, anchors, frames, tau_n, tau_t)

        fD, fg, fd = D[deleted], gnorm[deleted], d_euc[deleted]
        sD = D[~deleted]
        hinge = np.clip(fD - 1.0, 0, None)
        inside = fD <= 1.0
        # 경계까지 이동해야 하는 유클리드 거리: argmin anchor 중심 방향 직선 경로 기준
        gap = fd * np.clip(1.0 - 1.0 / np.clip(fD, 1e-9, None), 0, None)

        S, lam = cfg["sample_size"], cfg["lam"]
        # per-iteration 기대 raw gradient (cyclic sampler: S/N 확률로 히트, 히트 시 /S)
        # → E[|g|] = λ·2·hinge·||dD/dx|| / N
        per_iter_grad = lam * 2.0 * hinge * fg / N_total

        # 현실적 drift: Adam은 g/√E[g²]로 정규화 → plateau 방향의 일관 성분 비율
        #   ratio ≈ plateau_grad / rgb_grad (측정 lifetime 누적치, 둘 다 같은 파라미터)
        n_alive = np.maximum(TOTAL_ITERS - birth[deleted], 1)
        meas_ratio = acc_plat[deleted] / np.clip(acc_rgb[deleted], 1e-12, None)
        # start_iter 이후 lr 적분 × ratio = 예상 순 drift
        drift = cfg["_max_disp"] * meas_ratio

        reachable_inf_lambda = gap < cfg["_max_disp"]     # λ→∞ 이상적 상한으로도 도달?
        reachable_realistic = gap < drift                  # 측정 ratio 기준 실제 drift로 도달?

        fld = {
            "cfg": {k: v for k, v in cfg.items() if not k.startswith("_")},
            "adam_max_coherent_disp_m": cfg["_max_disp"],
            "D_min": {"floater_median": float(np.median(fD)),
                      "floater_mean": float(fD.mean()),
                      "floater_p90": float(np.percentile(fD, 90)),
                      "surface_median": float(np.median(sD)),
                      "surface_inside_ratio_pct": pct((sD <= 1).mean())},
            "floaters_inside_plateau_pct": pct(inside.mean()),
            "floaters_inside_count": int(inside.sum()),
            "gap_to_boundary_m": {"median": float(np.median(gap)),
                                  "mean": float(gap.mean()),
                                  "p10": float(np.percentile(gap, 10)),
                                  "p90": float(np.percentile(gap, 90)),
                                  "max": float(gap.max())},
            "per_iter_grad_expected": {"median": float(np.median(per_iter_grad)),
                                       "mean": float(per_iter_grad.mean())},
            "measured_plat_to_rgb_ratio": {"median": float(np.median(meas_ratio)),
                                           "mean": float(meas_ratio.mean())},
            "predicted_drift_m": {"median": float(np.median(drift)),
                                  "mean": float(drift.mean()),
                                  "p90": float(np.percentile(drift, 90))},
            "reachable_at_infinite_lambda_pct": pct(reachable_inf_lambda.mean()),
            "reachable_realistic_pct": pct(reachable_realistic.mean()),
        }

        # λ 스케일 counterfactual: drift ∝ λ (ratio가 λ에 선형이라 가정, ratio<<1 영역)
        lam_needed = np.full(n_del, np.inf)
        ok = (drift > 0) & (gap > 0)
        lam_needed[ok] = lam * gap[ok] / drift[ok]
        lam_needed[gap <= 0] = 0.0
        fld["lambda_needed_to_reach"] = {
            "median": float(np.median(lam_needed[np.isfinite(lam_needed)])) if np.isfinite(lam_needed).any() else None,
            "pct_needing_lambda_le_1": pct((lam_needed <= 1.0).mean()),
            "pct_needing_lambda_le_10": pct((lam_needed <= 10.0).mean()),
            "note": "단, λ 증가는 표면 Gaussian에도 동일 배율 적용 (exp26: λ=1.0에서 이미 -0.31dB)"
        }

        # exp_loss counterfactual: kernel 교체 시 hinge 지점 gradient 배율
        #   quad: 2·hinge  /  exp: exp(min(hinge,8))
        with np.errstate(over="ignore"):
            boost = np.exp(np.minimum(hinge, 8.0)) / np.clip(2.0 * hinge, 1e-12, None)
        boost = np.where(hinge > 0, boost, 0.0)
        fld["exp_loss_grad_boost"] = {"median": float(np.median(boost[hinge > 0])) if (hinge > 0).any() else 0.0,
                                      "p90": float(np.percentile(boost[hinge > 0], 90)) if (hinge > 0).any() else 0.0}

        # opacity_weight counterfactual: ∂L/∂opacity = λ·hinge²/N per iter (기대값)
        # opacity가 σ(x)라 raw param grad는 ·σ(1-σ); Adam+lr0.025로 일관 하강 시
        # per-iter 최대 -0.025 (raw). floater 평균 opacity에서 prune(0.01)까지 필요 스텝.
        op_f = opac[deleted]
        fld["opacity_weight_note"] = {
            "floater_opacity_median": float(np.median(op_f)),
            "per_iter_opacity_grad_expected": float(np.median(lam * hinge ** 2 / N_total)),
            "rgb_side_pressure": "floater RGB grad는 표면의 2.23배 — opacity를 되올리는 방향으로 경쟁"
        }
        report["fields"][name] = fld

        print(f"  D_min(floater): median={fld['D_min']['floater_median']:.2f}  "
              f"inside={fld['floaters_inside_plateau_pct']:.2f}%")
        print(f"  gap→boundary: median={fld['gap_to_boundary_m']['median']:.3f} m  "
              f"p90={fld['gap_to_boundary_m']['p90']:.3f} m")
        print(f"  predicted drift: median={fld['predicted_drift_m']['median']:.5f} m")
        print(f"  reachable @λ=∞(상한): {fld['reachable_at_infinite_lambda_pct']:.1f}%  "
              f"| realistic: {fld['reachable_realistic_pct']:.1f}%")

    # ── 타이밍: plateau 활성 전 출생 비율 ──────────────────────────────────
    fb = birth[deleted]
    report["timing"] = {
        "born_before_5000_pct": pct((fb < 5000).mean()),
        "born_before_7000_pct": pct((fb < 7000).mean()),
        "note": "plateau는 출생(split)을 막지 못함 — densify는 RGB viewspace grad 기준"
    }

    # ── 구조적 한계 요약 ───────────────────────────────────────────────────
    report["structural_limits"] = [
        "base 설정은 opacity로의 gradient 경로가 없음 → floater를 '삭제'할 수 없고 '이동'만 가능",
        "loss가 sample mean → per-point 유효 λ = λ/N (N=149k): floater 개별 gradient가 1/N로 희석",
        "cyclic sampler(8192/149k) → 각 floater는 ~18 iter에 1회만 히트",
        "이동에 성공해도 floater는 표면 위 잘못된 색상 blob으로 남음 (제거 아님)",
    ]

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n[saved] {args.out}")


if __name__ == "__main__":
    main()
