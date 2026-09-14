#!/usr/bin/env python3
"""Attach a causal fixed-rate pseudo-KF arrival schedule to COLMAP text data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def image_names(images_txt: Path) -> list[str]:
    rows = []
    for line in images_txt.read_text().splitlines():
        tokens = line.split()
        if len(tokens) == 10 and tokens[0].isdigit():
            rows.append((int(tokens[0]), tokens[9]))
    return [name for _, name in sorted(rows)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--rgb-per-interval", type=int, default=8)
    parser.add_argument("--iters-per-interval", type=int, default=60)
    parser.add_argument("--tail-iters", type=int, default=3000)
    args = parser.parse_args()
    if args.rgb_per_interval < 1 or args.iters_per_interval < 1:
        raise ValueError("interval sizes must be positive")

    names = image_names(args.dataset / "sparse" / "0" / "images.txt")
    arrivals = {}
    heldout = []
    for frame_index, name in enumerate(names):
        if frame_index % 8 == 0:
            heldout.append(name)
            continue
        interval_id = frame_index // args.rgb_per_interval
        arrivals[name] = 1 + interval_id * args.iters_per_interval
    intervals = 1 + (len(names) - 1) // args.rgb_per_interval
    payload = {
        "arrival_iteration_by_name": arrivals,
        "total_iterations": intervals * args.iters_per_interval + args.tail_iters,
        "iters_per_event": args.iters_per_interval,
        "tail_iters": args.tail_iters,
        "events": intervals,
        "all_frames": len(names),
        "train_frames": len(arrivals),
        "heldout_frames": len(heldout),
        "heldout_rule": "sorted COLMAP image index modulo 8 equals zero",
        "interval_definition": f"fixed non-overlapping {args.rgb_per_interval}-RGB-frame pseudo-KF intervals",
    }
    output = args.dataset / "causal_arrivals.json"
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({key: value for key, value in payload.items() if key != "arrival_iteration_by_name"}, indent=2))


if __name__ == "__main__":
    main()
