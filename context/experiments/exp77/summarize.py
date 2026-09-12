"""Compare complete exp77 runs; never infer success from execution alone."""
import argparse
import json
import math
import statistics
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, required=True)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    arms, schedules, traces, name_sets, grids = {}, [], [], [], []
    for arm in ("rr", "ercb", "packet"):
        path = args.runs / f"{arm}_s{args.seed}"
        summary = json.loads((path / "view_scheduler_summary.json").read_text())
        evaluations = [json.loads(line) for line in (path / "evaluation_curve.jsonl").read_text().splitlines()]
        curve = [row for row in evaluations if row["split"] == "test"]
        timing = [json.loads(line) for line in (path / "training_timing.jsonl").read_text().splitlines()]
        total = summary["total_iterations"]
        if not summary["post_update_reporting"] or summary["completed_updates_this_run"] != total:
            raise ValueError(f"{arm}: update/report mismatch")
        if sum(summary["selection_count"].values()) != total or max(summary["arrival_iteration"].values()) != total:
            raise ValueError(f"{arm}: draw/arrival/tail mismatch")
        if not curve or curve[-1]["iteration"] != total:
            raise ValueError(f"{arm}: final held-out evaluation missing")
        names = sorted(curve[-1]["per_view_psnr"])
        if any(set(row["per_view_psnr"]) != set(names) for row in curve):
            raise ValueError(f"{arm}: held-out membership changed")
        values = [curve[-1]["per_view_psnr"][name] for name in names]
        if not all(math.isfinite(v) for row in curve for v in row["per_view_psnr"].values()):
            raise ValueError(f"{arm}: nonfinite PSNR")
        q1 = max(1, math.ceil(len(values) / 4))
        late = max(1, math.ceil(len(values) / 3))
        delays = list(summary["first_service_delay_updates"].values())
        if any(delay < 0 for delay in delays):
            raise ValueError(f"{arm}: future-frame selection")
        arms[arm] = {"final_psnr": statistics.fmean(values),
                     "worst_q1_psnr": statistics.fmean(sorted(values)[:q1]),
                     "late_third_psnr": statistics.fmean(values[-late:]),
                     "curve": [{"updates": row["iteration"], "psnr": row["psnr"]} for row in curve],
                     "training_timing": timing, "training_gpu_ms": summary["training_gpu_ms"],
                     "scheduler_cpu_ms": summary["scheduler_cpu_ns"] / 1e6,
                     "unique_selected": summary["unique_selected"], "zero_service": summary["zero_service"],
                     "served_only_first_delay_mean": statistics.fmean(delays) if delays else None,
                     "served_only_first_delay_max": max(delays) if delays else None}
        schedules.append(summary["arrival_iteration"])
        name_sets.append(names)
        grids.append([row["iteration"] for row in curve])
        if arm != "rr":
            traces.append(summary["outer_trace_sha256"])
    if not schedules[0] == schedules[1] == schedules[2] or not name_sets[0] == name_sets[1] == name_sets[2]:
        raise ValueError("Arms used different arrival schedules or held-out sets")
    if not grids[0] == grids[1] == grids[2] or traces[0] != traces[1]:
        raise ValueError("Evaluation grids or ERCB outer sequences differ")
    result = {"status": "COMPLETE_COMPARISON_NOT_AUTOMATIC_GO", "seed": args.seed, "arms": arms,
              "packet_minus_ercb_db": arms["packet"]["final_psnr"] - arms["ercb"]["final_psnr"],
              "packet_minus_rr_db": arms["packet"]["final_psnr"] - arms["rr"]["final_psnr"],
              "caveats": ["One seed is a screen, not generalization evidence", "Delays exclude unserved views; read zero_service too",
                          "Compute-clock causal replay, not strict wall-clock SLAM", "Scheduler CPU ms is not measured extra mapping overhead"]}
    dest = args.runs / f"comparison_s{args.seed}.json"
    with dest.open("x") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
