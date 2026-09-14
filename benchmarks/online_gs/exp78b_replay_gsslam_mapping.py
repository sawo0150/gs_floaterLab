#!/usr/bin/env python3
"""Replay an exp78b frozen tracker trace through the current gsSLAM mapper.

This is a mapping-only adapter: tracker packets, poses, depth, normals, raw RGB
preprocessing, fixed held-out UIDs, control callbacks and wall-clock arrivals
all come from the same immutable archive used by the vanilla arm.  It does not
run tracking, final BA, color refinement, carve, or terminal pruning.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from types import MethodType

import numpy as np
import torch
import yaml


CUSTOM_ROOT = Path(
    os.environ.get(
        "EXP78B_CUSTOM_ROOT",
        "/home/intern/VIGS-SLAM-main-integration-20260828",
    )
)
WORKSPACE = Path("/home/intern/gs_floaterLab")
for source_root in (CUSTOM_ROOT / "vigs", CUSTOM_ROOT):
    value = str(source_root)
    if value not in sys.path:
        sys.path.insert(0, value)

from lietorch import SE3  # noqa: E402
import demo as custom_demo  # noqa: E402
import gs_backend as custom_gs_backend_module  # noqa: E402
from gs_backend import GSBackEnd  # noqa: E402
import gaussian.scene.gaussian_model as custom_gaussian_model_module  # noqa: E402

from exp78b_frozen_archive import FrozenTrackerArchive  # noqa: E402
from exp78b_dense_imu_pose import CausalImuDensePoseShaper  # noqa: E402
from exp78b_newborn_consolidation import (  # noqa: E402
    ObservationConditionedNewbornConsolidation,
)
from map_scheduler import (  # noqa: E402
    AdaptiveViewsetController,
    temporal_maximin_order,
)
from exp78b_timeline_scheduler import (  # noqa: E402
    ControlPreempted,
    DeadlineReached,
    FrozenTimelineScheduler,
    TimelineItem,
    build_frozen_timeline,
)


PROTOCOL = "exp78b_gsslam_frozen_mapping_replay_v27"


def install_relative_capacity_prune_closure(controller):
    """Close topology after repeated recovery from the first causal prune.

    This is a minimal-pruning diagnostic for the D1 state replay.  It observes
    neither a frame/iteration/horizon nor an absolute Gaussian count.  A net
    prune establishes a relative pre-prune recovery target; two *distinct*
    subsequent capacity observations at or above that target close topology
    while leaving the controller in its normal BALANCED optimization phase.
    """
    original_observe_capacity = controller.observe_capacity
    original_summary = controller.summary
    state = {
        "target": 0,
        "last_capacity": None,
        "recovery_observations": 0,
        "closures": 0,
    }

    def observe_capacity(self, gaussian_count, epochs_started):
        count = max(0, int(gaussian_count))
        epochs = max(0, int(epochs_started))
        if self.phase == self.FRONTIER and self.topology_observations > 0:
            target = max(0, int(self.latest_recovery_target))
            if target != state["target"]:
                state["target"] = target
                state["last_capacity"] = None
                state["recovery_observations"] = 0
            if target > 0 and count >= target:
                if count != state["last_capacity"]:
                    state["last_capacity"] = count
                    state["recovery_observations"] += 1
                if state["recovery_observations"] >= 2:
                    self.phase = self.BALANCED
                    self.replay_epoch_origin = epochs
                    self.transition_reason = (
                        "first_prune_repeated_relative_capacity_recovery"
                    )
                    state["closures"] += 1
                    return True
            else:
                state["last_capacity"] = None
                state["recovery_observations"] = 0
        elif self.topology_observations == 0:
            # Mapper resets reuse the controller instance.
            state["target"] = 0
            state["last_capacity"] = None
            state["recovery_observations"] = 0
        return original_observe_capacity(count, epochs)

    def summary(self):
        result = original_summary()
        result.update(
            {
                "relative_capacity_prune_closure": True,
                "relative_recovery_target": int(state["target"]),
                "relative_recovery_observations": int(
                    state["recovery_observations"]
                ),
                "relative_capacity_closures": int(state["closures"]),
            }
        )
        return result

    controller.observe_capacity = MethodType(observe_capacity, controller)
    controller.summary = MethodType(summary, controller)
    return state


class CausalOnlineRankDensity:
    """Dataset-name-free causal replacement for the Aria-fitted Sobel curve.

    The empirical rank uses only values observed no later than the current
    mapping view.  A cached frame UID always receives the same multiplier, so
    mapper resets or repeated packets cannot recalibrate on duplicate data.
    Mapping birth already normalizes point count by valid pixels; ranking makes
    the remaining content signal invariant to a sequence-wide Sobel scale.
    """

    def __init__(self, mean_multiplier: float, span: float) -> None:
        self.mean_multiplier = float(mean_multiplier)
        self.span = float(span)
        self.sorted_values: list[float] = []
        self.by_uid: dict[int, tuple[float, float, float]] = {}
        self.current_uid: int | None = None
        self.repeat_calls = 0
        self.repeat_sobel_max_abs_delta = 0.0

    def multiplier(
        self,
        sobel_mean: float,
        _curve_path: str,
        mult_min: float = 0.35,
        mult_max: float = 3.0,
    ) -> float:
        if self.current_uid is None:
            raise RuntimeError("online density called outside a mapped frame")
        uid = int(self.current_uid)
        if uid in self.by_uid:
            previous_sobel, _rank, multiplier = self.by_uid[uid]
            # Depth refinement changes the valid-pixel mask and can therefore
            # change the masked Sobel mean for the same RGB UID.  It is still
            # one physical observation: preserve its first causal allocation
            # rather than adding a duplicate calibration sample.
            self.repeat_calls += 1
            self.repeat_sobel_max_abs_delta = max(
                self.repeat_sobel_max_abs_delta,
                abs(previous_sobel - float(sobel_mean)),
            )
            return multiplier
        value = float(sobel_mean)
        count = len(self.sorted_values)
        left = bisect.bisect_left(self.sorted_values, value)
        right = bisect.bisect_right(self.sorted_values, value)
        # Mid-rank with a Jeffreys-like half observation keeps the first view
        # at q=0.5 and never emits the exact open-interval endpoints.
        rank = (0.5 * (left + right) + 0.5) / (count + 1.0)
        multiplier = self.mean_multiplier + self.span * (rank - 0.5)
        multiplier = float(min(max(multiplier, mult_min), mult_max))
        bisect.insort(self.sorted_values, value)
        self.by_uid[uid] = (value, float(rank), multiplier)
        return multiplier

    def summary(self) -> dict[str, object]:
        rows = [
            {
                "frame_uid": uid,
                "sobel_mean": values[0],
                "causal_rank": values[1],
                "multiplier": values[2],
            }
            for uid, values in sorted(self.by_uid.items())
        ]
        multipliers = np.asarray(
            [row["multiplier"] for row in rows], dtype=np.float64
        )
        return {
            "protocol": "exp78b_causal_online_sobel_rank_v1",
            "future_frames_used": False,
            "dataset_name_used": False,
            "duplicate_uid_recalibration": False,
            "repeat_calls_reused_first_multiplier": self.repeat_calls,
            "repeat_sobel_max_abs_delta": self.repeat_sobel_max_abs_delta,
            "mean_multiplier": self.mean_multiplier,
            "span": self.span,
            "unique_frames": len(rows),
            "observed_multiplier_mean": (
                None if not len(multipliers) else float(multipliers.mean())
            ),
            "observed_multiplier_min": (
                None if not len(multipliers) else float(multipliers.min())
            ),
            "observed_multiplier_max": (
                None if not len(multipliers) else float(multipliers.max())
            ),
            "per_frame": rows,
        }


class MinimumFirstServiceQueue:
    """Reserve sparse draws for causally arrived, never-served dense views.

    The wrapped queue remains authoritative for ordinary full-pool
    shuffle-without-replacement draws. Every ``period``-th draw is instead
    assigned FIFO to the oldest active dense view with zero selections. A
    view leaves the priority set after its first selection, whether that
    selection came from the reserved draw or the ordinary shuffle. Thus this
    is a minimum-service guarantee, not a persistent novelty or recency bias.

    This adapter deliberately supports only the unbounded CausalShuffleQueue
    used by exp78's dense-only mapping profile. Failing closed prevents a
    silent interaction with bounded or weighted epoch semantics.
    """

    def __init__(self, base, period: int) -> None:
        self._base = base
        self.period = int(period)
        if self.period <= 0:
            raise ValueError("minimum first-service period must be positive")
        required = (
            "_sync",
            "_queue",
            "_epoch_members",
            "_active_capacity",
            "_epoch_size",
            "_pool_pass_credit",
            "selection_counts",
            "draw_count",
        )
        missing = [name for name in required if not hasattr(base, name)]
        if missing:
            raise TypeError(f"replay queue lacks required state: {missing}")
        if base._active_capacity is not None or base._epoch_size is not None:
            raise ValueError(
                "minimum first-service adapter requires unbounded shuffle epochs"
            )
        self._known_active: set[object] = set()
        self._pending_fifo: collections.deque[object] = collections.deque()
        self._pending: set[object] = set()
        self.arrivals = 0
        self.ordinary_draws = 0
        self.reserved_draws = 0
        self.ordinary_first_services = 0
        self.stale_pending_drops = 0
        self.reset_count = 0

    def __getattr__(self, name):
        return getattr(self._base, name)

    @staticmethod
    def _is_dense(key: object) -> bool:
        return (
            isinstance(key, tuple)
            and len(key) >= 2
            and str(key[0]) == "dense"
        )

    def _register(self, candidates: set[object]) -> None:
        arrivals = candidates - self._known_active
        for key in sorted(arrivals, key=repr):
            if not self._is_dense(key):
                continue
            self._pending_fifo.append(key)
            self._pending.add(key)
            self.arrivals += 1
        removed = self._known_active - candidates
        for key in removed:
            self._pending.discard(key)
        self._known_active = set(candidates)

    def _oldest_unserved(self, candidates: set[object]):
        while self._pending_fifo:
            key = self._pending_fifo[0]
            if (
                key not in self._pending
                or key not in candidates
                or int(self._base.selection_counts[key]) > 0
            ):
                self._pending_fifo.popleft()
                if key in self._pending:
                    self._pending.discard(key)
                    self.stale_pending_drops += 1
                continue
            return key
        return None

    def _take_reserved(self, candidates: set[object]):
        # Synchronize first so a new arrival is also represented in the
        # wrapped queue's current epoch and can be removed exactly once.
        self._base._sync(candidates)
        key = self._oldest_unserved(candidates)
        if key is None:
            return None
        try:
            self._base._queue.remove(key)
        except ValueError as error:
            raise RuntimeError(
                f"unserved priority candidate missing from shuffle epoch: {key!r}"
            ) from error
        self._base._epoch_members.add(key)
        self._base.selection_counts[key] += 1
        self._base.draw_count += 1
        self._base._pool_pass_credit += 1.0 / max(1, len(candidates))
        self._pending.discard(key)
        self.reserved_draws += 1
        return key

    def draw(self, candidates, count: int = 1):
        candidates = set(candidates)
        count = max(0, int(count))
        self._register(candidates)
        if not candidates or count == 0:
            self._base.draw(candidates, 0)
            return []

        selected = []
        while len(selected) < count:
            use_reserved = (
                bool(self._pending)
                and (int(self._base.draw_count) + 1) % self.period == 0
            )
            key = self._take_reserved(candidates) if use_reserved else None
            if key is not None:
                selected.append(key)
                continue
            ordinary = self._base.draw(candidates, 1)
            if not ordinary:
                break
            key = ordinary[0]
            self.ordinary_draws += 1
            if key in self._pending:
                self._pending.discard(key)
                self.ordinary_first_services += 1
            selected.append(key)
        return selected

    def reset(self) -> None:
        self._base.reset()
        self._known_active.clear()
        self._pending_fifo.clear()
        self._pending.clear()
        self.reset_count += 1

    def summary(self, active_candidates):
        active = set(active_candidates)
        result = dict(self._base.summary(active))
        result.update(
            {
                "minimum_first_service_protocol": (
                    "causal_fifo_one_shot_every_k_draws_v1"
                ),
                "minimum_first_service_period": self.period,
                "minimum_first_service_arrivals": self.arrivals,
                "minimum_first_service_pending": len(self._pending & active),
                "minimum_first_service_reserved_draws": self.reserved_draws,
                "minimum_first_service_ordinary_draws": self.ordinary_draws,
                "minimum_first_service_ordinary_first_services": (
                    self.ordinary_first_services
                ),
                "minimum_first_service_stale_pending_drops": (
                    self.stale_pending_drops
                ),
                "minimum_first_service_reset_count": self.reset_count,
                "minimum_first_service_future_frames_used": False,
                "minimum_first_service_dataset_name_used": False,
            }
        )
        return result


class SourceQuotaReplayQueue:
    """Mix independent per-source shuffle streams at a causal fixed ratio.

    The stock unbounded queue accepts a keyframe fraction but only applies it
    to bounded epochs. Exp78 needs to isolate source allocation from
    working-set truncation, so this adapter keeps one ordinary unbounded
    shuffle-without-replacement queue per source and uses a residual-balanced
    clock only while both sources are currently available. Time before one
    source exists does not build debt that could later create a burst.

    The matched harness draws one view per optimizer step. Rejecting larger
    batches keeps both the source quota and per-step gradient scope explicit.
    """

    def __init__(self, base, keyframe_fraction: float) -> None:
        fraction = float(keyframe_fraction)
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("keyframe replay fraction must be in [0, 1]")
        required = (
            "_seed",
            "_active_capacity",
            "_epoch_size",
            "selection_counts",
            "draw",
            "reset",
        )
        missing = [name for name in required if not hasattr(base, name)]
        if missing:
            raise TypeError(f"replay queue lacks required state: {missing}")
        if base._active_capacity is not None or base._epoch_size is not None:
            raise ValueError(
                "source-quota adapter requires an unbounded shuffle queue"
            )
        queue_type = type(base)
        self._dense = base
        self._keyframe = queue_type(int(base._seed) + 32452843)
        self.keyframe_fraction = fraction
        self.selection_counts: collections.Counter = collections.Counter()
        self.draw_count = 0
        self._quota_residual = 0.0
        self._known_candidates: set[object] = set()
        self._pool_pass_credit = 0.0
        self.keyframe_draws = 0
        self.dense_draws = 0
        self.joint_availability_draws = 0
        self.joint_availability_keyframe_draws = 0
        self.keyframe_only_fallback_draws = 0
        self.dense_only_fallback_draws = 0
        self.reset_count = 0

    @staticmethod
    def _kind(key: object) -> str:
        if isinstance(key, tuple) and key:
            return str(key[0])
        return "candidate"

    @property
    def epochs_started(self) -> int:
        return int(self._dense.epochs_started + self._keyframe.epochs_started)

    @property
    def active_capacity(self):
        return None

    def set_active_capacity(self, capacity) -> None:
        if capacity is not None:
            raise ValueError("source-quota replay does not truncate its pools")

    def _target_kind(self, has_keyframes: bool, has_dense: bool) -> str:
        if has_keyframes and not has_dense:
            self.keyframe_only_fallback_draws += 1
            return "keyframe"
        if has_dense and not has_keyframes:
            self.dense_only_fallback_draws += 1
            return "dense"
        self.joint_availability_draws += 1
        self._quota_residual += self.keyframe_fraction
        if self._quota_residual >= 1.0:
            self._quota_residual -= 1.0
            self.joint_availability_keyframe_draws += 1
            return "keyframe"
        return "dense"

    def draw(self, candidates, count: int = 1):
        candidates = set(candidates)
        count = max(0, int(count))
        if count > 1:
            raise ValueError("source-quota replay requires one-view draws")
        keyframes = {key for key in candidates if self._kind(key) == "keyframe"}
        dense = {key for key in candidates if self._kind(key) == "dense"}
        unsupported = candidates - keyframes - dense
        if unsupported:
            raise ValueError(f"unsupported replay source keys: {unsupported!r}")
        if not candidates or count == 0:
            self._keyframe.draw(keyframes, 0)
            self._dense.draw(dense, 0)
            self._known_candidates = set(candidates)
            return []

        target = self._target_kind(bool(keyframes), bool(dense))
        source = self._keyframe if target == "keyframe" else self._dense
        source_candidates = keyframes if target == "keyframe" else dense
        selected = source.draw(source_candidates, 1)
        if len(selected) != 1:
            raise RuntimeError(f"{target} replay queue returned {selected!r}")
        key = selected[0]
        self.selection_counts[key] += 1
        self.draw_count += 1
        self._pool_pass_credit += 1.0 / max(1, len(candidates))
        if target == "keyframe":
            self.keyframe_draws += 1
        else:
            self.dense_draws += 1
        self._known_candidates = set(candidates)
        return selected

    def reset(self) -> None:
        self._dense.reset()
        self._keyframe.reset()
        self.selection_counts.clear()
        self.draw_count = 0
        self._quota_residual = 0.0
        self._known_candidates.clear()
        self._pool_pass_credit = 0.0
        self.keyframe_draws = 0
        self.dense_draws = 0
        self.joint_availability_draws = 0
        self.joint_availability_keyframe_draws = 0
        self.keyframe_only_fallback_draws = 0
        self.dense_only_fallback_draws = 0
        self.reset_count += 1

    def _working_set(self) -> set[object]:
        return set(self._dense._working_set) | set(self._keyframe._working_set)

    def summary(self, active_candidates):
        active = set(active_candidates)
        counts = [int(self.selection_counts[key]) for key in active]
        joint_draws = self.keyframe_draws + self.dense_draws
        working = self._working_set() & active
        return {
            "active_candidates": len(active),
            "working_candidates": len(working),
            "archive_candidates": len(active - working),
            "active_capacity": len(active),
            "queue_remaining": (
                len(self._dense._queue) + len(self._keyframe._queue)
            ),
            "epochs_started": self.epochs_started,
            "draw_count": self.draw_count,
            "selection_count_min": min(counts) if counts else 0,
            "selection_count_max": max(counts) if counts else 0,
            "epoch_size": 0,
            "new_slots": 0,
            "priority_new_pending": 0,
            "last_epoch_new": 0,
            "weight_floor": 0.0,
            "weight_bonus": 0.0,
            "weight_tau": 0.0,
            "last_weight_min": 0.0,
            "last_weight_max": 0.0,
            "last_weight_mean": 0.0,
            "weighted_members_total": 0,
            "weighted_new_total": 0,
            "weighted_new_fraction": 0.0,
            "weighted_full_epochs": 0,
            "weighted_full_new_fraction": 0.0,
            "admission_epochs_completed": 0,
            "source_quota_protocol": (
                "independent_unbounded_shuffle_residual_clock_v1"
            ),
            "source_quota_keyframe_fraction_requested": self.keyframe_fraction,
            "source_quota_keyframe_draws": self.keyframe_draws,
            "source_quota_dense_draws": self.dense_draws,
            "source_quota_keyframe_fraction_observed": (
                self.keyframe_draws / max(1, joint_draws)
            ),
            "source_quota_joint_availability_draws": (
                self.joint_availability_draws
            ),
            "source_quota_joint_keyframe_draws": (
                self.joint_availability_keyframe_draws
            ),
            "source_quota_joint_keyframe_fraction_observed": (
                self.joint_availability_keyframe_draws
                / max(1, self.joint_availability_draws)
            ),
            "source_quota_keyframe_only_fallback_draws": (
                self.keyframe_only_fallback_draws
            ),
            "source_quota_dense_only_fallback_draws": (
                self.dense_only_fallback_draws
            ),
            "source_quota_residual": self._quota_residual,
            "source_quota_reset_count": self.reset_count,
            "source_quota_future_frames_used": False,
            "source_quota_dataset_name_used": False,
        }

    def sampling_pool_epoch_clock(self) -> int:
        if not self._known_candidates:
            return 0
        return 1 + int(self._pool_pass_credit)

    def opportunity_epoch_clock(self) -> int:
        if not self._known_candidates:
            return 0
        return 1 + self.draw_count // len(self._known_candidates)

    def admission_epochs_completed(self) -> int:
        return 0

    def service_state(self, candidates, required_opportunities: int):
        candidates = set(candidates)
        required = max(1, int(required_opportunities))
        counts = {key: int(self.selection_counts[key]) for key in candidates}
        working = self._working_set() & candidates
        working_counts = [counts[key] for key in working]
        return {
            "candidates": len(candidates),
            "completed": sum(value >= required for value in counts.values()),
            "under_served": sum(value < required for value in counts.values()),
            "selection_count_min": min(counts.values()) if counts else 0,
            "working": len(working),
            "working_completed": sum(
                value >= required for value in working_counts
            ),
            "working_under_served": sum(
                value < required for value in working_counts
            ),
            "archive": len(candidates - working),
            "active_capacity": len(candidates),
        }


def configure_density_policy(
    config: dict,
    policy: str,
    mean_multiplier: float,
    span: float,
) -> tuple[dict[str, object], CausalOnlineRankDensity | None]:
    dataset = config.setdefault("Dataset", {})
    configured_curve = str(dataset.get("adaptive_density_curve", ""))
    metadata: dict[str, object] = {
        "policy": policy,
        "configured_curve": configured_curve,
        "configured_adaptive_density": bool(dataset.get("adaptive_density", False)),
    }
    calibrator = None
    if policy == "configured":
        if bool(dataset.get("adaptive_density", False)):
            if not configured_curve:
                raise ValueError("adaptive density is enabled without a curve")
            curve_path = Path(configured_curve)
            if not curve_path.is_absolute():
                curve_path = CUSTOM_ROOT / curve_path
            curve_path = curve_path.resolve()
            if not curve_path.is_file():
                raise FileNotFoundError(
                    f"configured adaptive-density curve is missing: {curve_path}"
                )
            dataset["adaptive_density_curve"] = str(curve_path)
            metadata.update(
                {
                    "effective_curve": str(curve_path),
                    "effective_curve_sha256": hashlib.sha256(
                        curve_path.read_bytes()
                    ).hexdigest(),
                }
            )
    elif policy == "disabled":
        dataset["adaptive_density"] = False
        metadata["effective_curve"] = None
    elif policy == "online_rank":
        if mean_multiplier <= 0.0 or span < 0.0:
            raise ValueError("online density mean must be positive and span non-negative")
        # D1's transferable birth recipe is a *bundle*: PPM performs the
        # content-weighted sampling and the causal rank replaces only the old
        # Aria-fitted multiplier curve.  Merely setting adaptive_density on an
        # upstream config is a silent no-op because GaussianModel consults the
        # multiplier only inside the PPM branch.  Pin the dataset-independent
        # base sampling budget here so B3 really evaluates the D1 mechanism.
        dataset["pcd_downsample"] = 256
        dataset["pcd_downsample_init"] = 64
        dataset["ppm_sampling"] = True
        dataset["adaptive_density"] = True
        dataset["adaptive_density_curve"] = "exp78b://causal-online-rank"
        dataset["adaptive_density_growth_allowance"] = 2.0
        calibrator = CausalOnlineRankDensity(mean_multiplier, span)
        metadata.update(
            {
                "effective_curve": "causal_online_rank",
                "mean_multiplier": float(mean_multiplier),
                "span": float(span),
                "effective_ppm_sampling": True,
                "effective_pcd_downsample": 256,
                "effective_pcd_downsample_init": 64,
                "effective_adaptive_density_growth_allowance": 2.0,
            }
        )
    else:
        raise ValueError(f"unsupported density policy: {policy}")
    metadata["effective_adaptive_density"] = bool(
        dataset.get("adaptive_density", False)
    )
    return metadata, calibrator


def install_online_density_policy(calibrator: CausalOnlineRankDensity) -> None:
    custom_gaussian_model_module.content_multiplier = calibrator.multiplier
    original = custom_gaussian_model_module.GaussianModel.create_pcd_from_image_and_depth

    def with_frame_uid(self, cam, *args, **kwargs):
        calibrator.current_uid = int(cam.tstamp)
        try:
            return original(self, cam, *args, **kwargs)
        finally:
            calibrator.current_uid = None

    custom_gaussian_model_module.GaussianModel.create_pcd_from_image_and_depth = (
        with_frame_uid
    )


def source_sha256(paths: list[Path]) -> dict[str, str]:
    return {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def runtime_provenance() -> dict[str, object]:
    module_paths = {}
    for name in (
        "diff_gaussian_rasterization",
        "simple_knn._C",
        "lietorch",
    ):
        try:
            module = __import__(name, fromlist=["*"])
            module_paths[name] = str(Path(module.__file__).resolve())
        except Exception as error:  # pragma: no cover - diagnostic only
            module_paths[name] = f"IMPORT_ERROR: {error!r}"
    active_sources = [
        Path(__file__),
        Path(__file__).with_name("exp78b_dense_imu_pose.py"),
        Path(__file__).with_name("exp78b_newborn_consolidation.py"),
        Path(custom_demo.__file__),
        Path(custom_gs_backend_module.__file__),
        Path(custom_gaussian_model_module.__file__),
        CUSTOM_ROOT / "vigs" / "map_scheduler.py",
        CUSTOM_ROOT / "vigs" / "gaussian" / "utils" / "content_budget.py",
    ]
    return {
        "working_directory": os.getcwd(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "cuda_device_name": torch.cuda.get_device_name(),
        "module_paths": module_paths,
        "active_source_sha256": source_sha256(active_sources),
        "custom_git_diff_sha256": hashlib.sha256(
            subprocess.check_output(
                ["git", "-C", str(CUSTOM_ROOT), "diff", "--binary"]
            )
        ).hexdigest(),
    }


class _CapturedNamespace(RuntimeError):
    def __init__(self, namespace: argparse.Namespace) -> None:
        super().__init__("captured parser namespace")
        self.namespace = namespace


def capture_demo_namespace(argv: list[str]) -> argparse.Namespace:
    """Use demo.py's authoritative parser without starting a VIGS run."""
    original = argparse.ArgumentParser.parse_args

    def capture(self, args=None, namespace=None):
        parsed = original(self, argv, namespace)
        raise _CapturedNamespace(parsed)

    argparse.ArgumentParser.parse_args = capture
    try:
        try:
            custom_demo.main()
        except _CapturedNamespace as result:
            parsed = result.namespace
        else:
            raise RuntimeError("demo parser capture unexpectedly entered the run")
    finally:
        argparse.ArgumentParser.parse_args = original
    custom_demo.resolve_fractional_frame_boundaries(parsed)
    return parsed


