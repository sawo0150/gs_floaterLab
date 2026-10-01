#!/usr/bin/env python3
"""Collect measured endpoints and input provenance without importing a mapper.

Each protocol remains distinct. In particular, D3 proxy renders are additional
work and FIFO runs are end-to-end comparisons with recorded tracking settings.
"""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "results/campaigns/gain_attribution"
OUT = RESULTS / "cvpr_assets/collection_v1"
MAIN = Path("/home/intern/VIGS-SLAM-custom")
ARCHIVES = ROOT / "results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/official_22ffe24_trt"
MANIFESTS = ROOT / "context/experiments/exp78/b_strict_fair_comparison/manifests"
CANDIDATES = {
    "rpng": [f"table_{i:02d}" for i in range(1, 9)],
    "utmm": ["ego-centric-1", "ego-centric-2", "ego-drive", "fast-straight", "slow-straight-1", "slow-straight-2", "square-1", "square-2"],
    "aria": ["aria1253", "aria1253rot", "aria301_12F", "aria301_305"],
}
KEYS = {"aria": ("aria", "aria1253"), "rot": ("aria", "aria1253rot"), "rpng": ("rpng", "table_06"), "utmm": ("utmm", "square-1")}


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2, default=str) + "\n")


def csv_write(p, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)


def inventory():
    rows = []
    for dataset, scenes in CANDIDATES.items():
        for scene in scenes:
            archive = ARCHIVES / dataset / scene / "seed0"
            manifest = MANIFESTS / f"{dataset}_{scene}.json"
            if scene == "aria1253rot":
                base = RESULTS / "main_validation/rot_inputs"
                archive, manifest = base / "archive", base / "heldout.json"
            elif scene == "aria301_12F":
                base = RESULTS / "cvpr_assets/inputs/aria301_12F"
                archive, manifest = base / "archive", base / "heldout.json"
            p = archive / "archive_manifest.json"
            row = {"dataset": dataset, "scene": scene, "archive": str(archive), "archive_exists": p.is_file(), "fixed_manifest": str(manifest), "fixed_manifest_exists": manifest.is_file()}
            if p.is_file():
                m = read(p)
                arrivals = [json.loads(s) for s in (archive / m["arrivals"]).read_text().splitlines() if s.strip()]
                fallback_imu = Path(m["input_image_directory"]).parent / ("imu.txt" if dataset == "rpng" else "imu_ours.txt")
                row.update(archive_sha256=sha(p), archive_schema=m["schema_version"], input_frames=len(arrivals), heldout_frames=sum(bool(x["held_out"]) for x in arrivals), sensor_seconds=float(arrivals[-1]["sensor_timestamp"])-float(arrivals[0]["sensor_timestamp"]), events=len(m["events"]), image_dir=m["input_image_directory"], calibration=m["input_calibration"], imu=m.get("input_imu", str(fallback_imu)), imu_path_in_archive="input_imu" in m, input_config=m["input_config"])
                paths = [Path(row[x]) for x in ["image_dir", "calibration", "imu", "input_config"]]
                row["raw_inputs_exist"] = all(x.exists() for x in paths)
                validation = archive / "validation.json"
                row["archive_validation"] = str(validation) if validation.exists() else ""
            if manifest.is_file():
                row["fixed_manifest_sha256"] = sha(manifest)
            row["ready"] = bool(row["archive_exists"] and row["fixed_manifest_exists"] and row.get("raw_inputs_exist"))
            rows.append(row)
    return rows


