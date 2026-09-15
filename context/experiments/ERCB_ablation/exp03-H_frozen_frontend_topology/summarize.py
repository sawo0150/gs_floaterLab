#!/usr/bin/env python3
import json
import re
from pathlib import Path


LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
RESULT_ROOT = LAB / "results/ERCB_ablation/exp03-H_frozen_frontend_topology"
OUTPUT = LAB / "context/experiments/ERCB_ablation/exp03-H_frozen_frontend_topology/evidence/summary.json"
SPECS = (
    ("utmm", "square-1", "q15"),
    ("rpng", "table_07", "q3"),
)


def last_summary(log_text):
    line = [line for line in log_text.splitlines() if "MAP_ONLINE_SUMMARY" in line][-1]
    return dict(re.findall(r"([A-Za-z0-9_]+)=([^ ]+)", line))


def ply_vertices(path):
    with path.open("rb") as stream:
        header = stream.read(4096).split(b"end_header", 1)[0].decode("ascii")
    return int(re.search(r"^element vertex (\d+)$", header, re.MULTILINE).group(1))


records = []
for family, scene, quota in SPECS:
    base = RESULT_ROOT / family / scene / quota
    pair = {}
    for arm, dirname in (("rr", "rr_replay_v3_s0"), ("ercb", "ercb_dense_replay_v3_s0")):
        run = base / dirname
        metrics = json.loads((run / "psnr/online_final/final_result.json").read_text())
        audit = json.loads((run / "sensor_eos_audit.json").read_text())
        log_text = (run / "run.log").read_text(errors="replace")
        summary = last_summary(log_text)
        topology_events = [
            {
                "event": int(event),
                "packet_index": int(packet),
                "before": int(before),
                "after": int(after),
            }
            for event, packet, before, after in re.findall(
                r"MAP_PACKET_TOPOLOGY_EVENT event=(\d+) packet_index=(\d+) before=(\d+) after=(\d+)",
                log_text,
            )
        ]
        pair[arm] = {
            "fixed_eval_psnr": metrics["fixed_eval_mean_psnr"],
            "fixed_eval_ssim": metrics["fixed_eval_mean_ssim"],
            "fixed_eval_lpips": metrics["fixed_eval_mean_lpips"],
            "fixed_eval_views": metrics["fixed_eval_view_count"],
            "mean_psnr": metrics["mean_psnr"],
            "adam_steps": int(summary["physical_adam_steps_total"]),
            "keyframe_updates": int(summary["keyframe_updates"]),
            "dense_updates": int(summary["dense_updates"]),
            "frontend_packets": int(summary["frontend_trace_packets"]),
            "frontend_expected_packets": int(summary["frontend_trace_expected_packets"]),
            "topology_events": int(summary["topology_trace_events"]),
            "topology_expected_events": int(summary["topology_trace_expected_events"]),
            "pending_keyframe_births": int(summary["pending_keyframe_births"]),
            "final_gaussians": ply_vertices(run / "3dgs_before_final.ply"),
            "topology_event_trace": topology_events,
            "zero_tail": (
                audit["updates_completed_after_sensor_eos"] == 0
                and audit["updates_completed_after_deadline"] == 0
                and audit["topology_actions_completed_after_sensor_eos"] == 0
                and audit["topology_actions_completed_after_deadline"] == 0
            ),
        }
    record = {
        "family": family,
        "scene": scene,
        "quota": quota,
        "seed": 0,
        "rr": pair["rr"],
        "ercb": pair["ercb"],
        "delta_ercb_minus_rr": {
            "fixed_eval_psnr": pair["ercb"]["fixed_eval_psnr"] - pair["rr"]["fixed_eval_psnr"],
            "fixed_eval_ssim": pair["ercb"]["fixed_eval_ssim"] - pair["rr"]["fixed_eval_ssim"],
            "fixed_eval_lpips": pair["ercb"]["fixed_eval_lpips"] - pair["rr"]["fixed_eval_lpips"],
            "adam_steps": pair["ercb"]["adam_steps"] - pair["rr"]["adam_steps"],
            "keyframe_updates": pair["ercb"]["keyframe_updates"] - pair["rr"]["keyframe_updates"],
            "dense_updates": pair["ercb"]["dense_updates"] - pair["rr"]["dense_updates"],
            "final_gaussians": pair["ercb"]["final_gaussians"] - pair["rr"]["final_gaussians"],
        },
        "valid_trace_pair": (
            pair["rr"]["frontend_packets"] == pair["ercb"]["frontend_packets"]
            == pair["rr"]["frontend_expected_packets"]
            == pair["ercb"]["frontend_expected_packets"]
            and pair["rr"]["topology_events"] == pair["ercb"]["topology_events"]
            == pair["rr"]["topology_expected_events"]
            == pair["ercb"]["topology_expected_events"]
            and pair["rr"]["topology_event_trace"] == pair["ercb"]["topology_event_trace"]
            and pair["rr"]["final_gaussians"] == pair["ercb"]["final_gaussians"]
            and pair["rr"]["pending_keyframe_births"] == pair["ercb"]["pending_keyframe_births"] == 0
            and pair["rr"]["zero_tail"] and pair["ercb"]["zero_tail"]
        ),
    }
    records.append(record)

payload = {
    "experiment": "exp03-H_frozen_frontend_topology",
    "protocol": "diagnostic_gt_pose_frozen_frontend_packet_driven_shared_topology",
    "records": records,
    "mean_fixed_eval_psnr_delta": sum(
        record["delta_ercb_minus_rr"]["fixed_eval_psnr"] for record in records
    ) / len(records),
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
print(OUTPUT)
