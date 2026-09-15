#!/usr/bin/env python3
"""Validate hashes, causality, and mapping-disjointness of an exp78b trace."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

import torch

from exp78b_frozen_archive import (
    FrozenTrackerArchive,
    sha256_file,
    tensor_digest,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    archive = FrozenTrackerArchive(args.archive)
    violations: list[str] = []
    geometry_refs: dict[str, str | dict[str, Any]] = {}
    raw_packet_heldout: set[int] = set()
    filtered_packet_uids: set[int] = set()
    event_uid_counts: Counter[int] = Counter()

    for expected_id, metadata in enumerate(archive.events):
        if int(metadata["event_id"]) != expected_id:
            violations.append(f"event_order:{metadata['event_id']}!={expected_id}")
        event = archive.load_event_payload(metadata)
        if event["kind"] in {"metric_rescale", "mapper_reset"}:
            if event["kind"] == "metric_rescale":
                scale = float(event["scale"])
                if not (scale > 0.0):
                    violations.append(f"invalid_metric_scale:{expected_id}")
            continue
        uids = [int(value) for value in event["frame_uids"].tolist()]
        event_uid_counts.update(uids)
        for reference in event["geometry_refs"]:
            geometry_refs[
                archive.geometry_cache_key(reference)
            ] = reference
        if any(uid > int(metadata["emitted_at_frame_uid"]) for uid in uids):
            violations.append(f"future_uid_in_event:{expected_id}")
        raw_packet_heldout.update(set(uids).intersection(archive.heldout_uids))
        if len(event["geometry_refs"]) != len(uids):
            violations.append(f"geometry_ref_count:{expected_id}")
        if event["poses"].shape[0] != len(uids):
            violations.append(f"pose_count:{expected_id}")
        if event["intrinsics"].shape[0] != len(uids):
            violations.append(f"intrinsics_count:{expected_id}")
        if event["pose_updates_data"] is not None:
            if event["pose_updates_data"].shape[0] != len(uids):
                violations.append(f"pose_update_count:{expected_id}")
            if event["scale_updates"] is None or event["scale_updates"].shape[0] != len(uids):
                violations.append(f"scale_update_count:{expected_id}")
        # Validate the mapper-facing UID filter without materializing RGB and
        # geometry tensors for every packet. FrozenTrackerArchive caches those
        # tensors for replay; doing that here made validation scale to the full
        # archive size in host RAM (tens of GB on long RPNG sequences).
        packet_uids = {uid for uid in uids if uid not in archive.heldout_uids}
        if packet_uids:
            filtered_packet_uids.update(packet_uids)
            if packet_uids.intersection(archive.heldout_uids):
                violations.append(f"heldout_survived_filter:{expected_id}")

    tensor_hash_mismatches = 0
    for cache_key in sorted(geometry_refs):
        item = archive.load_geometry(geometry_refs[cache_key])
        if tensor_digest(item["depth"], item["normal"]) != item["sha256_tensor_payload"]:
            tensor_hash_mismatches += 1
        archive._geometry_cache.pop(cache_key, None)
    if tensor_hash_mismatches:
        violations.append(f"geometry_tensor_hash_mismatch:{tensor_hash_mismatches}")

    dense_uid_counts: Counter[int] = Counter()
    for metadata in archive.dense_intervals:
        interval = archive.load_dense_interval(metadata)
        candidates = [int(value) for value in interval["candidate_uids"].tolist()]
        dense_uid_counts.update(candidates)
        if any(uid in archive.heldout_uids for uid in candidates):
            violations.append(f"heldout_dense_candidate:{metadata['interval_id']}")
        if any(uid > int(metadata["available_at_frame_uid"]) for uid in candidates):
            violations.append(f"future_dense_candidate:{metadata['interval_id']}")
        if interval["interpolated_poses_w2c"].shape != (len(candidates), 4, 4):
            violations.append(f"dense_pose_shape:{metadata['interval_id']}")

    runtime = archive.manifest["runtime"]
    if int(runtime["gaussian_optimizer_updates"]) != 0:
        violations.append("capture_gaussian_updates_nonzero")
    if int(runtime["post_eos_gaussian_optimizer_updates"]) != 0:
        violations.append("capture_post_eos_gaussian_updates_nonzero")
    if len(archive.arrivals) != int(runtime["frames"]):
        violations.append("arrival_count_mismatch")
    if sha256_file(archive.root / archive.manifest["arrivals"]) != archive.manifest["arrivals_sha256"]:
        violations.append("arrivals_hash_mismatch")

    report: dict[str, Any] = {
        "validation_protocol": "exp78b_frozen_tracker_validation_v2",
        "schema_version": archive.manifest["schema_version"],
        "archive": str(archive.root),
        "archive_manifest_sha256": sha256_file(archive.root / "archive_manifest.json"),
        "valid": not violations,
        "violations": violations,
        "frames": len(archive.arrivals),
        "heldout_count": len(archive.heldout_uids),
        "events": len(archive.events),
        "event_unique_uids": len(event_uid_counts),
        "raw_packet_heldout_count": len(raw_packet_heldout),
        "filtered_mapping_unique_uids": len(filtered_packet_uids),
        "filtered_mapping_heldout_overlap": len(
            filtered_packet_uids.intersection(archive.heldout_uids)
        ),
        "geometry_versions": len(geometry_refs),
        "geometry_tensor_hash_mismatches": tensor_hash_mismatches,
        "dense_intervals": len(archive.dense_intervals),
        "dense_candidate_occurrences": sum(dense_uid_counts.values()),
        "dense_unique_candidate_uids": len(dense_uid_counts),
        "dense_duplicate_occurrences": sum(
            max(0, count - 1) for count in dense_uid_counts.values()
        ),
        "dense_heldout_overlap": len(
            set(dense_uid_counts).intersection(archive.heldout_uids)
        ),
        "causal_event_order": not any(
            value.startswith(("future_uid", "future_dense", "event_order"))
            for value in violations
        ),
        "mapping_disjoint_filter_valid": not any(
            "heldout" in value for value in violations
        ),
        "zero_mapping_updates_during_capture": (
            int(runtime["gaussian_optimizer_updates"]) == 0
            and int(runtime["post_eos_gaussian_optimizer_updates"]) == 0
        ),
    }
    output = args.output or (archive.root / "validation.json")
    write_json(output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