def endpoint(protocol, run, dataset, scene, arm, budget=None, scale=None):
    mp = run / "psnr/strict_fixed_manifest/final_result.json"
    if not mp.exists():
        return None
    m = read(mp)
    q = m["predeclared_fixed_manifest_posthoc"]
    if not q.get("mapping_disjoint") or q.get("mapping_view_overlap_count") != 0:
        raise RuntimeError(f"Non-disjoint metric: {mp}")
    valid = [v for v in m["per_view"] if v["predeclared_fixed_manifest_split"]]
    if len(valid) != q["view_count"]:
        raise RuntimeError(f"Metric count mismatch: {mp}")
    rp = run / ("result.json" if protocol == "live_fifo" else "render_result.json")
    x = read(rp)
    geo = read(run / "geometry_runtime.json") if (run / "geometry_runtime.json").exists() else {}
    proxy = geo.get("stats", {}).get("aux_renders", 0)
    if protocol == "live_fifo":
        proxy = x.get("geometry", {}).get("stats", {}).get("aux_renders", proxy)
    renders = x.get("render_counts", {}).get("training", x.get("training_renders"))
    queues = x.get("worker", {}).get("queue", {})
    row = {"protocol": protocol, "dataset": dataset, "scene": scene, "arm": arm, "renders_per_kf_cap": budget, "time_scale": scale, "psnr": q["mean_psnr"], "ssim": q["mean_ssim"], "lpips": q["mean_lpips"], "eval_views": q["view_count"], "gaussians": m["gaussians"], "training_renders": renders, "proxy_renders": proxy, "mapping_seconds": x.get("mapping_seconds"), "sensor_seconds": x.get("sensor_duration_seconds"), "allowed_seconds": x.get("duration_seconds"), "tracking_seconds": x.get("tracking_elapsed_seconds"), "peak_cuda_allocated_bytes": x.get("peak_cuda_allocated_bytes", x.get("peak_cuda_allocated")), "optimizer_steps": x.get("main_optimizer_steps", x.get("optimizer_steps")), "mapping_disjoint": True, "zero_tail": x.get("zero_tail_observed", x.get("checks", {}).get("zero_tail")), "output": str(run), "metric_path": str(mp), "metric_sha256": sha(mp), "cohort_uid_sha256": hashlib.sha256(json.dumps(sorted(v["uid"] for v in valid)).encode()).hexdigest(), "result_sha256": sha(rp)}
    if protocol == "live_fifo":
        row["tracking_config_scope"] = "same_between_arms" if dataset == "aria" else "end_to_end_different_motion_window_radius"
        row["dropped_packets"] = queues.get("dropped_packets", x.get("worker", {}).get("dropped_packets"))
        row["end_lag_ms"] = x.get("end_lag_ms")
    return row


def collect():
    rows = []
    for key, (d, s) in KEYS.items():
        for arm in ["d3", "vanilla"]:
            row = endpoint("fixed_training40_d3", RESULTS / f"geometry_main_validation/gpu_v1/{key}/{arm}", d, s, arm, 40)
            if row:
                rows.append(row)
        for arm in ["ours", "vanilla"]:
            suffix = f"rot_gpu40_v1/{arm}" if key == "rot" else f"gpu40_v1/{key}/{arm}"
            row = endpoint("fixed_training40_native_previous", RESULTS / f"main_validation/{suffix}", d, s, arm, 40)
            if row:
                rows.append(row)
        for label, scale in [("scale1", 1), ("scale1p5", 1.5)]:
            for arm in ["ours", "vanilla"]:
                row = endpoint("live_fifo", RESULTS / f"fifo_live/v1/{label}/{key}/{arm}", d, s, arm, 40, scale)
                if row:
                    rows.append(row)
    for protocol in {r["protocol"] for r in rows}:
        groups = {}
        for r in rows:
            if r["protocol"] == protocol:
                groups.setdefault((r["dataset"], r["scene"], r["time_scale"]), []).append(r)
        for values in groups.values():
            if len(values) == 2 and len({r["cohort_uid_sha256"] for r in values}) != 1:
                raise RuntimeError(f"Paired held-out cohorts differ: {values}")
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=OUT)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    scene_rows, endpoints = inventory(), collect()
    source = {"custom_head": subprocess.check_output(["git", "-C", str(MAIN), "rev-parse", "HEAD"], text=True).strip(), "geometry_commit": "8c840d41dc70ba0a0015b4f93e1c279a278e2f46", "official_head": subprocess.check_output(["git", "-C", "/home/intern/VIGS-SLAM-official-exp78", "rev-parse", "HEAD"], text=True).strip(), "candidate_count": len(scene_rows), "measurement_count": len(endpoints), "core_sha256": {str(q): sha(q) for q in [*MAIN.glob("vigs/**/*.py"), *MAIN.glob("scripts/selected_mapping/*.py"), *MAIN.glob("scripts/selected_mapping/geometry_merge/*.py"), MAIN / "configs/selected_mapping_fixed40.json"]}}
    write(a.output / "scene_inventory.json", scene_rows)
    write(a.output / "source_lock.json", source)
    write(a.output / "measured_endpoints.json", endpoints)
    csv_write(a.output / "scene_inventory.csv", scene_rows)
    csv_write(a.output / "measured_endpoints.csv", endpoints)
    print(json.dumps({"output": str(a.output), "measurements": len(endpoints), "ready_inputs": sum(r["ready"] for r in scene_rows), "candidates": len(scene_rows), "unready": [r["scene"] for r in scene_rows if not r["ready"]]}))


if __name__ == "__main__":
    main()