def mapper_namespace(
    archive: FrozenTrackerArchive,
    config_path: Path,
    output: Path,
    seed: int,
    time_scale: str,
    profile: str,
    auto_topology_freeze: bool,
    observation_topology_gate: bool,
    service_shortfall_ercb: bool,
    service_shortfall_global_epoch: bool,
    dense_max_endpoint_fraction: float,
    include_keyframes_in_replay: bool,
    official_frontier_parity: bool,
    fixed_work_dense_global_views: int,
    fixed_work_dense_selector: str,
    fixed_work_ercb_beta: float,
    fixed_work_ercb_block_size: int,
    fixed_iteration_projected_dense_selector: str,
    fixed_iteration_projected_dense_iters: int,
    fixed_iteration_projected_dense_batch_size: int,
    fixed_iteration_projected_dense_norm_ratio: float,
    fixed_iteration_projected_dense_geometry_norm_ratio: float,
    fixed_iteration_dedicated_dense_selector: str,
    fixed_iteration_dedicated_dense_iters: int,
    fixed_iteration_dedicated_dense_batch_size: int,
    fixed_iteration_dedicated_dense_scope: str,
) -> argparse.Namespace:
    image_dir = Path(archive.manifest["input_image_directory"])
    imu_file = Path(
        archive.manifest.get(
            "input_imu",
            image_dir.parent
            / (
                "imu_ours.txt"
                if archive.manifest["dataset"] == "utmm"
                else "imu.txt"
            ),
        )
    )
    if not imu_file.is_file():
        raise FileNotFoundError(f"could not infer archived IMU source: {imu_file}")
    argv = [
        "--imagedir", str(image_dir),
        "--imufile", str(imu_file),
        "--calib", str(archive.manifest["input_calibration"]),
        "--config", str(config_path),
        "--output", str(output),
        "--gsmapping",
        "--pure_online",
        "--realtime_replay",
        "--replay_time_scale", "1.0" if time_scale == "unbounded" else time_scale,
        "--eval_online_final",
        "--eval_metrics_only",
        "--mapping_exclude_fixed_eval_views",
        "--mapping_replay_deadline_guard",
        "--mapping_replay_iters", "1",
        "--mapping_replay_batch_size", "1",
        "--mapping_idle_replay_batch_size", "1",
        "--mapping_replay_tracking_reserve_ms", "0",
        "--mapping_replay_seed", str(seed),
        "--background_dense_pose_source", "interpolate",
        "--mapping_dense_max_endpoint_fraction",
        str(dense_max_endpoint_fraction),
        "--background_polish_idle_guard_ms", "0",
        "--background_polish_fast_loop",
        "--start", "0",
        "--length", str(len(archive.arrivals)),
        "--stride", "1",
        "--seed", str(seed),
    ]
    if official_frontier_parity:
        argv.extend(
            (
                "--late_mapping_start_frame", "0",
                "--late_mapping_iters", "10",
                "--enable_isotropic_loss",
            )
        )
    else:
        argv.extend(
            (
                "--mapping_after_imu_init",
                "--pgba_transform_xyz_adam_moments",
                "--pgba_correct_gaussian_quaternion_order",
            )
        )
    if profile in (
        "final_v7_scheduler",
        "d1_fixed_state_rr_imu",
        "dense_rr",
        "dense_rr_imu",
    ):
        argv.append("--idle_map_rr")
        if not include_keyframes_in_replay:
            argv.append("--mapping_replay_dense_only")
    if auto_topology_freeze:
        argv.append("--mapping_auto_topology_freeze")
    if observation_topology_gate:
        argv.append("--mapping_observation_topology_gate")
    if service_shortfall_ercb:
        argv.append("--mapping_replay_service_shortfall_ercb")
    if service_shortfall_global_epoch:
        if not service_shortfall_ercb:
            raise ValueError(
                "global-residue ERCB mapper mode requires service-shortfall ERCB"
            )
        argv.append("--mapping_replay_service_shortfall_global_epoch")
    if profile == "final_v7_scheduler":
        argv.extend(
            (
                "--mapping_model_scheduler",
                "--mapping_adaptive_viewset",
                "--mapping_pose_active_archive",
                "--mapping_work_credit_admission",
            )
        )
    elif profile == "d1_fixed_state_rr_imu":
        # Historical D1 spent physical Adam iterations on one-view dense
        # replay without advancing the frontier topology clock.  Preserve
        # that allocation, but replace its deprecated cadence-dependent
        # global freeze with final-v7's observation-only state transition.
        # Adaptive view-set/admission policies are intentionally absent here:
        # they were not part of D1 and belong in later contribution ablations.
        argv.append("--mapping_model_scheduler")
    elif profile not in ("dense_rr", "dense_rr_imu", "frontier_only"):
        raise ValueError(f"unsupported mapping profile: {profile}")
    parsed = capture_demo_namespace(argv)
    parsed.image_size = archive.manifest["preprocessing"]["output_image_size_hw"]
    parsed.length = len(archive.arrivals)
    parsed.start = 0
    parsed.stride = 1
    parsed.seed = seed
    parsed.mapping_dense_global_views = int(fixed_work_dense_global_views)
    parsed.mapping_dense_global_replay_scheduler = bool(
        fixed_work_dense_selector != "off"
    )
    if fixed_work_dense_selector == "ercb":
        parsed.mapping_replay_count_softmax_beta = float(
            fixed_work_ercb_beta
        )
        parsed.mapping_replay_count_softmax_block_size = int(
            fixed_work_ercb_block_size
        )
    elif fixed_work_dense_selector == "rr":
        parsed.mapping_replay_count_softmax_beta = -1.0
    parsed.mapping_dense_projected_replay_scheduler = bool(
        fixed_iteration_projected_dense_selector != "off"
    )
    parsed.mapping_dense_projected_iters = int(
        fixed_iteration_projected_dense_iters
    )
    parsed.mapping_dense_projected_batch_size = int(
        fixed_iteration_projected_dense_batch_size
    )
    parsed.mapping_dense_projected_norm_ratio = float(
        fixed_iteration_projected_dense_norm_ratio
    )
    parsed.mapping_dense_projected_geometry_norm_ratio = float(
        fixed_iteration_projected_dense_geometry_norm_ratio
    )
    if fixed_iteration_projected_dense_selector == "ercb":
        parsed.mapping_replay_count_softmax_beta = float(
            fixed_work_ercb_beta
        )
        parsed.mapping_replay_count_softmax_block_size = int(
            fixed_work_ercb_block_size
        )
    elif fixed_iteration_projected_dense_selector == "rr":
        parsed.mapping_replay_count_softmax_beta = -1.0
    parsed.mapping_dense_dedicated_iters = int(
        fixed_iteration_dedicated_dense_iters
    )
    parsed.mapping_dense_dedicated_batch_size = int(
        fixed_iteration_dedicated_dense_batch_size
    )
    parsed.mapping_dense_dedicated_replay_scheduler = bool(
        fixed_iteration_dedicated_dense_selector != "off"
    )
    parsed.mapping_dense_dedicated_parameter_scope = str(
        fixed_iteration_dedicated_dense_scope
    )
    if fixed_iteration_dedicated_dense_selector == "rr":
        parsed.mapping_replay_count_softmax_beta = -1.0
    return parsed


