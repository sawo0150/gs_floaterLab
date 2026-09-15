#!/usr/bin/env python3
import json
import re
import statistics
from pathlib import Path

LAB_ROOT = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
RESULT_ROOT = LAB_ROOT / "results/ERCB_ablation/exp03-G_frozen_tracking_pose"
OUT = Path(__file__).resolve().parent / "evidence/summary.json"


def parse_summary(log_path: Path) -> dict:
    lines = [line for line in log_path.read_text(errors="replace").splitlines()
             if line.startswith("MAP_ONLINE_SUMMARY ")]
    if not lines:
        raise RuntimeError(f"missing MAP_ONLINE_SUMMARY: {log_path}")
    fields = {}
    for token in lines[-1].split()[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key] = value
    return fields


def ply_vertices(path: Path) -> int:
    with path.open("rb") as handle:
        for raw in handle:
            line = raw.decode("ascii", errors="strict").strip()
            if line.startswith("element vertex "):
                return int(line.rsplit(" ", 1)[1])
            if line == "end_header":
                break
    raise RuntimeError(f"missing vertex count: {path}")


def as_int(fields: dict, key: str) -> int:
    return int(fields[key])


runs = []
pattern = re.compile(r"^(rr|ercb_dense)_s(\d+)$")
for result_path in sorted(RESULT_ROOT.glob("*/*/q*/*/psnr/online_final/final_result.json")):
    arm_dir = result_path.parents[2]
    match = pattern.match(arm_dir.name)
    if not match:
        continue
    selector, seed_text = match.groups()
    q_dir, scene_dir, family_dir = arm_dir.parent, arm_dir.parent.parent, arm_dir.parent.parent.parent
    metrics = json.loads(result_path.read_text())
    summary = parse_summary(arm_dir / "run.log")
    audit = json.loads((arm_dir / "sensor_eos_audit.json").read_text())
    runs.append({
        "family": family_dir.name,
        "scene": scene_dir.name,
        "quota": int(q_dir.name.removeprefix("q")),
        "seed": int(seed_text),
        "selector": selector,
        "fixed_eval_mean_psnr": metrics["fixed_eval_mean_psnr"],
        "fixed_eval_mean_ssim": metrics["fixed_eval_mean_ssim"],
        "fixed_eval_mean_lpips": metrics["fixed_eval_mean_lpips"],
        "adam_steps": as_int(summary, "physical_adam_steps_total"),
        "keyframe_updates": as_int(summary, "keyframe_updates"),
        "dense_updates": as_int(summary, "dense_updates"),
        "topology_events": as_int(summary, "topology_events"),
        "dense_under_required": as_int(summary, "dense_under_required"),
        "dense_last_to_first": float(summary["selection_count_last_to_first"]),
        "final_gaussians": ply_vertices(arm_dir / "3dgs_before_final.ply"),
        "zero_tail": (
            audit["updates_completed_after_sensor_eos"] == 0
            and audit["topology_actions_completed_after_sensor_eos"] == 0
        ),
    })

pairs = []
grouped = {}
for run in runs:
    key = (run["family"], run["scene"], run["quota"], run["seed"])
    grouped.setdefault(key, {})[run["selector"]] = run
for (family, scene, quota, seed), arms in sorted(grouped.items()):
    if set(arms) != {"rr", "ercb_dense"}:
        continue
    rr, ercb = arms["rr"], arms["ercb_dense"]
    pairs.append({
        "family": family,
        "scene": scene,
        "quota": quota,
        "seed": seed,
        "rr_psnr": rr["fixed_eval_mean_psnr"],
        "ercb_psnr": ercb["fixed_eval_mean_psnr"],
        "delta_psnr": ercb["fixed_eval_mean_psnr"] - rr["fixed_eval_mean_psnr"],
        "delta_ssim": ercb["fixed_eval_mean_ssim"] - rr["fixed_eval_mean_ssim"],
        "delta_lpips": ercb["fixed_eval_mean_lpips"] - rr["fixed_eval_mean_lpips"],
        "adam_steps_rr": rr["adam_steps"],
        "adam_steps_ercb": ercb["adam_steps"],
        "keyframe_updates_rr": rr["keyframe_updates"],
        "keyframe_updates_ercb": ercb["keyframe_updates"],
        "dense_updates_rr": rr["dense_updates"],
        "dense_updates_ercb": ercb["dense_updates"],
        "topology_events_rr": rr["topology_events"],
        "topology_events_ercb": ercb["topology_events"],
        "final_gaussians_rr": rr["final_gaussians"],
        "final_gaussians_ercb": ercb["final_gaussians"],
        "dense_under_required_rr": rr["dense_under_required"],
        "dense_under_required_ercb": ercb["dense_under_required"],
        "dense_last_to_first_rr": rr["dense_last_to_first"],
        "dense_last_to_first_ercb": ercb["dense_last_to_first"],
        "zero_tail_both": rr["zero_tail"] and ercb["zero_tail"],
    })

aggregates = []
for key in sorted({(p["family"], p["scene"], p["quota"]) for p in pairs}):
    selected = [p for p in pairs if (p["family"], p["scene"], p["quota"]) == key]
    deltas = [p["delta_psnr"] for p in selected]
    aggregates.append({
        "family": key[0],
        "scene": key[1],
        "quota": key[2],
        "n": len(deltas),
        "mean_delta_psnr": statistics.mean(deltas),
        "sample_stdev_delta_psnr": statistics.stdev(deltas) if len(deltas) > 1 else None,
        "wins": sum(delta > 0 for delta in deltas),
    })

payload = {
    "experiment": "exp03-G_frozen_tracking_pose",
    "date": "2026-09-15",
    "diagnostic_only": True,
    "primary_metric": "fixed_eval_mean_psnr",
    "runs": runs,
    "pairs": pairs,
    "aggregates": aggregates,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"pairs": pairs, "aggregates": aggregates}, indent=2))
