#!/usr/bin/env python3
"""
extract_floaters_rulebase.py
============================
수동 라벨(2,817개)로 캘리브레이션된 룰베이스 floater 자동 추출기.
301_1253 dataset의 아무 run 결과 ply에 적용 가능 (ORB/MPS 트랙 모두).

규칙 (rounds/round8_carve_loss_design.md에서 검증):
    score = w(x) · (1 − maxop_5cm(x))
      w(x) = ρ(x) · min(d5_SLAM(x)/0.25, 1),  ρ = 빈공간 증거비 (사전 계산 field)
    score 내림차순으로 선택하되, 선택된 점들의 누적 시각 기여량이
    (전체의) budget에 닿으면 중단 — 표면 피해 상한 보장.

운영점 프리셋 (exp32 라벨 기준 실측):
    --preset safe        budget 0.75% → recall ~55%, 실제 표면 기여손실 ~0.5%
    --preset balanced    budget 1.5%  → recall ~69%, 손실 ~1.1% (기본값)
    --preset aggressive  budget 3.0%  → recall ~80%대, SuperSplat 검수 전제

출력 (--out-dir, 기본 ply 옆 rulebase_floaters/):
    floater_mask.npy            원본 ply 순서의 bool 마스크
    point_cloud_cleaned.ply     floater 제거본
    floaters_only.ply           floater만 (SuperSplat 검수용)
    report.json                 개수·기여량·(라벨 있으면) recall/precision

사용:
    python scripts/analysis/extract_floaters_rulebase.py \
        --ply <run>/point_cloud/iteration_30000/point_cloud.ply \
        [--track orb|mps] [--preset balanced] [--labels <cleaned.ply>]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter

ROOT = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
FIELDS = {
    "orb": ROOT / "results/experiments/exp32_lineage_diag/carve_fields.npz",
    "mps": ROOT / "results/diagnostic/mps_carve_field.npz",
}
SLAM_TXT = {
    "orb": ROOT / "data/03_rgb_3dgs_full/sparse/0/points3D.txt",
    "mps": Path("/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets"
                "/aria_mps_2dgs/0416_Data__0416_301-1253/sparse/0/points3D.txt"),
}
PRESETS = {"safe": 0.0075, "balanced": 0.015, "aggressive": 0.03}
VOXEL = 0.10
D5_TAU = 0.25
MAXOP_R = 0.05
SCORE_MIN = 0.3
ANCHOR_TERM_MIN_MPS = 10.0   # MPS semidense outlier(7.6%) 차단


def load_points3d(path):
    pts = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        t = line.split()
        if len(t) >= 7:
            pts.append([float(t[1]), float(t[2]), float(t[3])])
    return np.array(pts, np.float32)


def champion_score(xyz, opac, track):
    z = np.load(FIELDS[track])
    ts = uniform_filter(z["transit"], 3)
    es = uniform_filter(z["terminal"], 3)
    ratio = ts / (ts + 3.0 * es + 1e-6)
    lo, dims = z["lo"], z["dims"]

    def grid(field, p):
        gi = np.floor((p - lo) / VOXEL).astype(np.int64)
        inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
        out = np.zeros(len(p), np.float32)
        out[inb] = field[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
        return out

    anchors = load_points3d(SLAM_TXT[track])
    if track == "mps":
        ev = grid(es, anchors)
        anchors = anchors[ev > ANCHOR_TERM_MIN_MPS]

    rho = grid(ratio, xyz)
    d5, _ = cKDTree(anchors).query(xyz, k=5, workers=-1)
    w = rho * np.clip(d5.mean(1) / D5_TAU, 0, 1)
    pairs = cKDTree(xyz).query_ball_point(xyz, MAXOP_R, workers=-1, return_sorted=False)
    maxop = np.fromiter((opac[p].max() for p in pairs), dtype=np.float64, count=len(xyz))
    return w * (1.0 - maxop)


def extract(ply_path, track, budget, out_dir, labels_path=None):
    ply = PlyData.read(str(ply_path))
    v = ply["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1).astype(np.float64))
    try:
        visn = np.clip(np.asarray(v["accum_visibility"]).astype(np.float64), 1, None)
    except Exception:
        visn = np.ones(len(xyz))
    contrib = opac * np.sort(scales, 1)[:, 1:].prod(1) * visn
    total = contrib.sum()

    print(f"[score] {len(xyz):,} gaussians, track={track} ...")
    s = champion_score(xyz, opac, track)

    order = np.argsort(-s)
    eligible = s[order] > SCORE_MIN
    csum = np.cumsum(np.where(eligible, contrib[order], 0)) / total
    k = int((eligible & (csum <= budget)).sum())
    mask = np.zeros(len(xyz), bool)
    mask[order[:k]] = True

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "floater_mask.npy", mask)
    PlyData([PlyElement.describe(v.data[~mask], "vertex")]).write(str(out_dir / "point_cloud_cleaned.ply"))
    PlyData([PlyElement.describe(v.data[mask], "vertex")]).write(str(out_dir / "floaters_only.ply"))

    report = {
        "ply": str(ply_path), "track": track, "budget": budget,
        "n_total": len(xyz), "n_extracted": int(mask.sum()),
        "extracted_contrib_pct": float(contrib[mask].sum() / total * 100),
        "extracted_visible(op>0.3)": int((mask & (opac > 0.3)).sum()),
        "score_min": SCORE_MIN,
    }

    if labels_path:
        # 라벨(cleaned ply)과 대조 — SuperSplat 좌표 변환 때문에 색 feature 매칭 (pitfalls 참조)
        vc = PlyData.read(str(labels_path))["vertex"]
        fo = np.stack([np.asarray(v[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
        fc = np.stack([np.asarray(vc[k]) for k in ("f_dc_0", "f_dc_1", "f_dc_2")], 1).astype(np.float32)
        d, _ = cKDTree(fc).query(fo, workers=-1)
        gt = d > 1e-5
        tp = int((mask & gt).sum())
        report["labels"] = {
            "n_gt_floaters": int(gt.sum()),
            "recall": tp / max(int(gt.sum()), 1),
            "precision_vs_labels": tp / max(int(mask.sum()), 1),
            "note": "precision은 하한 — 라벨이 저op 먼지에 불완전 (patch_evidence 참조)",
            "true_surface_harm_pct": float(contrib[mask & ~gt].sum() / total * 100),
        }

    json.dump(report, open(out_dir / "report.json", "w"), indent=2, ensure_ascii=False)
    print(f"[done] {report['n_extracted']:,}개 추출 ({report['extracted_contrib_pct']:.2f}% 기여, "
          f"가시 {report['extracted_visible(op>0.3)']:,}) → {out_dir}")
    if "labels" in report:
        L = report["labels"]
        print(f"[labels] recall {L['recall']*100:.1f}%  표면측 기여손실 {L['true_surface_harm_pct']:.3f}% "
              f"(라벨 불완전으로 과대평가)")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ply", required=True)
    ap.add_argument("--track", choices=["orb", "mps"], default="orb")
    ap.add_argument("--preset", choices=list(PRESETS), default="balanced")
    ap.add_argument("--budget", type=float, default=None, help="프리셋 대신 직접 지정 (기여량 비율)")
    ap.add_argument("--labels", default=None, help="수동 cleaned ply (있으면 recall 검증)")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    budget = args.budget if args.budget is not None else PRESETS[args.preset]
    ply_path = Path(args.ply)
    out_dir = Path(args.out_dir) if args.out_dir else ply_path.parent / "rulebase_floaters"
    extract(ply_path, args.track, budget, out_dir, args.labels)


if __name__ == "__main__":
    main()