class BoundaryGuard:
    def __init__(self, deadline: float | None, reserve_seconds: float) -> None:
        self.deadline = deadline
        self.reserve_seconds = reserve_seconds
        self.next_control_due: float | None = None
        self.optimizer_steps_completed = 0
        self.main_gaussian_steps_completed = 0
        self.auxiliary_adam_steps_completed = 0
        self.optimizer_steps_rejected_at_deadline = 0
        self.topology_actions_rejected_at_deadline = 0
        self.control_preemptions = 0
        self.optimizer_completion_times: list[float] = []

    @property
    def enabled(self) -> bool:
        return self.deadline is not None

    def reject_if_unsafe(self, kind: str) -> None:
        now = time.monotonic()
        if self.next_control_due is not None and now >= self.next_control_due:
            self.control_preemptions += 1
            raise ControlPreempted(kind)
        if self.deadline is not None and now >= self.deadline - self.reserve_seconds:
            if kind == "optimizer":
                self.optimizer_steps_rejected_at_deadline += 1
            else:
                self.topology_actions_rejected_at_deadline += 1
            raise DeadlineReached(kind)


def install_adam_guard(mapper: GSBackEnd, guard: BoundaryGuard):
    original = torch.optim.Adam.step

    def guarded_step(optimizer, *args, **kwargs):
        guard.reject_if_unsafe("optimizer")
        if (
            optimizer is mapper.gaussians.optimizer
            and bool(getattr(mapper, "_exp78b_replay_scope_active", False))
        ):
            scope = str(
                getattr(mapper, "_exp78b_replay_gradient_scope", "full")
            )
            replay_keys = getattr(mapper, "_exp78b_current_replay_keys", ())
            if (
                bool(
                    getattr(
                        mapper,
                        "_exp78b_keyframe_replay_full_geometry",
                        False,
                    )
                )
                and len(replay_keys) == 1
                and replay_keys[0][0] == "keyframe"
            ):
                scope = "full"
            if scope == "adaptive_imu_curvature":
                threshold = float(
                    getattr(mapper, "_exp78b_replay_curvature_threshold_deg")
                )
                curvature_values = [
                    float(mapper._exp78b_dense_pose_shaper.curvature_by_uid[int(key[1])])
                    for key in replay_keys
                    if key[0] == "dense"
                ]
                scope = (
                    "full"
                    if curvature_values
                    and max(curvature_values) <= threshold
                    else "appearance"
                )
                mapper._exp78b_adaptive_scope_counts[scope] += 1
            elif scope == "adaptive_endpoint_geometry":
                threshold = float(
                    getattr(
                        mapper,
                        "_exp78b_replay_endpoint_geometry_fraction",
                    )
                )
                endpoint_distances = [
                    float(
                        getattr(
                            mapper.polish_viewpoints[int(key[1])],
                            "causal_endpoint_distance",
                            0.5,
                        )
                    )
                    for key in replay_keys
                    if key[0] == "dense" and int(key[1]) in mapper.polish_viewpoints
                ]
                scope = (
                    "full"
                    if endpoint_distances
                    and max(endpoint_distances) <= threshold
                    else "appearance"
                )
                mapper._exp78b_adaptive_scope_counts[scope] += 1
            elif scope == "adaptive_topology_maturation":
                scope = (
                    "appearance"
                    if bool(
                        getattr(
                            mapper,
                            "_mapping_auto_topology_frozen",
                            False,
                        )
                    )
                    else "full"
                )
                mapper._exp78b_adaptive_scope_counts[scope] += 1
            replay_source = (
                str(replay_keys[0][0]) if len(replay_keys) == 1 else "unknown"
            )
            mapper._exp78b_effective_replay_scope_counts[
                f"{replay_source}:{scope}"
            ] += 1
            allowed = {
                "full": {
                    "xyz",
                    "f_dc",
                    "f_rest",
                    "opacity",
                    "scaling",
                    "rotation",
                },
                "appearance": {"f_dc", "f_rest"},
                "appearance_opacity": {"f_dc", "f_rest", "opacity"},
            }[scope]
            for group in optimizer.param_groups:
                if group.get("name") not in allowed:
                    for parameter in group["params"]:
                        parameter.grad = None
        result = original(optimizer, *args, **kwargs)
        if guard.enabled:
            torch.cuda.synchronize()
            guard.optimizer_completion_times.append(time.monotonic())
        guard.optimizer_steps_completed += 1
        if optimizer is mapper.gaussians.optimizer:
            guard.main_gaussian_steps_completed += 1
        else:
            guard.auxiliary_adam_steps_completed += 1
        return result

    torch.optim.Adam.step = guarded_step
    return original


def install_topology_guard(mapper: GSBackEnd, guard: BoundaryGuard) -> None:
    gaussian = mapper.gaussians
    for name in (
        "densify_and_prune",
        "reset_opacity",
        "reset_opacity_nonvisible",
    ):
        original = getattr(gaussian, name, None)
        if original is None:
            continue

        def guarded(self, *args, __original=original, **kwargs):
            guard.reject_if_unsafe("topology")
            return __original(*args, **kwargs)

        setattr(gaussian, name, MethodType(guarded, gaussian))


def install_newborn_consolidation(
    mapper: GSBackEnd,
    controller: ObservationConditionedNewbornConsolidation,
) -> None:
    """Couple dense service evidence to per-lineage topology eligibility."""
    mapper._exp78b_newborn_consolidation_controller = controller
    queue = mapper._mapping_replay_queue
    original_draw = queue.draw

    def observed_draw(*args, **kwargs):
        keys = original_draw(*args, **kwargs)
        controller.observe_dense_draw(keys, mapper.polish_viewpoints)
        return keys

    queue.draw = observed_draw

    install_newborn_consolidation_gaussian(mapper, controller)


