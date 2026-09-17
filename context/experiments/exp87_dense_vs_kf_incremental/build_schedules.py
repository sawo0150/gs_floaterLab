#!/usr/bin/env python3
"""Build exp87 causal schedules (~30k updates) and the keyframe-only pool list.

Causality is preserved exactly as in benchmark-A/B: every frame keeps the event
(VIGS keyframe interval) it was assigned by prepare_datasets.py, and an event's
frames become eligible only at that event's iteration. The only change is the
per-event budget, which is scaled so the stream spans a standard 3DGS-length
run (~30,000 optimizer updates) instead of the ERCB ablation's 1-15k. That is
what lets densification and per-view repetition reach the regime where the
batch dense-vs-keyframe effect was originally observed (exp66).

Outputs per scene:
  evidence/schedules/<family>/<scene>.json   full causal pool (all train frames)
  evidence/eligible/<family>/<scene>_kf.json keyframe-only pool (names only)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
KF_SOURCE = ROOT / "context/experiments/ERCB_ablation/benchmark-B/evidence/schedules_kfrr"
TARGET_ITERATIONS = 30_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(family: str, scene: str, stride: int = 20) -> dict:
    causal = DATA_ROOT / family / scene / f"stride{stride}" / "causal_arrivals.json"
    payload = json.loads(causal.read_text())
    if payload.get("iters_per_event") != 60 or payload.get("tail_iters") != 0:
        raise ValueError(f"unexpected causal_arrivals.json: {causal}")
    events = payload["events"]
    budget = max(1, round((TARGET_ITERATIONS - 1) / max(events - 1, 1)))
    converted = {
        name: 1 + ((int(value) - 1) // 60) * budget
        for name, value in payload["arrival_iteration_by_name"].items()
    }
    total = max(converted.values())
    schedule_path = HERE / "evidence/schedules" / family / f"{scene}.json"
    schedule_path.parent.mkdir(parents=True, exist_ok=True)
    schedule_path.write_text(json.dumps({
        "arrival_iteration_by_name": converted,
        "total_iterations": total,
        "updates_per_event": budget,
        "events": events,
        "tail_iters": 0,
        "source_schedule": str(causal),
        "source_schedule_sha256": sha256(causal),
    }, indent=2) + "\n")

    kf_source = KF_SOURCE / family / f"{scene}_stride{stride}_event15.json"
    kf_names = sorted(json.loads(kf_source.read_text())["arrival_iteration_by_name"])
    missing = [n for n in kf_names if n not in converted]
    if missing:
        raise ValueError(f"keyframe name absent from schedule: {family}/{scene} {missing[:3]}")
    eligible_path = HERE / "evidence/eligible" / family / f"{scene}_kf.json"
    eligible_path.parent.mkdir(parents=True, exist_ok=True)
    eligible_path.write_text(json.dumps(kf_names, indent=2) + "\n")

    return {
        "family": family, "scene": scene, "stride": stride,
        "events": events, "updates_per_event": budget, "total_iterations": total,
        "train_frames": len(converted), "keyframe_frames": len(kf_names),
        "heldout_frames": payload["heldout_frames"],
        "updates_per_train_frame": round(total / len(converted), 2),
        "updates_per_keyframe": round(total / len(kf_names), 2),
        "schedule": str(schedule_path), "eligible_kf": str(eligible_path),
        "keyframe_source": str(kf_source),
    }


def main() -> None:
    # Families interleaved so that a partial panel is still representative of all
    # three datasets, and the largest scenes (5-7k train frames) run last.
    scenes = [
        ("aria", "aria1253"), ("utmm", "square-1"), ("rpng", "table_01"),
        ("aria", "aria1253rot"), ("utmm", "ego-centric-1"), ("rpng", "table_02"),
        ("aria", "aria301_305"), ("utmm", "ego-centric-2"), ("rpng", "table_06"),
        ("aria", "aria301_12F"), ("utmm", "ego-drive"), ("rpng", "table_07"),
        ("utmm", "square-2"), ("rpng", "table_04"),
        ("utmm", "fast-straight"), ("rpng", "table_05"),
        ("utmm", "slow-straight-2"), ("rpng", "table_03"), ("rpng", "table_08"),
    ]
    records = [build(family, scene) for family, scene in scenes]
    inventory = HERE / "evidence/schedule_inventory.json"
    inventory.write_text(json.dumps({
        "protocol": "exp87 causal schedules scaled to a standard 30k-update run",
        "target_iterations": TARGET_ITERATIONS, "records": records,
    }, indent=2) + "\n")
    for r in records:
        print(f"{r['family']}/{r['scene']}: events={r['events']} budget={r['updates_per_event']} "
              f"total={r['total_iterations']} train={r['train_frames']} kf={r['keyframe_frames']} "
              f"upd/frame={r['updates_per_train_frame']} upd/kf={r['updates_per_keyframe']}")
    print(inventory)


if __name__ == "__main__":
    main()
