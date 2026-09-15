#!/usr/bin/env python3
"""Reader and exact preprocessing utilities for exp78b frozen tracker traces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

import cv2
from lietorch import SE3
import numpy as np
import torch


SCHEMA_VERSION = "exp78b_frozen_tracker_v3"
SUPPORTED_SCHEMA_VERSIONS = {
    "exp78b_frozen_tracker_v2",
    SCHEMA_VERSION,
}
TARGET_PIXELS = 341 * 640


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_digest(*tensors: torch.Tensor) -> str:
    digest = hashlib.sha256()
    for tensor in tensors:
        contiguous = tensor.detach().cpu().contiguous()
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        digest.update(contiguous.numpy().tobytes(order="C"))
    return digest.hexdigest()


class FrozenTrackerArchive:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()
        self.manifest = json.loads((self.root / "archive_manifest.json").read_text())
        self.schema_version = str(self.manifest.get("schema_version"))
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                f"unsupported archive schema: {self.manifest.get('schema_version')}"
            )
        self.arrivals = [
            json.loads(line)
            for line in (self.root / self.manifest["arrivals"]).read_text().splitlines()
            if line.strip()
        ]
        self.arrival_by_uid = {
            int(record["frame_uid"]): record for record in self.arrivals
        }
        self.heldout_uids = {
            int(record["frame_uid"])
            for record in self.arrivals
            if bool(record["held_out"])
        }
        self.image_dir = Path(self.manifest["input_image_directory"])
        self.calibration = np.loadtxt(
            self.manifest["input_calibration"], delimiter=" "
        )
        self.preprocessing = self.manifest["preprocessing"]
        self._rgb_cache: dict[int, torch.Tensor] = {}
        self._geometry_cache: dict[str, dict[str, Any]] = {}

    @property
    def events(self) -> list[dict[str, Any]]:
        return self.manifest["events"]

    @property
    def dense_intervals(self) -> list[dict[str, Any]]:
        return self.manifest["dense_intervals"]

    def load_rgb(self, uid: int) -> torch.Tensor:
        uid = int(uid)
        cached = self._rgb_cache.get(uid)
        if cached is not None:
            return cached
        record = self.arrival_by_uid[uid]
        path = self.image_dir / record["source_name"]
        image = cv2.imread(str(path))
        if image is None:
            raise FileNotFoundError(path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height0, width0, _ = image.shape
        if len(self.calibration) > 4 and bool(self.preprocessing["undistort"]):
            camera_matrix = np.asarray(
                [
                    [self.calibration[0], 0, self.calibration[2]],
                    [0, self.calibration[1], self.calibration[3]],
                    [0, 0, 1],
                ]
            )
            image = cv2.undistort(
                image, camera_matrix, self.calibration[4:]
            )
        cropborder = int(self.preprocessing["cropborder"])
        if cropborder > 0:
            image = image[
                cropborder:-cropborder, cropborder:-cropborder
            ]
            height0, width0, _ = image.shape
        height1 = int(
            height0 * np.sqrt(TARGET_PIXELS / float(height0 * width0))
        )
        width1 = int(
            width0 * np.sqrt(TARGET_PIXELS / float(height0 * width0))
        )
        height1 -= height1 % 8
        width1 -= width1 % 8
        image = cv2.resize(image, (width1, height1))
        tensor = torch.as_tensor(image).permute(2, 0, 1).contiguous()
        expected = tuple(int(value) for value in self.preprocessing["output_image_size_hw"])
        if tuple(tensor.shape[-2:]) != expected:
            raise ValueError(
                f"preprocessed RGB shape {tuple(tensor.shape[-2:])} != {expected}"
            )
        self._rgb_cache[uid] = tensor
        return tensor

    @staticmethod
    def geometry_cache_key(reference: str | dict[str, Any]) -> str:
        if isinstance(reference, str):
            return reference
        return json.dumps(reference, sort_keys=True, separators=(",", ":"))

    def load_geometry(self, relative: str | dict[str, Any]) -> dict[str, Any]:
        cache_key = self.geometry_cache_key(relative)
        cached = self._geometry_cache.get(cache_key)
        if cached is not None:
            return cached
        if isinstance(relative, dict):
            depth_item = torch.load(
                self.root / relative["depth"], map_location="cpu", weights_only=False
            )
            normal_item = torch.load(
                self.root / relative["normal"], map_location="cpu", weights_only=False
            )
            if (
                depth_item.get("schema_version") != SCHEMA_VERSION
                or depth_item.get("tensor_kind") != "depth"
                or normal_item.get("schema_version") != SCHEMA_VERSION
                or normal_item.get("tensor_kind") != "normal"
            ):
                raise ValueError(f"split geometry schema mismatch: {relative}")
            value = {
                "schema_version": SCHEMA_VERSION,
                "frame_uid_at_capture": int(relative["frame_uid_at_capture"]),
                "sha256_tensor_payload": relative["sha256_tensor_payload"],
                "depth": depth_item["tensor"],
                "normal": normal_item["tensor"],
            }
            self._geometry_cache[cache_key] = value
            return value
        value = torch.load(
            self.root / relative, map_location="cpu", weights_only=False
        )
        if value.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(f"geometry schema mismatch: {relative}")
        self._geometry_cache[cache_key] = value
        return value

    def load_event_payload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        path = self.root / metadata["payload"]
        if sha256_file(path) != metadata["payload_sha256"]:
            raise ValueError(f"event hash mismatch: {path}")
        return torch.load(path, map_location="cpu", weights_only=False)

    def mapping_packet(
        self,
        metadata: dict[str, Any],
        *,
        filter_heldout: bool = True,
    ) -> dict[str, Any] | None:
        event = self.load_event_payload(metadata)
        if event["kind"] in {"metric_rescale", "mapper_reset"}:
            return None
        uids = event["frame_uids"].long()
        keep = torch.ones_like(uids, dtype=torch.bool)
        if filter_heldout:
            keep = torch.as_tensor(
                [int(uid) not in self.heldout_uids for uid in uids.tolist()],
                dtype=torch.bool,
            )
        if not bool(keep.any()):
            return None
        selected_positions = keep.nonzero(as_tuple=False).flatten().tolist()
        selected_uids = uids[keep]
        geometry = [
            self.load_geometry(event["geometry_refs"][position])
            for position in selected_positions
        ]
        pose_updates = None
        if event["pose_updates_data"] is not None:
            pose_updates = SE3(event["pose_updates_data"][keep].clone())
        packet = {
            # Local indexing is required after held-out filtering.  The
            # official PGBA branch indexes packet-local tstamp with viz_idx.
            "viz_idx": torch.arange(selected_uids.numel(), dtype=torch.long),
            "tstamp": selected_uids.float(),
            "poses": event["poses"][keep].clone(),
            "images": torch.stack(
                [self.load_rgb(int(uid)) for uid in selected_uids.tolist()]
            ),
            "normals": torch.stack([item["normal"] for item in geometry]),
            "depths": torch.stack([item["depth"] for item in geometry]),
            "intrinsics": event["intrinsics"][keep].clone(),
            "pose_updates": pose_updates,
            "scale_updates": (
                None
                if event["scale_updates"] is None
                else event["scale_updates"][keep].clone()
            ),
            "update_idx": None,
            "final": False,
        }
        return packet

    def load_dense_interval(self, metadata: dict[str, Any]) -> dict[str, Any]:
        path = self.root / metadata["payload"]
        if sha256_file(path) != metadata["payload_sha256"]:
            raise ValueError(f"dense interval hash mismatch: {path}")
        return torch.load(path, map_location="cpu", weights_only=False)

    def dense_records(
        self,
        metadata: dict[str, Any],
        *,
        seen_uids: set[int] | None = None,
    ) -> list[tuple[Any, ...]]:
        interval = self.load_dense_interval(metadata)
        output = []
        left_uid = int(interval["left_keyframe_uid"])
        right_uid = int(interval["right_keyframe_uid"])
        for uid_tensor, pose in zip(
            interval["candidate_uids"], interval["interpolated_poses_w2c"]
        ):
            uid = int(uid_tensor.item())
            if uid in self.heldout_uids or (
                seen_uids is not None and uid in seen_uids
            ):
                continue
            alpha = float(uid - left_uid) / float(right_uid - left_uid)
            output.append(
                (
                    uid,
                    self.load_rgb(uid).unsqueeze(0),
                    pose.clone(),
                    alpha,
                    left_uid,
                    right_uid,
                )
            )
            if seen_uids is not None:
                seen_uids.add(uid)
        return output


def timestamp_from_name(name: str, nanoseconds: bool) -> float:
    value = float(re.findall(r"[+]?(?:\d*\.\d+|\d+)", name)[-1])
    return value / 1e9 if nanoseconds else value