def install_newborn_consolidation_gaussian(
    mapper: GSBackEnd,
    controller: ObservationConditionedNewbornConsolidation,
) -> None:
    """Install the topology hook on the current post-reset Gaussian object."""
    gaussian = mapper.gaussians
    original_densify_and_prune = gaussian.densify_and_prune
    original_reset_opacity_nonvisible = gaussian.reset_opacity_nonvisible

    def consolidated(self, *args, **kwargs):
        epoch = int(mapper._mapping_replay_queue.epochs_started)
        point_ids_before = [
            int(value) for value in self.point_ids.detach().cpu().tolist()
        ]
        protected = controller.protected_point_ids(point_ids_before, epoch)
        inherited = {
            int(value) for value in (kwargs.get("protected_point_ids") or ())
        }
        protected.update(inherited)
        kwargs["protected_point_ids"] = protected
        protected_rows_before = sum(
            int(value in protected) for value in point_ids_before
        )
        gaussian_count_before = len(point_ids_before)
        result = original_densify_and_prune(*args, **kwargs)
        point_ids_after = [
            int(value) for value in self.point_ids.detach().cpu().tolist()
        ]
        protected_rows_after = sum(
            int(value in protected) for value in point_ids_after
        )
        gaussian_count_after = len(point_ids_after)
        controller.observe_topology_result(
            epochs_started=epoch,
            protected_points=len(protected),
            protected_rows_before=protected_rows_before,
            protected_rows_after=protected_rows_after,
            gaussian_count_before=gaussian_count_before,
            gaussian_count_after=gaussian_count_after,
        )
        print(
            "NEWBORN_CONSOLIDATION "
            f"epoch={epoch} protected_points={len(protected)} "
            f"protected_rows_before={protected_rows_before} "
            f"protected_rows_after={protected_rows_after} "
            f"before={gaussian_count_before} after={gaussian_count_after}",
            flush=True,
        )
        return result

    gaussian.densify_and_prune = MethodType(consolidated, gaussian)

    def consolidated_reset_opacity_nonvisible(
        self, visibility_filters, protected_mask=None
    ):
        epoch = int(mapper._mapping_replay_queue.epochs_started)
        point_ids = [
            int(value) for value in self.point_ids.detach().cpu().tolist()
        ]
        protected = controller.protected_point_ids(
            point_ids, epoch, record_query=False
        )
        newborn_mask = torch.isin(
            self.point_ids,
            torch.as_tensor(
                sorted(protected), dtype=self.point_ids.dtype
            ),
        ).to(device=self.get_xyz.device)
        combined_mask = (
            newborn_mask
            if protected_mask is None
            else torch.logical_or(
                protected_mask.to(newborn_mask.device), newborn_mask
            )
        )
        return original_reset_opacity_nonvisible(
            visibility_filters, protected_mask=combined_mask
        )

    gaussian.reset_opacity_nonvisible = MethodType(
        consolidated_reset_opacity_nonvisible, gaussian
    )


def install_render_telemetry(mapper: GSBackEnd) -> dict[str, int]:
    telemetry = {
        "map_calls": 0,
        "training_rasterized_view_updates": 0,
        "nontraining_rasterized_view_updates": 0,
        "frontier_packet_calls": 0,
        "idle_replay_calls": 0,
        "idle_replay_calls_completed": 0,
    }
    map_depth = 0
    original_map = mapper.map

    def counted_map(self, *args, **kwargs):
        nonlocal map_depth
        telemetry["map_calls"] += 1
        map_depth += 1
        try:
            return original_map(*args, **kwargs)
        finally:
            map_depth -= 1

    mapper.map = MethodType(counted_map, mapper)

    def wrap(name: str, batch: bool) -> None:
        original = getattr(custom_gs_backend_module, name)

        def counted(*args, **kwargs):
            count = len(args[0]) if batch else 1
            key = (
                "training_rasterized_view_updates"
                if map_depth
                else "nontraining_rasterized_view_updates"
            )
            telemetry[key] += int(count)
            return original(*args, **kwargs)

        setattr(custom_gs_backend_module, name, counted)

    wrap("render", False)
    wrap("render_batch", True)
    wrap("render_kernel_batch", True)
    return telemetry


def install_dense_imu_pose_refresh(
    mapper: GSBackEnd,
    shaper: CausalImuDensePoseShaper,
) -> None:
    """Reapply a camera-local IMU curvature residual after every KF refresh."""
    original = mapper._refresh_causal_dense_poses

    def refreshed(self):
        updated = original()
        for uid, residual_cpu in shaper.left_residual_by_uid.items():
            camera = self.polish_viewpoints.get(uid)
            if camera is None:
                continue
            pose = torch.eye(4, dtype=camera.R.dtype, device=camera.R.device)
            pose[:3, :3] = camera.R
            pose[:3, 3] = camera.T
            corrected = residual_cpu.to(
                device=pose.device, dtype=pose.dtype
            ) @ pose
            camera.update_RT(corrected[:3, :3], corrected[:3, 3])
            camera.dense_pose_source = "causal_raw_imu_rotation_shape"
            camera.dense_geometry_trusted = False
        return updated

    mapper._refresh_causal_dense_poses = MethodType(refreshed, mapper)


def install_dense_pose_confidence_weighting(mapper: GSBackEnd) -> None:
    """Weight dense appearance replay by endpoint interpolation confidence.

    For uniformly spaced samples within a keyframe interval, endpoint distance
    ``d=min(alpha, 1-alpha)`` is uniform on [0, 0.5].  Therefore
    ``4/3 * (1-d)`` has expectation one: it mildly favors better-constrained
    endpoint-near poses without changing the average gradient scale, dropping
    views, or consulting sequence-wide/future statistics.
    """
    original = mapper._frontier_mapping_view_loss
    mapper._exp78b_pose_confidence_stats = {
        "protocol": "causal_endpoint_linear_mean_one_v1",
        "calls": 0,
        "weight_sum": 0.0,
        "weight_min": float("inf"),
        "weight_max": -float("inf"),
        "future_frames_used": False,
        "dataset_name_used": False,
    }

    def weighted(self, image, depth, viewpoint, *args, **kwargs):
        loss = original(image, depth, viewpoint, *args, **kwargs)
        if (
            bool(getattr(self, "_exp78b_replay_scope_active", False))
            and getattr(viewpoint, "sensor_type", None) == "rgb_dense"
        ):
            distance = float(
                np.clip(
                    getattr(viewpoint, "causal_endpoint_distance", 0.5),
                    0.0,
                    0.5,
                )
            )
            weight = (4.0 / 3.0) * (1.0 - distance)
            stats = self._exp78b_pose_confidence_stats
            stats["calls"] += 1
            stats["weight_sum"] += weight
            stats["weight_min"] = min(stats["weight_min"], weight)
            stats["weight_max"] = max(stats["weight_max"], weight)
            return loss * weight
        return loss

    mapper._frontier_mapping_view_loss = MethodType(weighted, mapper)


def install_replay_selection_capture(mapper: GSBackEnd) -> None:
    original = mapper._mapping_replay_queue.draw

    def captured(*args, **kwargs):
        keys = original(*args, **kwargs)
        mapper._exp78b_current_replay_keys = tuple(keys)
        return keys

    mapper._mapping_replay_queue.draw = captured


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def save_shared_trajectories(archive: FrozenTrackerArchive, output: Path) -> None:
    evaluation = torch.load(
        archive.root / archive.manifest["evaluation_only_post_eos_trajectory"],
        map_location="cpu",
        weights_only=False,
    )
    final_state = torch.load(
        archive.root / archive.manifest["final_tracker_state"],
        map_location="cpu",
        weights_only=False,
    )
    timestamps = np.asarray(
        [float(record["sensor_timestamp"]) for record in archive.arrivals],
        dtype=np.float64,
    )
    np.savetxt(
        output / "traj_full_beforeBA.txt",
        np.concatenate((timestamps[:, None], evaluation["poses_c2w_vector"].numpy()), axis=1),
    )
    keyframe_c2w = SE3(final_state["keyframe_poses_w2c"]).inv().data.numpy()
    np.savetxt(
        output / "traj_kf_beforeBA.txt",
        np.concatenate(
            (final_state["keyframe_sensor_timestamps"].numpy()[:, None], keyframe_c2w),
            axis=1,
        ),
    )
    np.save(
        output / "intrinsics.npy",
        final_state["keyframe_intrinsics_full_resolution"][0].numpy(),
    )


