#!/usr/bin/env python3
"""Compare custom and vanilla on exactly the same non-vanilla-KF views."""

import argparse
import json
from pathlib import Path
from statistics import fmean


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--custom-dir", required=True, type=Path)
    parser.add_argument("--vanilla-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    custom_path = args.custom_dir / "psnr/online_final/final_result.json"
    vanilla_path = args.vanilla_dir / "psnr/after_opt/final_result.json"
    custom = load_json(custom_path)
    vanilla = load_json(vanilla_path)

    custom_fixed = {
        int(row["frame_idx"]): row
        for row in custom["per_view"]
        if row.get("is_fixed_eval_view", False)
    }
    vanilla_rows = {
        int(row["frame_idx"]): row for row in vanilla["per_view"]
    }
    missing = sorted(set(custom_fixed) - set(vanilla_rows))
    if missing:
        raise RuntimeError(f"vanilla evaluator is missing fixed views: {missing[:10]}")

    shared_ids = sorted(
        frame_idx
        for frame_idx in custom_fixed
        if not vanilla_rows[frame_idx]["is_keyframe"]
    )
    if not shared_ids:
        raise RuntimeError("shared non-keyframe held-out set is empty")

    custom_psnr = fmean(custom_fixed[i]["psnr"] for i in shared_ids)
    vanilla_psnr = fmean(vanilla_rows[i]["psnr"] for i in shared_ids)
    delta = custom_psnr - vanilla_psnr
    result = {
        "scene": args.scene,
        "protocol": "shared_fixed_stride5_plus_last_excluding_vanilla_keyframes",
        "view_count": len(shared_ids),
        "shared_frame_indices": shared_ids,
        "vanilla_keyframes_removed_from_fixed_set": len(custom_fixed) - len(shared_ids),
        "custom_psnr": custom_psnr,
        "vanilla_psnr": vanilla_psnr,
        "delta_db": delta,
        "passes_plus_1db": delta >= 1.0,
        "custom_result": str(custom_path),
        "vanilla_result": str(vanilla_path),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "shared_frame_indices"}, indent=2))


if __name__ == "__main__":
    main()
