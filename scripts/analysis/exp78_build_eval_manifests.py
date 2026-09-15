#!/usr/bin/env python3
"""Freeze method-independent rendering UIDs before exp78 optimization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
SEQUENCES = {
    "rpng": {
        "root": WORKSPACE / "data/benchmarks/rpng/prepared/rpngar",
        "image_dir": "rgb",
        "development": {"table_01", "table_06"},
    },
    "utmm": {
        "root": WORKSPACE / "data/benchmarks/utmm/prepared/UTMM_Dataset",
        "image_dir": "rgb_timestamp",
        "development": {"ego-drive", "square-2"},
    },
}


def digest_lines(values: list[str]) -> str:
    return hashlib.sha256(("\n".join(values) + "\n").encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=WORKSPACE / "context/experiments/exp78/b_strict_fair_comparison/manifests",
    )
    parser.add_argument("--modulus", type=int, default=5)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "protocol": "fixed_mod5_plus_last_uid_v1",
        "selection_rule": "zero_based_frame_index % 5 == 0 OR final frame",
        "mapping_contract": "all listed UIDs must be excluded from GS supervision and birth",
        "tracking_contract": "tracking may observe listed RGB frames; rendering metrics are mapping-held-out",
        "modulus": args.modulus,
        "prospective_split_note": "Legacy experiments exposed all sequences; validation is untouched only relative to exp78 tuning after this lock.",
        "datasets": {},
    }
    for dataset, spec in SEQUENCES.items():
        root = spec["root"]
        development = spec["development"]
        dataset_summary: dict[str, object] = {}
        for sequence_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            image_dir = sequence_dir / str(spec["image_dir"])
            if not image_dir.is_dir():
                continue
            names = sorted(path.name for path in image_dir.iterdir() if path.is_file())
            selected = [
                {"frame_index": index, "uid": name, "timestamp_token": Path(name).stem}
                for index, name in enumerate(names)
                if index % args.modulus == 0 or index == len(names) - 1
            ]
            role = "development" if sequence_dir.name in development else "validation"
            manifest = {
                "dataset": dataset,
                "sequence": sequence_dir.name,
                "role": role,
                "frame_count": len(names),
                "eval_count": len(selected),
                "all_input_uids_sha256": digest_lines(names),
                "eval_uids_sha256": digest_lines([row["uid"] for row in selected]),
                "selection_rule": summary["selection_rule"],
                "mapping_disjoint_required": True,
                "views": selected,
            }
            path = args.output / f"{dataset}_{sequence_dir.name}.json"
            path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            dataset_summary[sequence_dir.name] = {
                "role": role,
                "frame_count": len(names),
                "eval_count": len(selected),
                "manifest": str(path.relative_to(WORKSPACE)),
                "eval_uids_sha256": manifest["eval_uids_sha256"],
            }
        summary["datasets"][dataset] = dataset_summary
    summary_path = args.output / "manifest_index.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