def scale_pending_dense(records: list[tuple], scale: float) -> None:
    for record in records:
        pose = record[2]
        pose[:3, 3] *= float(scale)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--time-scale", choices=("unbounded", "1.0", "1.5"), default="1.5"
    )
    parser.add_argument("--deadline-reserve-ms", type=float, default=50.0)
    parser.add_argument(
        "--mapping-after-metric-init",
        action="store_true",
        help=(
            "apply the common B fixed-work gate: packets before the causal "
            "metric-rescale event consume no mapping credit"
        ),
    )
    parser.add_argument(
        "--official-frontier-parity",
        action="store_true",
        help=(
            "restore official frontier10/isotropic/PGBA behavior on the "
            "custom code path; valid for frontier_only or the fixed-work "
            "dense-slot isolation path"
        ),
    )
    parser.add_argument(
        "--fixed-work-dense-global-views",
        type=int,
        default=0,
        help=(
            "replace this many already-budgeted historical/global KF slots "
            "with causal dense views in regular map() calls; fixed-work only"
        ),
    )
    parser.add_argument(
        "--fixed-work-dense-selector",
        choices=("off", "rr", "ercb"),
        default="off",
        help=(
            "selector for fixed-work dense global-slot replacement; this "
            "does not enable idle replay"
        ),
    )
    parser.add_argument(
        "--fixed-work-ercb-beta",
        type=float,
        default=0.02,
    )
    parser.add_argument(
        "--fixed-work-ercb-block-size",
        type=int,
        default=128,
    )
    parser.add_argument(
        "--fixed-iteration-projected-dense-selector",
        choices=("off", "rr", "ercb"),
        default="off",
        help=(
            "preserve the ordinary KF backward and add a scheduled dense "
            "projected gradient inside the same physical Adam iteration"
        ),
    )
    parser.add_argument(
        "--fixed-iteration-projected-dense-iters",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--fixed-iteration-projected-dense-batch-size",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--fixed-iteration-projected-dense-norm-ratio",
        type=float,
        default=0.25,
    )
    parser.add_argument(
        "--fixed-iteration-projected-dense-geometry-norm-ratio",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--fixed-iteration-dedicated-dense-selector",
        choices=("off", "rr"),
        default="off",
        help=(
            "allocate final iterations of each regular map call to causal "
            "dense-only Adam steps without changing the physical iteration count"
        ),
    )
    parser.add_argument(
        "--fixed-iteration-dedicated-dense-iters",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--fixed-iteration-dedicated-dense-batch-size",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--fixed-iteration-dedicated-dense-scope",
        choices=("full", "appearance", "appearance_opacity"),
        default="appearance",
    )
    parser.add_argument(
        "--compute-paced-dense-admission",
        action="store_true",
        help=(
            "admit one global causal dense seed, then one already-arrived "
            "view per completed-work token; unused credit is discarded "
            "while no candidate waits"
        ),
    )
    parser.add_argument(
        "--compute-paced-dense-token-cost",
        type=int,
        default=22,
        help="completed projected dense-view updates per paid admission",
    )
    parser.add_argument(
        "--service-shortfall-ercb",
        action="store_true",
        help=(
            "paper Stage 3: replace only dense RR ordering with "
            "K8/rho.75/gamma=log1.5 service-shortfall ERCB; use with either "
            "fixed C1 admission or explicit Stage-3c C1-off isolation"
        ),
    )
    parser.add_argument(
        "--fixed-event-dense-opportunities-per-packet",
        type=int,
        default=0,
        help=(
            "Stage-3 ordering isolation: in unbounded causal replay, offer "
            "one independent dense Adam opportunity after each completed "
            "mapping packet; 0 disables"
        ),
    )
    parser.add_argument(
        "--c2-orthogonal-isolation",
        action="store_true",
        help=(
            "Stage-3c only: keep the fixed-event Stage-1 D1 backbone but "
            "disable C1 admission so RR versus service-shortfall ERCB changes "
            "ordering over the complete causally arrived dense pool"
        ),
    )
    parser.add_argument(
        "--c2-global-residue-isolation",
        action="store_true",
        help=(
            "Stage-3d only: repeat Stage-3c with the repaired C2 arm "
            "conditioned on the remaining global reshuffling epoch"
        ),
    )
    parser.add_argument(
        "--c1-c2-global-residue-integration",
        action="store_true",
        help=(
            "Stage-4 only: enable the accepted C1 admission policy in both "
            "arms and opt the service-shortfall arm into the repaired "
            "global-residue C2 semantics"
        ),
    )
    parser.add_argument(
        "--density-policy",
        choices=("configured", "disabled", "online_rank"),
        default="configured",
        help=(
            "configured resolves the YAML curve under the custom repo and "
            "fails if missing; disabled uses the fixed base point budget"
        ),
    )
    parser.add_argument(
        "--online-density-mean-multiplier",
        type=float,
        default=2.0,
    )
    parser.add_argument(
        "--online-density-span",
        type=float,
        default=2.0,
        help="rank q maps to mean + span * (q - 0.5)",
    )
    parser.add_argument(
        "--dense-replay-scope",
        choices=(
            "full",
            "appearance",
            "appearance_opacity",
            "adaptive_imu_curvature",
            "adaptive_endpoint_geometry",
            "adaptive_topology_maturation",
        ),
        default="full",
        help="Gaussian parameter groups updated by idle dense replay only",
    )
    parser.add_argument(
        "--dense-replay-curvature-threshold-deg",
        type=float,
        default=1.0,
        help=(
            "for adaptive_imu_curvature, allow full Gaussian updates only "
            "when raw-gyro within-endpoint curvature is at most this value"
        ),
    )
    parser.add_argument(
        "--dense-replay-endpoint-geometry-fraction",
        type=float,
        default=0.1,
        help=(
            "for adaptive_endpoint_geometry, allow full Gaussian updates "
            "only for dense views within this normalized distance of an "
            "already-arrived keyframe endpoint"
        ),
    )
    parser.add_argument(
        "--profile",
        choices=(
            "final_v7_scheduler",
            "d1_fixed_state_rr_imu",
            "dense_rr",
            "dense_rr_imu",
            "frontier_only",
        ),
        default="final_v7_scheduler",
    )
    parser.add_argument(
        "--auto-topology-freeze",
        action="store_true",
        help=(
            "freeze native densify/prune once causal births double the "
            "post-topology model; new keyframe births remain enabled"
        ),
    )
    parser.add_argument(
        "--observation-topology-gate",
        action="store_true",
        help=(
            "paper Stage 1: replace historical cadence auto-freeze with "
            "the isolated observation-driven topology permission gate"
        ),
    )
    parser.add_argument(
        "--relative-capacity-prune-closure",
        action="store_true",
        help=(
            "D1 diagnostic: after a net prune, close further topology only "
            "after two distinct observations recover its relative pre-prune "
            "capacity; mapping and birth continue"
        ),
    )
    parser.add_argument(
        "--d1-preserve-full-frontier",
        action="store_true",
        help=(
            "fixed-iteration D1 port: retain every B1 multi-view frontier "
            "iteration while final-v7 observation state controls topology; "
            "dense supervision is separately projected into the same Adam step"
        ),
    )
    parser.add_argument(
        "--observation-conditioned-newborn-consolidation",
        action="store_true",
        help=(
            "protect immature keyframe-origin births from clone/split and "
            "prune until final-v7 repeated dense-service evidence matures them"
        ),
    )
    parser.add_argument(
        "--new-view-service-period",
        type=int,
        default=0,
        help=(
            "reserve every K-th dense replay draw for the oldest causally "
            "available view that has never been selected; 0 disables"
        ),
    )
    parser.add_argument(
        "--dense-pose-confidence-weighting",
        action="store_true",
        help=(
            "during dense replay, apply mean-one linear confidence based only "
            "on distance to the two already-arrived keyframe endpoints"
        ),
    )
    parser.add_argument(
        "--dense-pose-refresh-every-packet",
        action="store_true",
        help=(
            "after each completed causal tracker packet, refresh registered "
            "dense poses from the latest already-arrived keyframe endpoints"
        ),
    )
    parser.add_argument(
        "--dense-pose-refresh-period",
        type=int,
        default=1,
        help=(
            "when packet refresh is enabled, refresh after every N completed "
            "causal tracker packets"
        ),
    )
    parser.add_argument(
        "--dense-max-endpoint-fraction",
        type=float,
        default=0.5,
        help=(
            "only admit causally bracketed dense views whose normalized "
            "distance to the nearer arrived keyframe endpoint is at most "
            "this value; 0.5 admits the full interval"
        ),
    )
    parser.add_argument(
        "--include-keyframes-in-replay",
        action="store_true",
        help=(
            "include causally arrived, non-held-out RGB-D keyframes in the "
            "same per-view uniform replay pool as dense RGB"
        ),
    )
    parser.add_argument(
        "--keyframe-replay-fraction",
        type=float,
        default=-1.0,
        help=(
            "when non-negative, mix independent causal keyframe and dense "
            "shuffle streams at this long-run keyframe draw fraction"
        ),
    )
    parser.add_argument(
        "--keyframe-replay-full-geometry",
        action="store_true",
        help=(
            "apply the configured dense gradient restriction only to dense "
            "replay; single-keyframe replay retains full RGB-D geometry"
        ),
    )
    args = parser.parse_args()

    if args.new_view_service_period < 0:
        raise ValueError("new-view service period must be non-negative")
    if args.dense_pose_refresh_period <= 0:
        raise ValueError("dense-pose refresh period must be positive")
    if not 0.0 <= args.dense_max_endpoint_fraction <= 0.5:
        raise ValueError("dense max endpoint fraction must be in [0, 0.5]")
    if not 0.0 <= args.dense_replay_endpoint_geometry_fraction <= 0.5:
        raise ValueError(
            "dense replay endpoint geometry fraction must be in [0, 0.5]"
        )
    if (
        args.dense_replay_scope == "adaptive_topology_maturation"
        and not args.auto_topology_freeze
    ):
        raise ValueError(
            "adaptive topology maturation requires --auto-topology-freeze"
        )
    if args.observation_topology_gate and args.auto_topology_freeze:
        raise ValueError(
            "observation topology gate and auto topology freeze are "
            "mutually exclusive"
        )
    if (
        args.observation_topology_gate
        and args.profile != "dense_rr_imu"
    ):
        raise ValueError(
            "paper Stage 1 observation topology gate requires the exact "
            "D1 dense_rr_imu profile"
        )
    if args.new_view_service_period and args.profile not in ("dense_rr", "dense_rr_imu"):
        raise ValueError(
            "new-view first service is defined only for dense_rr profiles"
        )
    if args.fixed_work_dense_global_views < 0:
        raise ValueError("fixed-work dense global views must be non-negative")
    if args.fixed_work_ercb_beta < 0.0:
        raise ValueError("fixed-work ERCB beta must be non-negative")
    if args.fixed_work_ercb_block_size <= 0:
        raise ValueError("fixed-work ERCB block size must be positive")
    fixed_work_dense_enabled = args.fixed_work_dense_global_views > 0
    fixed_iteration_projected_enabled = (
        args.fixed_iteration_projected_dense_selector != "off"
    )
    fixed_iteration_dedicated_enabled = (
        args.fixed_iteration_dedicated_dense_selector != "off"
    )
    if fixed_iteration_projected_enabled and fixed_iteration_dedicated_enabled:
        raise ValueError(
            "projected and dedicated fixed-iteration dense modes are mutually exclusive"
        )
    if fixed_iteration_dedicated_enabled != (
        args.fixed_iteration_dedicated_dense_iters > 0
    ):
        raise ValueError(
            "dedicated dense selector and positive iteration allocation must be enabled together"
        )
    if fixed_iteration_dedicated_enabled and not (
        args.time_scale == "unbounded"
        and args.mapping_after_metric_init
        and args.profile in ("dense_rr", "dense_rr_imu")
        and args.official_frontier_parity
        and not args.auto_topology_freeze
    ):
        raise ValueError(
            "dedicated dense allocation requires fixed-iteration work mode, "
            "official frontier parity, ordinary topology, and no global freeze"
        )
    if args.fixed_iteration_dedicated_dense_iters < 0:
        raise ValueError("dedicated dense iterations must be non-negative")
    if args.fixed_iteration_dedicated_dense_batch_size <= 0:
        raise ValueError("dedicated dense batch size must be positive")
    if args.observation_conditioned_newborn_consolidation and not (
        args.time_scale == "unbounded"
        and args.mapping_after_metric_init
        and args.profile in ("dense_rr", "dense_rr_imu")
        and args.official_frontier_parity
        and (fixed_iteration_projected_enabled or fixed_iteration_dedicated_enabled)
        and args.density_policy == "online_rank"
        and not args.auto_topology_freeze
    ):
        raise ValueError(
            "observation-conditioned newborn consolidation requires the "
            "fixed-iteration projected-dense online-rank birth arm with "
            "ordinary topology and no global freeze"
        )
    if fixed_work_dense_enabled != (args.fixed_work_dense_selector != "off"):
        raise ValueError(
            "fixed-work dense views and selector must be enabled together"
        )
    if fixed_work_dense_enabled and not (
        args.time_scale == "unbounded"
        and args.mapping_after_metric_init
        and args.profile in ("dense_rr", "dense_rr_imu")
        and args.official_frontier_parity
    ):
        raise ValueError(
            "fixed-work dense slots require unbounded work mode, the common "
            "metric-init gate, a dense profile, and official frontier parity"
        )
    if args.fixed_iteration_projected_dense_iters < 0:
        raise ValueError("fixed-iteration projected dense iters must be non-negative")
    if args.fixed_iteration_projected_dense_batch_size <= 0:
        raise ValueError("fixed-iteration projected dense batch must be positive")
    if not 0.0 < args.fixed_iteration_projected_dense_norm_ratio <= 1.0:
        raise ValueError("fixed-iteration projected dense norm ratio must be in (0,1]")
    if not 0.0 <= args.fixed_iteration_projected_dense_geometry_norm_ratio <= 1.0:
        raise ValueError(
            "fixed-iteration projected dense geometry norm ratio must be in [0,1]"
        )
    if fixed_iteration_projected_enabled != (
        args.fixed_iteration_projected_dense_iters > 0
    ):
        raise ValueError(
            "fixed-iteration projected selector and positive iters must be enabled together"
        )
    if fixed_iteration_projected_enabled and not (
        args.time_scale == "unbounded"
        and args.mapping_after_metric_init
        and (
            args.profile in ("dense_rr", "dense_rr_imu")
            or (
                args.profile == "d1_fixed_state_rr_imu"
                and args.d1_preserve_full_frontier
            )
        )
        and args.official_frontier_parity
        and not fixed_work_dense_enabled
    ):
        raise ValueError(
            "fixed-iteration projected dense requires unbounded work mode, "
            "the common metric-init gate, a dense profile, official frontier "
            "parity, and no dense global-slot replacement"
        )
    if args.compute_paced_dense_token_cost <= 0:
        raise ValueError("compute-paced dense token cost must be positive")
    native_d1_dense_service_clock = (
        args.profile == "dense_rr_imu"
        and args.observation_topology_gate
        and not args.auto_topology_freeze
        and not args.official_frontier_parity
        and not fixed_work_dense_enabled
        and not fixed_iteration_dedicated_enabled
    )
    if args.compute_paced_dense_admission and not (
        fixed_iteration_projected_enabled
        or native_d1_dense_service_clock
    ):
        raise ValueError(
            "compute-paced dense admission requires either the fixed-iteration "
            "projected clock or the Stage-1 native independent-dense clock"
        )
    stage3c_c2_orthogonal_isolation = bool(args.c2_orthogonal_isolation)
    stage3d_c2_global_residue_isolation = bool(
        args.c2_global_residue_isolation
    )
    stage4_c1_c2_global_residue_integration = bool(
        args.c1_c2_global_residue_integration
    )
    if sum(
        int(value)
        for value in (
            stage3c_c2_orthogonal_isolation,
            stage3d_c2_global_residue_isolation,
            stage4_c1_c2_global_residue_integration,
        )
    ) > 1:
        raise ValueError(
            "Stage-3c, Stage-3d, and Stage-4 modes are mutually exclusive"
        )
    c2_full_pool_isolation = bool(
        stage3c_c2_orthogonal_isolation
        or stage3d_c2_global_residue_isolation
    )
    c2_global_residue_semantics = bool(
        stage3d_c2_global_residue_isolation
        or stage4_c1_c2_global_residue_integration
    )
    selector_audit_required = bool(
        c2_full_pool_isolation
        or stage4_c1_c2_global_residue_integration
    )
    if stage4_c1_c2_global_residue_integration and not (
        args.compute_paced_dense_admission
        and args.fixed_event_dense_opportunities_per_packet == 1
    ):
        raise ValueError(
            "Stage-4 C1+C2 integration requires compute-paced C1 and one "
            "fixed dense opportunity per eligible mapping packet"
        )
    if args.service_shortfall_ercb and not (
        native_d1_dense_service_clock
        and not args.include_keyframes_in_replay
        and args.new_view_service_period == 0
        and (
            args.compute_paced_dense_admission
            or c2_full_pool_isolation
        )
    ):
        raise ValueError(
            "service-shortfall ERCB requires either the isolated Stage-2 C1 "
            "path or explicit Stage-3c/3d C2 isolation, plus native D1 "
            "dense-only replay and no ordering adapter"
        )
    if args.fixed_event_dense_opportunities_per_packet not in (0, 1):
        raise ValueError(
            "fixed-event dense opportunities must be the predeclared 0 or 1"
        )
    fixed_event_dense_isolation = bool(
        args.fixed_event_dense_opportunities_per_packet
    )
    if selector_audit_required and not fixed_event_dense_isolation:
        raise ValueError(
            "Stage-3c/3d/4 comparison requires one fixed dense opportunity "
            "per eligible mapping packet"
        )
    if fixed_event_dense_isolation and not (
        args.time_scale == "unbounded"
        and (
            (
                c2_full_pool_isolation
                and not args.compute_paced_dense_admission
            )
            or (
                not c2_full_pool_isolation
                and args.compute_paced_dense_admission
            )
        )
        and native_d1_dense_service_clock
        and args.observation_topology_gate
        and args.profile == "dense_rr_imu"
        and args.dense_replay_scope == "appearance"
        and args.density_policy == "online_rank"
        and not args.auto_topology_freeze
        and not args.official_frontier_parity
        and not fixed_work_dense_enabled
        and not fixed_iteration_projected_enabled
        and not fixed_iteration_dedicated_enabled
        and not args.include_keyframes_in_replay
        and args.new_view_service_period == 0
    ):
        raise ValueError(
            "fixed-event dense isolation requires unbounded native D1, "
            "observation topology, online-rank birth, independent "
            "appearance-only dense replay, no ordering/work adapter, and "
            "exactly one of Stage-2/4 C1 or a Stage-3c/3d C2-only mode"
        )
    if args.relative_capacity_prune_closure and not (
        args.time_scale == "unbounded"
        and args.mapping_after_metric_init
        and args.profile == "d1_fixed_state_rr_imu"
        and args.official_frontier_parity
        and not args.auto_topology_freeze
    ):
        raise ValueError(
            "relative-capacity prune closure requires the fixed-work D1 "
            "profile, official frontier parity, and no global auto-freeze"
        )
    if args.d1_preserve_full_frontier and not (
        args.time_scale == "unbounded"
        and args.mapping_after_metric_init
        and args.profile == "d1_fixed_state_rr_imu"
        and args.official_frontier_parity
        and fixed_iteration_projected_enabled
        and not args.auto_topology_freeze
    ):
        raise ValueError(
            "full-frontier D1 requires fixed-iteration work mode, the D1 "
            "observation-state profile, official frontier parity, projected "
            "dense supervision, and no global auto-freeze"
        )
    if args.official_frontier_parity and not (
        args.profile == "frontier_only"
        or args.profile == "d1_fixed_state_rr_imu"
        or fixed_work_dense_enabled
        or fixed_iteration_projected_enabled
        or fixed_iteration_dedicated_enabled
    ):
        raise ValueError(
            "--official-frontier-parity requires frontier_only or a "
            "fixed-iteration dense isolation path"
        )
    if not (
        args.keyframe_replay_fraction == -1.0
        or 0.0 <= args.keyframe_replay_fraction <= 1.0
    ):
        raise ValueError("keyframe replay fraction must be -1 or in [0, 1]")
    if args.keyframe_replay_fraction >= 0.0:
        if not args.include_keyframes_in_replay:
            raise ValueError(
                "keyframe replay fraction requires --include-keyframes-in-replay"
            )
        if args.new_view_service_period:
            raise ValueError(
                "source quota conflicts with the minimum first-service adapter"
            )
        if args.profile not in ("dense_rr", "dense_rr_imu"):
            raise ValueError("source quota requires a dense_rr replay profile")
    if args.keyframe_replay_full_geometry and args.keyframe_replay_fraction < 0.0:
        raise ValueError(
            "full-geometry keyframe replay requires an explicit source quota"
        )

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = FrozenTrackerArchive(args.archive)
    config_path = args.config.resolve()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.cuda.reset_peak_memory_stats()
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    density_policy, online_density = configure_density_policy(
        config,
        args.density_policy,
        args.online_density_mean_multiplier,
        args.online_density_span,
    )
    if online_density is not None:
        install_online_density_policy(online_density)
    effective_config_sha256 = hashlib.sha256(
        json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    mapper_args = mapper_namespace(
        archive,
        config_path,
        output,
        args.seed,
        args.time_scale,
        args.profile,
        args.auto_topology_freeze,
        args.observation_topology_gate,
        args.service_shortfall_ercb,
        bool(
            args.service_shortfall_ercb
            and c2_global_residue_semantics
        ),
        args.dense_max_endpoint_fraction,
        args.include_keyframes_in_replay,
        args.official_frontier_parity,
        args.fixed_work_dense_global_views,
        args.fixed_work_dense_selector,
        args.fixed_work_ercb_beta,
        args.fixed_work_ercb_block_size,
        args.fixed_iteration_projected_dense_selector,
        args.fixed_iteration_projected_dense_iters,
        args.fixed_iteration_projected_dense_batch_size,
        args.fixed_iteration_projected_dense_norm_ratio,
        args.fixed_iteration_projected_dense_geometry_norm_ratio,
        args.fixed_iteration_dedicated_dense_selector,
        args.fixed_iteration_dedicated_dense_iters,
        args.fixed_iteration_dedicated_dense_batch_size,
        args.fixed_iteration_dedicated_dense_scope,
    )
    mapper = GSBackEnd(config, str(output), mapper_args, use_gui=False)
    relative_capacity_prune_state = None
    if args.relative_capacity_prune_closure:
        relative_capacity_prune_state = install_relative_capacity_prune_closure(
            mapper._mapping_model_controller
        )
    if args.profile == "d1_fixed_state_rr_imu":
        # Fixed-event B holds physical Adam iterations constant.  A PGBA
        # revision still consumes final-v7's one-shot causal recovery state,
        # but it must not silently shrink the event's pre-existing credit.
        original_structural_iterations = (
            mapper._mapping_model_controller.structural_iterations
        )

        def fixed_credit_structural_iterations(requested, window_size):
            original_structural_iterations(requested, window_size)
            return max(0, int(requested))

        mapper._mapping_model_controller.structural_iterations = (
            fixed_credit_structural_iterations
        )
        if args.d1_preserve_full_frontier:
            original_foreground_allocation = (
                mapper._mapping_model_controller.foreground_allocation
            )

            def full_frontier_allocation(requested, window_size, worker_saturated):
                # Retain causal state observations, but fixed-iteration B must
                # never trade away a reference frontier gradient. Dense work
                # is separately accounted by the projected-gradient path.
                original_foreground_allocation(
                    requested, window_size, worker_saturated
                )
                return max(0, int(requested)), 0

            mapper._mapping_model_controller.foreground_allocation = (
                full_frontier_allocation
            )
        else:
            original_state_map = mapper.map

            def fixed_credit_state_map(
                self, current_window, iters, *positional, **kwargs
            ):
                # Direct replay and PGBA recovery already carry an explicit work
                # role.  Only ordinary frontier dispatch needs to be partitioned.
                if (
                    kwargs.get("replay_only", False)
                    or kwargs.get("structural_recovery", False)
                    or kwargs.get("terminal_geometry_commit", False)
                ):
                    return original_state_map(
                        current_window, iters, *positional, **kwargs
                    )

                available_window = [
                    int(uid)
                    for uid in current_window
                    if int(uid) in self.viewpoints
                    and not bool(
                        getattr(
                            self.viewpoints[int(uid)],
                            "mapping_eval_excluded",
                            False,
                        )
                    )
                ]
                requested = max(0, int(iters))
                if requested == 0 or not available_window:
                    return original_state_map(
                        current_window, iters, *positional, **kwargs
                    )

                newest_frame = max(available_window)
                self._update_mapping_model_state(newest_frame)
                frontier_iters = self._mapping_model_controller.normal_iterations(
                    requested, len(available_window)
                )
                replay_iters = requested - frontier_iters

                frontier_completed = 0
                if frontier_iters > 0:
                    frontier_kwargs = dict(kwargs)
                    frontier_kwargs["foreground_saturated"] = False
                    frontier_completed = original_state_map(
                        current_window,
                        frontier_iters,
                        *positional,
                        **frontier_kwargs,
                    ) or 0

                replay_completed = 0
                if replay_iters > 0:
                    replay_kwargs = dict(kwargs)
                    replay_kwargs.update(
                        {
                            "advance_iteration_count": False,
                            "foreground_saturated": False,
                            "replay_only": True,
                        }
                    )
                    replay_completed = original_state_map(
                        current_window,
                        replay_iters,
                        *positional,
                        **replay_kwargs,
                    ) or 0
                return int(frontier_completed) + int(replay_completed)

            mapper.map = MethodType(fixed_credit_state_map, mapper)
    if args.keyframe_replay_fraction >= 0.0:
        mapper._mapping_replay_queue = SourceQuotaReplayQueue(
            mapper._mapping_replay_queue,
            args.keyframe_replay_fraction,
        )
    if args.new_view_service_period:
        mapper._mapping_replay_queue = MinimumFirstServiceQueue(
            mapper._mapping_replay_queue,
            args.new_view_service_period,
        )
    mapper._exp78b_replay_gradient_scope = args.dense_replay_scope
    mapper._exp78b_replay_curvature_threshold_deg = (
        args.dense_replay_curvature_threshold_deg
    )
    mapper._exp78b_replay_endpoint_geometry_fraction = (
        args.dense_replay_endpoint_geometry_fraction
    )
    mapper._exp78b_keyframe_replay_full_geometry = bool(
        args.keyframe_replay_full_geometry
    )
    mapper._exp78b_replay_scope_active = False
    mapper._exp78b_current_replay_keys = ()
    mapper._exp78b_adaptive_scope_counts = {"full": 0, "appearance": 0}
    mapper._exp78b_effective_replay_scope_counts = collections.Counter()
    dense_pose_shaper = (
        CausalImuDensePoseShaper(archive)
        if args.profile in ("dense_rr_imu", "d1_fixed_state_rr_imu")
        else None
    )
    if dense_pose_shaper is not None:
        mapper._exp78b_dense_pose_shaper = dense_pose_shaper
        install_dense_imu_pose_refresh(mapper, dense_pose_shaper)
    compute_paced_admission = (
        AdaptiveViewsetController(required_opportunities=2)
        if args.compute_paced_dense_admission
        else None
    )
    compute_paced_records_by_uid: dict[int, tuple] = {}
    if args.dense_pose_confidence_weighting:
        install_dense_pose_confidence_weighting(mapper)
    if args.dense_replay_scope in (
        "adaptive_imu_curvature",
        "adaptive_endpoint_geometry",
    ):
        if dense_pose_shaper is None:
            raise ValueError(
                f"{args.dense_replay_scope} requires --profile dense_rr_imu"
            )
        if (
            args.dense_replay_scope == "adaptive_imu_curvature"
            and args.dense_replay_curvature_threshold_deg < 0.0
        ):
            raise ValueError("dense replay curvature threshold must be non-negative")
    if (
        fixed_event_dense_isolation
        or args.keyframe_replay_full_geometry
        or args.dense_replay_scope in (
        "adaptive_imu_curvature",
        "adaptive_endpoint_geometry",
        "adaptive_topology_maturation",
        )
    ):
        install_replay_selection_capture(mapper)
    if fixed_event_dense_isolation and not hasattr(
        mapper, "mapping_lifecycle_snapshot"
    ):
        raise RuntimeError(
            "fixed-event Stage 3/4 requires lifecycle parity telemetry"
        )

    newborn_consolidation = (
        ObservationConditionedNewbornConsolidation()
        if args.observation_conditioned_newborn_consolidation
        else None
    )
    if newborn_consolidation is not None:
        install_newborn_consolidation(mapper, newborn_consolidation)

    replay_start = time.monotonic()
    sensor_timestamp0 = float(archive.arrivals[0]["sensor_timestamp"])
    sensor_timestamp_last = float(archive.arrivals[-1]["sensor_timestamp"])
    time_scale = None if args.time_scale == "unbounded" else float(args.time_scale)
    deadline = (
        None
        if time_scale is None
        else replay_start + (sensor_timestamp_last - sensor_timestamp0) * time_scale
    )
    guard = BoundaryGuard(deadline, args.deadline_reserve_ms / 1000.0)
    original_adam_step = install_adam_guard(mapper, guard)
    install_topology_guard(mapper, guard)
    telemetry = install_render_telemetry(mapper)

    event_records: list[dict[str, object]] = []
    processed_event_ids: set[int] = set()
    pending_dense: list[tuple] = []
    seen_dense_uids: set[int] = set()
    registered_dense_uids: set[int] = set()
    dense_admission_ledger: list[dict[str, object]] = []
    fixed_event_dense_opportunity_ledger: list[dict[str, object]] = []
    map_generation = 0
    dense_records_available = 0
    dense_registration_calls = 0
    dense_registration_wall_seconds = 0.0
    dense_pose_packet_refresh_calls = 0
    dense_pose_packet_refresh_updates = 0
    dense_pose_packet_refresh_wall_seconds = 0.0
    dense_pose_packet_refresh_skipped_deadline = 0
    dense_pose_packet_refresh_candidate_packets = 0
    imu_metric_ready = False
    skipped_before_imu: list[int] = []
    replay_serviced_since_dispatch = True

    def register_pending_dense(boundary_source_id: str) -> int:
        nonlocal dense_registration_calls, dense_registration_wall_seconds
        selected_uids: list[int] = []
        if (
            compute_paced_admission is not None
            and hasattr(mapper, "projection_matrix")
        ):
            is_valid = lambda uid: (
                int(uid) in compute_paced_records_by_uid
                and int(uid) not in mapper.viewpoints
                and int(uid) not in mapper.polish_viewpoints
            )
            selected_uids = compute_paced_admission.bootstrap_token_service(
                is_valid=is_valid,
            )
            selected_uids.extend(
                compute_paced_admission.admit_token_service(
                    int(mapper.mapping_replay_dense_updates),
                    args.compute_paced_dense_token_cost,
                    is_valid=is_valid,
                )
            )
            pending_dense.extend(
                compute_paced_records_by_uid.pop(int(uid))
                for uid in selected_uids
            )
            dense_admission_ledger.extend(
                {
                    "uid": int(uid),
                    "map_generation": int(map_generation),
                    "completed_dense_service": int(
                        mapper.mapping_replay_dense_updates
                    ),
                    "boundary_source_id": str(boundary_source_id),
                }
                for uid in selected_uids
            )
        if not pending_dense or not hasattr(mapper, "projection_matrix"):
            return 0
        records = list(pending_dense)
        pending_dense.clear()
        registered_before = set(mapper.polish_viewpoints)
        torch.cuda.synchronize()
        started = time.monotonic()
        added = mapper.register_causal_dense_views(records)
        if dense_pose_shaper is not None:
            for record in records:
                uid = int(record[0])
                camera = mapper.polish_viewpoints.get(uid)
                if camera is None:
                    continue
                camera.causal_pose_left_residual = (
                    dense_pose_shaper.left_residual_by_uid[uid].clone()
                )
                camera.dense_pose_source = "causal_raw_imu_rotation_shape"
                camera.causal_gyro_curvature_degrees = float(
                    dense_pose_shaper.curvature_by_uid[uid]
                )
                camera.dense_geometry_trusted = False
        torch.cuda.synchronize()
        dense_registration_calls += 1
        dense_registration_wall_seconds += time.monotonic() - started
        registered_now = set(mapper.polish_viewpoints) - registered_before
        if int(added) != len(registered_now):
            raise RuntimeError(
                "dense registration count mismatch: "
                f"backend={added} observed={len(registered_now)}"
            )
        registered_dense_uids.update(int(uid) for uid in registered_now)
        return int(added)

    def process_control(item: TimelineItem, input_lag: float) -> None:
        nonlocal imu_metric_ready, map_generation
        metadata = item.metadata
        event_id = int(metadata["event_id"])
        payload = archive.load_event_payload(metadata)
        guard.next_control_due = None
        torch.cuda.synchronize()
        started = time.monotonic()
        with torch.no_grad():
            if item.kind == "metric_rescale":
                scale = float(payload["scale"])
                mapper.rescale(scale)
                scale_pending_dense(pending_dense, scale)
                if compute_paced_admission is not None:
                    scale_pending_dense(
                        list(compute_paced_records_by_uid.values()), scale
                    )
                imu_metric_ready = True
            else:
                mapper.remove_all_gaussians()
                map_generation += 1
                if compute_paced_admission is not None:
                    compute_paced_admission.reset_token_service_clock(
                        int(mapper.mapping_replay_dense_updates)
                    )
                if newborn_consolidation is not None:
                    newborn_consolidation.reset_active_map()
                    install_newborn_consolidation_gaussian(
                        mapper, newborn_consolidation
                    )
                install_topology_guard(mapper, guard)
        torch.cuda.synchronize()
        processed_event_ids.add(event_id)
        event_records.append(
            {
                "event_id": event_id,
                "kind": item.kind,
                "input_lag_seconds_at_start": input_lag,
                "filtered_frame_uids": [],
                "optimizer_steps_completed": 0,
                "rasterized_view_updates": 0,
                "wall_seconds": time.monotonic() - started,
                "completed": True,
            }
        )

    def process_dense(item: TimelineItem, input_lag: float) -> None:
        nonlocal dense_records_available
        records = archive.dense_records(item.metadata, seen_uids=seen_dense_uids)
        dense_records_available += len(records)
        if args.profile != "frontier_only":
            if dense_pose_shaper is not None:
                records = dense_pose_shaper.shape_records(item.metadata, records)
            if compute_paced_admission is None:
                pending_dense.extend(records)
            else:
                left = int(item.metadata["left_keyframe_uid"])
                right = int(item.metadata["right_keyframe_uid"])
                records_by_uid = {int(record[0]): record for record in records}
                ordered_uids = temporal_maximin_order(
                    records_by_uid,
                    left,
                    right,
                )
                compute_paced_records_by_uid.update(records_by_uid)
                compute_paced_admission.add_interval(
                    (left, right),
                    ordered_uids,
                    bootstrap=False,
                )
                # Spend service before the next interval can affect the
                # candidate set, then materialize the one global seed (or any
                # already-paid records) as soon as the mapper exists.
                register_pending_dense(item.source_id)

    scheduler: FrozenTimelineScheduler

    def process_packet(
        item: TimelineItem,
        input_lag: float,
        next_control_due: float | None,
        strict_deadline: float | None,
    ) -> None:
        nonlocal replay_serviced_since_dispatch
        nonlocal dense_pose_packet_refresh_calls
        nonlocal dense_pose_packet_refresh_updates
        nonlocal dense_pose_packet_refresh_wall_seconds
        nonlocal dense_pose_packet_refresh_skipped_deadline
        nonlocal dense_pose_packet_refresh_candidate_packets
        metadata = item.metadata
        event_id = int(metadata["event_id"])
        if (
            args.mapping_after_metric_init
            or bool(mapper_args.mapping_after_imu_init)
        ) and not imu_metric_ready:
            skipped_before_imu.append(event_id)
            processed_event_ids.add(event_id)
            event_records.append(
                {
                    "event_id": event_id,
                    "kind": item.kind,
                    "input_lag_seconds_at_start": input_lag,
                    "filtered_frame_uids": [],
                    "optimizer_steps_completed": 0,
                    "rasterized_view_updates": 0,
                    "wall_seconds": 0.0,
                    "completed": True,
                    "policy_skip": (
                        "mapping_before_metric_init"
                        if args.mapping_after_metric_init
                        else "mapping_after_imu_init"
                    ),
                }
            )
            return
        packet = archive.mapping_packet(metadata, filter_heldout=True)
        if packet is None:
            processed_event_ids.add(event_id)
            return
        packet["mapping_worker_saturated"] = bool(
            not replay_serviced_since_dispatch
            or scheduler.pending_mapping_packets
        )
        replay_serviced_since_dispatch = False
        telemetry["frontier_packet_calls"] += 1
        guard.next_control_due = next_control_due
        torch.cuda.synchronize()
        started = time.monotonic()
        before_steps = guard.optimizer_steps_completed
        before_views = telemetry["training_rasterized_view_updates"]
        after_frontier_steps = before_steps
        after_frontier_views = before_views
        fixed_dense_steps = 0
        fixed_dense_views = 0
        completed = False
        stop_reason = None
        try:
            mapper.process_track_data(packet)
            completed = True
            processed_event_ids.add(event_id)
            after_frontier_steps = guard.optimizer_steps_completed
            after_frontier_views = telemetry["training_rasterized_view_updates"]
            register_pending_dense(f"event:{event_id}:post_frontier")
            if (
                fixed_event_dense_isolation
                and mapper.initialized
                and mapper.current_window
                and mapper.polish_viewpoints
            ):
                fixed_before_steps = guard.optimizer_steps_completed
                fixed_before_views = telemetry[
                    "training_rasterized_view_updates"
                ]
                fixed_before_dense = int(mapper.mapping_replay_dense_updates)
                fixed_pool_uids = sorted(
                    int(uid) for uid in mapper.polish_viewpoints
                )
                fixed_interval_ids: set[tuple[int, int]] = set()
                for uid in fixed_pool_uids:
                    camera = mapper.polish_viewpoints[int(uid)]
                    left = getattr(
                        camera, "causal_admission_left_keyframe", None
                    )
                    right = getattr(
                        camera, "causal_admission_right_keyframe", None
                    )
                    if left is None or right is None:
                        raise RuntimeError(
                            "fixed-event dense candidate lacks immutable "
                            "causal interval endpoints: "
                            f"uid={uid} left={left!r} right={right!r}"
                        )
                    fixed_interval_ids.add((int(left), int(right)))
                lifecycle_before = mapper.mapping_lifecycle_snapshot()
                selector_before = lifecycle_before.get("selector_block")
                if selector_audit_required and selector_before is None:
                    raise RuntimeError(
                        "Stage-3c/3d/4 requires non-mutating selector-block "
                        "telemetry"
                    )
                mapper._exp78b_replay_scope_active = True
                try:
                    fixed_completed = bool(
                        mapper.idle_map_rr_step(iters=1, batch_size=1)
                    )
                    selected_keys = [
                        [str(key[0]), int(key[1])]
                        for key in mapper._exp78b_current_replay_keys
                    ]
                finally:
                    mapper._exp78b_replay_scope_active = False
                    mapper._exp78b_current_replay_keys = ()
                if not fixed_completed:
                    raise RuntimeError(
                        "fixed-event dense opportunity did not complete"
                    )
                fixed_dense_steps = (
                    guard.optimizer_steps_completed - fixed_before_steps
                )
                fixed_dense_views = (
                    telemetry["training_rasterized_view_updates"]
                    - fixed_before_views
                )
                dense_delta = (
                    int(mapper.mapping_replay_dense_updates)
                    - fixed_before_dense
                )
                if fixed_dense_steps != 1 or dense_delta != 1:
                    raise RuntimeError(
                        "fixed-event opportunity must complete exactly one "
                        f"Adam/dense service: adam={fixed_dense_steps} "
                        f"dense={dense_delta}"
                    )
                lifecycle_snapshot = mapper.mapping_lifecycle_snapshot()
                selector_after = lifecycle_snapshot.get("selector_block")
                selector_block_delta = None
                if selector_before is not None and selector_after is not None:
                    selector_block_delta = int(
                        selector_after["blocks_started"]
                    ) - int(selector_before["blocks_started"])
                    if selector_block_delta not in (0, 1):
                        raise RuntimeError(
                            "fixed-event selector may start at most one block: "
                            f"delta={selector_block_delta}"
                        )
                fixed_event_dense_opportunity_ledger.append(
                    {
                        "opportunity_index": len(
                            fixed_event_dense_opportunity_ledger
                        ),
                        "event_id": int(event_id),
                        "map_generation": int(map_generation),
                        "pool_uids_before": fixed_pool_uids,
                        "causal_interval_count_before": len(
                            fixed_interval_ids
                        ),
                        "selected_keys": selected_keys,
                        "completed_dense_service_before": fixed_before_dense,
                        "completed_dense_service_after": int(
                            mapper.mapping_replay_dense_updates
                        ),
                        "optimizer_steps_completed": fixed_dense_steps,
                        "rasterized_view_updates": fixed_dense_views,
                        "selector_block_before": selector_before,
                        "selector_block_started": selector_block_delta,
                        "lifecycle": lifecycle_snapshot,
                    }
                )
                replay_serviced_since_dispatch = True
                register_pending_dense(f"event:{event_id}:post_fixed_dense")
            dense_pose_packet_refresh_candidate_packets += 1
            refresh_due = (
                args.dense_pose_refresh_every_packet
                and dense_pose_packet_refresh_candidate_packets
                % args.dense_pose_refresh_period
                == 0
            )
            if refresh_due:
                now = time.monotonic()
                if (
                    strict_deadline is not None
                    and now >= strict_deadline - guard.reserve_seconds
                ):
                    dense_pose_packet_refresh_skipped_deadline += 1
                else:
                    torch.cuda.synchronize()
                    refresh_started = time.monotonic()
                    dense_pose_packet_refresh_updates += int(
                        mapper._refresh_causal_dense_poses()
                    )
                    torch.cuda.synchronize()
                    dense_pose_packet_refresh_wall_seconds += (
                        time.monotonic() - refresh_started
                    )
                    dense_pose_packet_refresh_calls += 1
        except ControlPreempted:
            stop_reason = "control_preempted"
            mapper.gaussians.optimizer.zero_grad(set_to_none=True)
            raise
        except DeadlineReached:
            stop_reason = "deadline"
            mapper.gaussians.optimizer.zero_grad(set_to_none=True)
            raise
        finally:
            guard.next_control_due = None
            torch.cuda.synchronize()
            event_records.append(
                {
                    "event_id": event_id,
                    "kind": item.kind,
                    "input_lag_seconds_at_start": input_lag,
                    "filtered_frame_uids": [
                        int(value) for value in packet["tstamp"].tolist()
                    ],
                    "wall_seconds": time.monotonic() - started,
                    "optimizer_steps_completed": (
                        guard.optimizer_steps_completed - before_steps
                    ),
                    "frontier_optimizer_steps_completed": (
                        after_frontier_steps - before_steps
                    ),
                    "fixed_dense_optimizer_steps_completed": fixed_dense_steps,
                    "rasterized_view_updates": (
                        telemetry["training_rasterized_view_updates"] - before_views
                    ),
                    "frontier_rasterized_view_updates": (
                        after_frontier_views - before_views
                    ),
                    "fixed_dense_rasterized_view_updates": fixed_dense_views,
                    "completed": completed,
                    "stop_reason": stop_reason,
                    "mapping_worker_saturated": bool(
                        packet["mapping_worker_saturated"]
                    ),
                }
            )

    def idle_step(next_arrival: float | None, strict_deadline: float | None) -> bool:
        nonlocal replay_serviced_since_dispatch
        if args.profile == "frontier_only" or args.time_scale == "unbounded":
            return False
        if not mapper.initialized or not mapper.current_window:
            return False
        guard.next_control_due = None
        telemetry["idle_replay_calls"] += 1
        mapper._exp78b_replay_scope_active = True
        try:
            completed = bool(mapper.idle_map_rr_step(iters=1, batch_size=1))
        finally:
            mapper._exp78b_replay_scope_active = False
            mapper._exp78b_current_replay_keys = ()
        if completed:
            telemetry["idle_replay_calls_completed"] += 1
            replay_serviced_since_dispatch = True
        return completed

    scheduler = FrozenTimelineScheduler(
        build_frozen_timeline(archive),
        replay_start=replay_start,
        sensor_timestamp0=sensor_timestamp0,
        time_scale=time_scale,
        deadline=deadline,
        queue_capacity=2,
    )
    try:
        scheduler_stats = scheduler.run(
            process_control=process_control,
            process_dense=process_dense,
            process_packet=process_packet,
            idle_step=idle_step,
        )
    finally:
        torch.optim.Adam.step = original_adam_step

    torch.cuda.synchronize()
    replay_seconds = time.monotonic() - replay_start
    tracking_mapped_uids = {
        int(value)
        for value, viewpoint in mapper.viewpoints.items()
        if not bool(getattr(viewpoint, "mapping_eval_excluded", False))
    }
    dense_selected_uids = {
        int(key[1])
        for key, count in mapper._mapping_replay_queue.selection_counts.items()
        if isinstance(key, tuple)
        and len(key) >= 2
        and key[0] == "dense"
        and int(count) > 0
    }
    mapped_uids = sorted(tracking_mapped_uids | dense_selected_uids)
    heldout_overlap = sorted(set(mapped_uids).intersection(archive.heldout_uids))
    origin_uids = sorted(
        {
            int(value)
            for value in mapper.gaussians.unique_kfIDs.detach().cpu().tolist()
            if int(value) >= 0
        }
    )
    origin_heldout_overlap = sorted(set(origin_uids).intersection(archive.heldout_uids))
    if heldout_overlap or origin_heldout_overlap:
        raise RuntimeError(
            "mapping-disjointness violated: "
            f"views={heldout_overlap} origins={origin_heldout_overlap}"
        )
    mapper.gaussians.save_ply(output / "3dgs_before_final.ply")
    save_shared_trajectories(archive, output)
    replay_summary = mapper.mapping_replay_summary()
    online_density_summary = (
        None if online_density is None else online_density.summary()
    )
    if online_density is not None and int(
        online_density_summary["unique_frames"]
    ) <= 0:
        raise RuntimeError(
            "online-rank density was requested but no Gaussian birth invoked "
            "the causal multiplier"
        )

    runtime = {
        "protocol": PROTOCOL,
        "method": f"gsslam_{args.profile}_quality_first_no_carve",
        "mapping_profile": args.profile,
        "fixed_work_dense_global_views": args.fixed_work_dense_global_views,
        "fixed_work_dense_selector": args.fixed_work_dense_selector,
        "fixed_work_ercb_beta": args.fixed_work_ercb_beta,
        "fixed_work_ercb_block_size": args.fixed_work_ercb_block_size,
        "fixed_iteration_projected_dense_selector": (
            args.fixed_iteration_projected_dense_selector
        ),
        "fixed_iteration_projected_dense_iters": (
            args.fixed_iteration_projected_dense_iters
        ),
        "fixed_iteration_projected_dense_batch_size": (
            args.fixed_iteration_projected_dense_batch_size
        ),
        "fixed_iteration_projected_dense_norm_ratio": (
            args.fixed_iteration_projected_dense_norm_ratio
        ),
        "fixed_iteration_projected_dense_geometry_norm_ratio": (
            args.fixed_iteration_projected_dense_geometry_norm_ratio
        ),
        "fixed_iteration_dedicated_dense_selector": (
            args.fixed_iteration_dedicated_dense_selector
        ),
        "fixed_iteration_dedicated_dense_iters": (
            args.fixed_iteration_dedicated_dense_iters
        ),
        "fixed_iteration_dedicated_dense_batch_size": (
            args.fixed_iteration_dedicated_dense_batch_size
        ),
        "fixed_iteration_dedicated_dense_scope": (
            args.fixed_iteration_dedicated_dense_scope
        ),
        "compute_paced_dense_admission": args.compute_paced_dense_admission,
        "compute_paced_dense_token_cost": args.compute_paced_dense_token_cost,
        "service_shortfall_ercb_requested": args.service_shortfall_ercb,
        "c2_orthogonal_isolation": stage3c_c2_orthogonal_isolation,
        "c2_global_residue_isolation": (
            stage3d_c2_global_residue_isolation
        ),
        "c1_c2_global_residue_integration": (
            stage4_c1_c2_global_residue_integration
        ),
        "fixed_event_dense_opportunities_per_packet": (
            args.fixed_event_dense_opportunities_per_packet
        ),
        "fixed_event_dense_opportunity_ledger": (
            fixed_event_dense_opportunity_ledger
        ),
        "dense_admission_ledger": dense_admission_ledger,
        "service_shortfall_ercb_parameters": (
            {
                "block_size": 8,
                "relative_floor_ratio": 0.75,
                "gamma": math.log(1.5),
                "maximum_bonus": 1.5,
                "global_epoch_no_repeat": bool(
                    c2_global_residue_semantics
                ),
            }
            if args.service_shortfall_ercb
            else None
        ),
        "compute_paced_dense_admission_summary": (
            None
            if compute_paced_admission is None
            else compute_paced_admission.summary()
        ),
        "new_view_service_period": args.new_view_service_period,
        "dense_pose_confidence_weighting": args.dense_pose_confidence_weighting,
        "dense_pose_refresh_every_packet": args.dense_pose_refresh_every_packet,
        "dense_pose_refresh_period": args.dense_pose_refresh_period,
        "dense_pose_packet_refresh_candidate_packets": (
            dense_pose_packet_refresh_candidate_packets
        ),
        "dense_pose_packet_refresh_calls": dense_pose_packet_refresh_calls,
        "dense_pose_packet_refresh_updates": dense_pose_packet_refresh_updates,
        "dense_pose_packet_refresh_wall_seconds": (
            dense_pose_packet_refresh_wall_seconds
        ),
        "dense_pose_packet_refresh_skipped_deadline": (
            dense_pose_packet_refresh_skipped_deadline
        ),
        "dense_max_endpoint_fraction": args.dense_max_endpoint_fraction,
        "include_keyframes_in_replay": args.include_keyframes_in_replay,
        "keyframe_replay_fraction": args.keyframe_replay_fraction,
        "keyframe_replay_full_geometry": args.keyframe_replay_full_geometry,
        "dense_pose_confidence_summary": (
            getattr(mapper, "_exp78b_pose_confidence_stats", None)
        ),
        "auto_topology_freeze_requested": args.auto_topology_freeze,
        "observation_topology_gate_requested": (
            args.observation_topology_gate
        ),
        "auto_topology_frozen_final": bool(
            getattr(mapper, "_mapping_auto_topology_frozen", False)
        ),
        "observation_conditioned_newborn_consolidation_requested": (
            args.observation_conditioned_newborn_consolidation
        ),
        "observation_conditioned_newborn_consolidation_summary": (
            None
            if newborn_consolidation is None
            else newborn_consolidation.summary()
        ),
        "relative_capacity_prune_closure_requested": (
            args.relative_capacity_prune_closure
        ),
        "d1_preserve_full_frontier": args.d1_preserve_full_frontier,
        "relative_capacity_prune_closure_summary": (
            None
            if relative_capacity_prune_state is None
            else {
                "target": int(relative_capacity_prune_state["target"]),
                "recovery_observations": int(
                    relative_capacity_prune_state["recovery_observations"]
                ),
                "closures": int(relative_capacity_prune_state["closures"]),
            }
        ),
        "dense_replay_gradient_scope": args.dense_replay_scope,
        "dense_replay_curvature_threshold_degrees": (
            args.dense_replay_curvature_threshold_deg
        ),
        "dense_replay_endpoint_geometry_fraction": (
            args.dense_replay_endpoint_geometry_fraction
        ),
        "dense_replay_adaptive_scope_optimizer_steps": dict(
            mapper._exp78b_adaptive_scope_counts
        ),
        "effective_replay_source_scope_optimizer_steps": dict(
            mapper._exp78b_effective_replay_scope_counts
        ),
        "custom_root": str(CUSTOM_ROOT),
        "custom_commit": __import__("subprocess").check_output(
            ["git", "-C", str(CUSTOM_ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "archive": str(archive.root),
        "archive_manifest_sha256": hashlib.sha256(
            (archive.root / "archive_manifest.json").read_bytes()
        ).hexdigest(),
        "config": str(config_path),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "effective_config_sha256": effective_config_sha256,
        "density_policy": density_policy,
        "online_density_summary": online_density_summary,
        "runtime_provenance": runtime_provenance(),
        "seed": args.seed,
        "time_scale": args.time_scale,
        "sensor_duration_seconds": sensor_timestamp_last - sensor_timestamp0,
        "budget_seconds": (
            None
            if time_scale is None
            else (sensor_timestamp_last - sensor_timestamp0) * time_scale
        ),
        "deadline_reserve_ms": args.deadline_reserve_ms,
        "work_contract": (
            (
                "d1_stage1_native_fixed_one_dense_opportunity_per_completed_packet_v1"
                if c2_full_pool_isolation
                else "d1_native_fixed_one_dense_opportunity_per_completed_packet_v1"
            )
            if fixed_event_dense_isolation
            else (
                "official_event_adam_v1"
                if args.time_scale == "unbounded"
                and args.mapping_after_metric_init
                else None
            )
        ),
        "comparison_contract": (
            (
                "stage4_c1_c2_global_residue_fixed_event_integration_v1"
                if stage4_c1_c2_global_residue_integration
                else (
                    "stage3d_c2_global_residue_fixed_event_ordering_only_v1"
                    if stage3d_c2_global_residue_isolation
                    else (
                        "stage3c_c2_orthogonal_fixed_event_ordering_only_v1"
                        if stage3c_c2_orthogonal_isolation
                        else "stage3_rr_vs_ercb_fixed_event_ordering_only_v2"
                    )
                )
            )
            if fixed_event_dense_isolation
            else (
                "official_event_adam_v1_with_accounted_auxiliary_dense_views"
                if fixed_iteration_projected_enabled
                else (
                "official_event_adam_v1_with_method_specific_view_allocation"
                if fixed_iteration_dedicated_enabled
                else (
                    "official_event_adam_v1_with_method_specific_view_allocation"
                    if args.profile == "d1_fixed_state_rr_imu"
                    else None
                )
                )
            )
        ),
        "mapping_after_metric_init": args.mapping_after_metric_init,
        "official_frontier_parity": args.official_frontier_parity,
        "deadline_hit": scheduler_stats["deadline_reached"],
        "deadline_source_id": scheduler_stats["deadline_source_id"],
        "mapping_wall_seconds": replay_seconds,
        "input_lag_seconds_max": scheduler_stats["arrival_lag_seconds_max"],
        "input_lag_seconds_mean": scheduler_stats["arrival_lag_seconds_mean"],
        "events_in_archive": len(archive.events),
        "event_ids_fully_processed": sorted(processed_event_ids),
        "events_skipped_before_imu_metric_init": skipped_before_imu,
        "optimizer_steps_completed": guard.optimizer_steps_completed,
        "main_gaussian_optimizer_steps_completed": guard.main_gaussian_steps_completed,
        "auxiliary_adam_steps_completed": guard.auxiliary_adam_steps_completed,
        "optimizer_steps_rejected_at_deadline": guard.optimizer_steps_rejected_at_deadline,
        "topology_actions_rejected_at_deadline": guard.topology_actions_rejected_at_deadline,
        "control_boundary_preemptions": guard.control_preemptions,
        "post_eos_optimizer_updates": (
            0
            if deadline is None
            else sum(value > deadline for value in guard.optimizer_completion_times)
        ),
        "map_calls": telemetry["map_calls"],
        "frontier_packet_calls": telemetry["frontier_packet_calls"],
        "idle_replay_calls": telemetry["idle_replay_calls"],
        "idle_replay_calls_completed": telemetry["idle_replay_calls_completed"],
        "rasterized_view_updates": telemetry["training_rasterized_view_updates"],
        "nontraining_rasterized_view_updates": telemetry[
            "nontraining_rasterized_view_updates"
        ],
        "dense_records_causally_available": dense_records_available,
        "dense_unique_uids_causally_available": len(seen_dense_uids),
        "dense_input_policy": (
            "observed_but_unsupported"
            if args.profile == "frontier_only"
            else (
                "causal_dense_projected_into_fixed_adam_iteration"
                if fixed_iteration_projected_enabled
                else (
                    "causal_dense_owns_fixed_adam_iteration_allocation"
                    if fixed_iteration_dedicated_enabled
                    else (
                        "causal_dense_replaces_budgeted_global_slot"
                        if args.fixed_work_dense_global_views > 0
                        else (
                            "causally_registered_raw_imu_rotation_shaped_for_idle_replay"
                            if dense_pose_shaper is not None
                            else "causally_registered_endpoint_interpolated_for_idle_replay"
                        )
                    )
                )
            )
        ),
        "dense_pose_shaper": (
            None if dense_pose_shaper is None else dense_pose_shaper.summary()
        ),
        "dense_registration_calls": dense_registration_calls,
        "dense_registration_wall_seconds": dense_registration_wall_seconds,
        "dense_arrived_unique_views": len(seen_dense_uids),
        "dense_arrived_frame_uids": sorted(seen_dense_uids),
        "dense_pending_unregistered_frame_uids": sorted(
            int(record[0]) for record in pending_dense
        ),
        "dense_registered_unique_views": len(registered_dense_uids),
        "dense_registered_frame_uids": sorted(registered_dense_uids),
        "dense_selected_unique_views": len(dense_selected_uids),
        "dense_selected_frame_uids": sorted(dense_selected_uids),
        "tracking_mapped_unique_views": len(tracking_mapped_uids),
        "unique_mapped_views": len(mapped_uids),
        "mapped_frame_uids": mapped_uids,
        "heldout_mapping_overlap_count": len(heldout_overlap),
        "gaussian_origin_uids": origin_uids,
        "heldout_gaussian_origin_overlap_count": len(origin_heldout_overlap),
        "gaussians": int(mapper.gaussians.get_xyz.shape[0]),
        "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "mapping_replay_summary": replay_summary,
        "common_scheduler": scheduler_stats,
        "tensor_rt_tracker_archive": True,
        "causal_carve_enabled": False,
        "terminal_pruning_performed": False,
        "final_ba_performed": False,
        "final_color_refinement_performed": False,
        "evaluation_trajectory_is_post_eos_but_mapping_supervision_allowed": False,
        "events": event_records,
    }
    write_json(output / "mapping_replay_runtime.json", runtime)
    write_json(output / "mapped_uids.json", mapped_uids)
    print("EXP78B_GSSLAM_REPLAY " + json.dumps(runtime, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
