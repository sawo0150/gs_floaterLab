#!/usr/bin/env python3
"""Derive a keyframe-only causal RR pool from the existing full-pool schedules.

For each scene, the actual VIGS keyframe timestamps (traj_kf_beforeBA.txt) are
mapped to the nearest RGB frame index -- exactly the same boundary computation
prepare_datasets.py uses to define event brackets. That gives one frame name
per event that is a "real" keyframe as opposed to a dense in-between frame.
Filtering an existing arrival_iteration_by_name schedule down to those names
(keeping the same arrival iterations, same total_iterations, same budget)
yields a keyframe-only RR candidate pool that is directly comparable to the
existing full-pool RR/ERCB arms: same Adam step budget, same event boundaries,
smaller (keyframe-only) source pool.

Read-only with respect to evidence/manifest.json, evidence/schedules/, and
evidence/dataset_inventory.json -- writes only under evidence/schedules_kfrr/
and evidence/keyframe_pool_inventory.json, so it is safe to run while
run_panel.py is still executing the full-pool rr/ercb manifest.
"""

from __future__ import annotations

import json
from pathlib import Path

from prepare_datasets import inventory, load_trajectory, nearest_indices

HERE = Path(__file__).resolve().parent
SOURCE_INVENTORY = HERE / "evidence/source_inventory.json"
DATASET_INVENTORY = HERE / "evidence/dataset_inventory.json"
SCHEDULES = HERE / "evidence/schedules"
OUTPUT = HERE / "evidence/schedules_kfrr"
POOL_INVENTORY = HERE / "evidence/keyframe_pool_inventory.json"

CONDITIONS = ((40, 15), (20, 15), (20, 30), (20, 60))


def keyframe_names(row: dict) -> set[str]:
    images, timestamps, _ = inventory(row)
    source_run = Path(row["output"])
    keyframes = load_trajectory(source_run / "traj_kf_beforeBA.txt")
    mapped = nearest_indices(keyframes[:, 0], timestamps)
    first_train = next(index for index in range(len(images)) if index % 8 != 0)
    boundaries = mapped[mapped >= first_train]
    return {images[index].name for index in boundaries}


def main() -> None:
    source = json.loads(SOURCE_INVENTORY.read_text())
    source_by_key = {(row["family"], row["scene"]): row for row in source["records"]}
    dataset = json.loads(DATASET_INVENTORY.read_text())
    records = []
    for entry in dataset["records"]:
        family, scene = entry["family"], entry["scene"]
        row = source_by_key[(family, scene)]
        names = keyframe_names(row)
        raw_boundaries = len(names)
        record = {
            "family": family, "scene": scene,
            "raw_keyframe_boundaries": raw_boundaries,
            "conditions": {},
        }
        for stride, budget in CONDITIONS:
            source_schedule = SCHEDULES / family / f"{scene}_stride{stride}_event{budget}.json"
            payload = json.loads(source_schedule.read_text())
            full_pool = payload["arrival_iteration_by_name"]
            kf_pool = {name: value for name, value in full_pool.items() if name in names}
            if not kf_pool:
                raise ValueError(f"empty keyframe-only pool: {family}/{scene} stride{stride} event{budget}")
            populated_events = len(set(kf_pool.values()))
            destination = OUTPUT / family / f"{scene}_stride{stride}_event{budget}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "arrival_iteration_by_name": kf_pool,
                "total_iterations": payload["total_iterations"],
                "source_schedule": str(source_schedule),
                "full_pool_size": len(full_pool),
                "keyframe_only_pool_size": len(kf_pool),
                "populated_events": populated_events,
                "updates_per_event": payload["updates_per_event"],
                "tail_iters": 0,
                "pool_definition": "full-pool schedule filtered to VIGS keyframe-mapped frame names only",
            }, indent=2) + "\n")
            record["conditions"][f"stride{stride}_event{budget}"] = {
                "full_pool_size": len(full_pool),
                "keyframe_only_pool_size": len(kf_pool),
                "populated_events": populated_events,
            }
        records.append(record)
        print(f"{family}/{scene}: raw_boundaries={raw_boundaries} " + " ".join(
            f"{key}={value['keyframe_only_pool_size']}/{value['full_pool_size']}"
            for key, value in record["conditions"].items()
        ), flush=True)
    POOL_INVENTORY.write_text(json.dumps({
        "protocol": "benchmark-B keyframe-only RR candidate pool derivation",
        "records": records,
    }, indent=2) + "\n")
    print(POOL_INVENTORY)


if __name__ == "__main__":
    main()
