#!/usr/bin/env python3
"""Freeze the two local Aria mapping-held-out manifests for exp78 B."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
OUTPUT = WORKSPACE / "context/experiments/exp78/b_strict_fair_comparison/manifests"
SCENES = {
    "aria1253": (
        Path("/home/intern/p28_5090_20260813/VIGS-SLAM-custom/data/aria1253_repro/rgb"),
        "development",
    ),
    "aria301_305": (
        Path("/home/intern/p28_5090_20260813/VIGS-SLAM-custom/data/aria301_305/rgb"),
        "transfer",
    ),
}


def digest_lines(values: list[str]) -> str:
    return hashlib.sha256(("\n".join(values) + "\n").encode()).hexdigest()


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for sequence, (image_dir, role) in SCENES.items():
        names = sorted(
            (path.name for path in image_dir.iterdir() if path.is_file()),
            key=lambda name: float(Path(name).stem),
        )
        selected = [
            {
                "frame_index": index,
                "timestamp_token": Path(name).stem,
                "uid": name,
            }
            for index, name in enumerate(names)
            if index % 5 == 0 or index == len(names) - 1
        ]
        manifest = {
            "all_input_uids_sha256": digest_lines(names),
            "dataset": "aria",
            "eval_count": len(selected),
            "eval_uids_sha256": digest_lines([row["uid"] for row in selected]),
            "frame_count": len(names),
            "mapping_disjoint_required": True,
            "role": role,
            "selection_rule": "zero_based_frame_index % 5 == 0 OR final frame",
            "sequence": sequence,
            "views": selected,
        }
        destination = OUTPUT / f"aria_{sequence}.json"
        destination.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
