#!/usr/bin/env python3
"""Replay an exp78b frozen tracker trace through vanilla VIGS mapping only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
from types import MethodType, SimpleNamespace
import time

from lietorch import SE3
import numpy as np
import torch
import yaml

import gs_backend as official_gs_backend_module
from gs_backend import GSBackEnd

from exp78b_frozen_archive import FrozenTrackerArchive
from exp78b_timeline_scheduler import (
    ControlPreempted,
    DeadlineReached,
    FrozenTimelineScheduler,
    TimelineItem,
    build_frozen_timeline,
)


PROTOCOL = "exp78b_frozen_mapping_replay_v3_d1_render_match"


class DeadlineGuard:
    def __init__(self, deadline: float | None, reserve_seconds: float) -> None:
        self.deadline = deadline
        self.reserve_seconds = reserve_seconds
        self.next_control_due: float | None = None
        self.optimizer_steps_rejected = 0
        self.topology_actions_rejected = 0
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
                self.optimizer_steps_rejected += 1
            else:
                self.topology_actions_rejected += 1
            raise DeadlineReached(kind)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def install_gaussian_hooks(
    mapper: GSBackEnd,
    telemetry: dict[str, int],
    guard: DeadlineGuard,
) -> None:
    original_step = mapper.gaussians.optimizer.step
    original_densify_and_prune = mapper.gaussians.densify_and_prune
    original_reset_nonvisible = mapper.gaussians.reset_opacity_nonvisible

    def counted_step(*args, **kwargs):
        guard.reject_if_unsafe("optimizer")
        result = original_step(*args, **kwargs)
        if guard.enabled:
            torch.cuda.synchronize()
            guard.optimizer_completion_times.append(time.monotonic())
        telemetry["optimizer_steps_completed"] += 1
        return result

    def guarded_densify_and_prune(*args, **kwargs):
        guard.reject_if_unsafe("topology")
        return original_densify_and_prune(*args, **kwargs)

    def guarded_reset_nonvisible(*args, **kwargs):
        guard.reject_if_unsafe("topology")
        return original_reset_nonvisible(*args, **kwargs)

    mapper.gaussians.optimizer.step = counted_step
    mapper.gaussians.densify_and_prune = guarded_densify_and_prune
    mapper.gaussians.reset_opacity_nonvisible = guarded_reset_nonvisible


def install_telemetry(
    mapper: GSBackEnd, guard: DeadlineGuard
) -> dict[str, int]:
    telemetry = {
        "training_rasterized_view_updates": 0,
        "nontraining_renders": 0,
        "optimizer_steps_completed": 0,
        "map_calls": 0,
    }
    original_render = official_gs_backend_module.render
    original_map = mapper.map
    map_depth = 0

    def counted_render(*args, **kwargs):
        result = original_render(*args, **kwargs)
        if map_depth:
            telemetry["training_rasterized_view_updates"] += 1
        else:
            telemetry["nontraining_renders"] += 1
        return result

    def counted_map(self, *args, **kwargs):
        nonlocal map_depth
        telemetry["map_calls"] += 1
        map_depth += 1
        try:
            return original_map(*args, **kwargs)
        finally:
            map_depth -= 1

    official_gs_backend_module.render = counted_render
    mapper.map = MethodType(counted_map, mapper)
    install_gaussian_hooks(mapper, telemetry, guard)
    return telemetry


class D1RenderBudgetAdapter:
    """Cap native vanilla mapping by the render work spent by native D1.

    D1 is not rewritten into a common Adam-step schedule.  Vanilla keeps its
    own window/global sampler, RGB-D/normal loss, optimizer, and topology
    cadence.  This adapter changes only how many *native vanilla* iterations a
    packet may execute so that its cumulative render count follows the D1
    render-credit envelope.  D1 dense renders become ordinary vanilla KF
    render credit; no synthetic ``KF then dense`` schedule is introduced into
    vanilla.
    """

    def __init__(self, mapper: GSBackEnd, telemetry: dict[str, int]) -> None:
        self.mapper = mapper
        self.telemetry = telemetry
        self._counted_native_map = mapper.map
        self._event_open = False
        self._available_render_credit = 0
        self.render_credit_received = 0
        self.render_credit_consumed = 0
        self.logical_event_map_calls = 0
        self.native_requested_iterations = 0
        self.native_executed_iterations = 0
        self.final_partial_view_update = 0

        def views_per_iteration(
            current_window, include_global, max_viewpoints
        ):
            current = [
                key for key in current_window if key in self.mapper.viewpoints
            ]
            count = len(current)
            if include_global:
                current_set = set(current)
                global_count = sum(
                    key not in current_set for key in self.mapper.viewpoints
                )
                count += min(2, global_count)
            return min(int(max_viewpoints), count)

        def budgeted_map(
            bound_mapper,
            current_window,
            iters,
            prune=False,
            include_global=True,
            max_viewpoints=20,
        ):
            if not self._event_open:
                return self._counted_native_map(
                    current_window,
                    iters=iters,
                    prune=prune,
                    include_global=include_global,
                    max_viewpoints=max_viewpoints,
                )
            self.logical_event_map_calls += 1
            requested = int(iters)
            self.native_requested_iterations += requested
            per_iteration = views_per_iteration(
                current_window, include_global, max_viewpoints
            )
            if per_iteration <= 0:
                return None
            executable = min(
                requested,
                self._available_render_credit // per_iteration,
            )
            if executable <= 0:
                return None
            before = int(self.telemetry["training_rasterized_view_updates"])
            result = self._counted_native_map(
                current_window,
                iters=executable,
                prune=prune,
                include_global=include_global,
                max_viewpoints=max_viewpoints,
            )
            consumed = int(
                self.telemetry["training_rasterized_view_updates"]
            ) - before
            expected = executable * per_iteration
            if consumed != expected:
                raise RuntimeError(
                    "native vanilla render count was not predictable: "
                    f"expected={expected} observed={consumed}"
                )
            self.native_executed_iterations += executable
            self._available_render_credit -= consumed
            self.render_credit_consumed += consumed
            return result

        mapper.map = MethodType(budgeted_map, mapper)

    def begin_event(self, render_credit: int) -> None:
        if self._event_open:
            raise RuntimeError("nested D1 render-match event")
        render_credit = int(render_credit)
        if render_credit < 0:
            raise ValueError("D1 render credit must be non-negative")
        self._event_open = True
        self._available_render_credit += render_credit
        self.render_credit_received += render_credit

    def end_event(self) -> None:
        if not self._event_open:
            raise RuntimeError("D1 render-match event is not open")
        self._event_open = False

    def finish_budget_inside_final_event(self) -> None:
        """Consume the exact residual credit before the final causal event ends."""
        if not self._event_open:
            raise RuntimeError("final D1 render-match event is not open")
        if self._available_render_credit <= 0:
            return
        if not self.mapper.initialized or not self.mapper.current_window:
            raise RuntimeError("cannot finish render budget before map init")

        current_window = self.mapper.current_window
        current_set = set(current_window)
        full_views = min(
            20,
            len(current_window)
            + min(
                2,
                sum(
                    key not in current_set for key in self.mapper.viewpoints
                ),
            ),
        )
        if full_views <= 0:
            raise RuntimeError("final vanilla mapping window is empty")

        full_iterations = self._available_render_credit // full_views
        if full_iterations:
            before = int(self.telemetry["training_rasterized_view_updates"])
            self._counted_native_map(
                current_window,
                iters=full_iterations,
                include_global=True,
                max_viewpoints=20,
            )
            consumed = int(
                self.telemetry["training_rasterized_view_updates"]
            ) - before
            expected = full_iterations * full_views
            if consumed != expected:
                raise RuntimeError(
                    "final native vanilla render count mismatch: "
                    f"expected={expected} observed={consumed}"
                )
            self.native_executed_iterations += full_iterations
            self._available_render_credit -= consumed
            self.render_credit_consumed += consumed

        if self._available_render_credit:
            partial_views = self._available_render_credit
            before = int(self.telemetry["training_rasterized_view_updates"])
            self._counted_native_map(
                current_window,
                iters=1,
                include_global=True,
                max_viewpoints=partial_views,
            )
            consumed = int(
                self.telemetry["training_rasterized_view_updates"]
            ) - before
            if consumed != partial_views:
                raise RuntimeError(
                    "final partial vanilla update did not consume exact "
                    f"credit: expected={partial_views} observed={consumed}"
                )
            self.native_executed_iterations += 1
            self.final_partial_view_update = partial_views
            self._available_render_credit -= consumed
            self.render_credit_consumed += consumed


def build_d1_render_ledger(
    reference_runtime: Path,
    archive: FrozenTrackerArchive,
) -> dict[str, object]:
    reference = json.loads(reference_runtime.read_text(encoding="utf-8"))
    archive_manifest_sha256 = hashlib.sha256(
        (archive.root / "archive_manifest.json").read_bytes()
    ).hexdigest()
    if reference.get("archive_manifest_sha256") != archive_manifest_sha256:
        raise ValueError("D1 reference and vanilla archive hashes differ")
    if int(reference.get("post_eos_optimizer_updates", -1)) != 0:
        raise ValueError("D1 reference is not zero-tail")
    if int(reference.get("heldout_mapping_overlap_count", -1)) != 0:
        raise ValueError("D1 reference used held-out mapping supervision")

    event_regular_budget: dict[int, int] = {}
    selected_packet_events: set[int] = set()
    uncommitted_regular_attempts = 0
    reference_event_steps = 0
    for record in reference.get("events", []):
        event_id = int(record["event_id"])
        kind = str(record["kind"])
        if kind not in {"keyframe_update", "pose_scale_correction"}:
            continue
        selected_packet_events.add(event_id)
        attempted = int(record.get("rasterized_view_updates", 0) or 0)
        completed_steps = int(record.get("optimizer_steps_completed", 0) or 0)
        if bool(record.get("completed")):
            event_regular_budget[event_id] = attempted
            reference_event_steps += completed_steps
        else:
            event_regular_budget[event_id] = 0
            uncommitted_regular_attempts += attempted

    replay = reference.get("mapping_replay_summary") or {}
    dense_committed = int(replay.get("steps", 0) or 0)
    if bool(replay.get("service_shortfall_ercb", 0)):
        # Stage-3 selection counts intentionally advance only after Adam
        # succeeds.  A final deadline rejection can still have consumed a
        # physical rasterization, exposed separately from completed service.
        dense_attempted = dense_committed + int(
            replay.get("service_shortfall_pending_draw_attempts", 0) or 0
        )
    else:
        dense_attempted = int(
            replay.get("draw_count", dense_committed) or 0
        )
    uncommitted_dense_attempts = max(0, dense_attempted - dense_committed)

    positive_events = [
        event_id
        for event_id in sorted(event_regular_budget)
        if event_regular_budget[event_id] > 0
    ]
    regular_committed = sum(event_regular_budget.values())
    if not positive_events or regular_committed <= 0:
        raise ValueError("D1 reference has no committed regular render work")

    reference_attempted = int(reference.get("rasterized_view_updates", -1))
    reference_total_steps = int(
        reference.get("optimizer_steps_completed", -1)
    )
    event_attempted = regular_committed + uncommitted_regular_attempts
    event_ledger_includes_dense = (
        event_attempted == reference_attempted
        and reference_event_steps == reference_total_steps
    )
    if event_ledger_includes_dense:
        # Fixed-event Stage-3/4 records include the independent dense render
        # and Adam commit in each parent event.  Adding mapping_replay_summary
        # again would double-count one render per completed dense service.
        computed_attempted = event_attempted
        computed_steps = reference_event_steps
        additional_total = uncommitted_regular_attempts
    else:
        # The original wall-paced D1 ledger records regular frontier work in
        # events and independent dense work only in mapping_replay_summary.
        computed_attempted = event_attempted + dense_attempted
        computed_steps = reference_event_steps + dense_committed
        additional_total = dense_attempted + uncommitted_regular_attempts
    if reference_attempted != computed_attempted:
        raise ValueError(
            "D1 reference render telemetry is internally inconsistent: "
            f"runtime={reference_attempted} computed={computed_attempted}"
        )
    if computed_steps != reference_total_steps:
        raise ValueError("D1 reference optimizer telemetry is inconsistent")

    # Vanilla gets the entire physical D1 render count as useful native KF
    # work.  This includes the few D1 renders whose Adam step was preempted, so
    # the baseline is slightly advantaged rather than the candidate.  Prefix
    # allocation is only the causal compute envelope; it does not create a
    # dense-update path in vanilla.
    additional_by_event: dict[int, int] = {}
    cumulative_regular = 0
    allocated_additional = 0
    for event_id in positive_events:
        cumulative_regular += event_regular_budget[event_id]
        target_cumulative = (
            cumulative_regular * additional_total // regular_committed
        )
        additional_by_event[event_id] = (
            target_cumulative - allocated_additional
        )
        allocated_additional = target_cumulative
    if allocated_additional != additional_total:
        raise RuntimeError("failed to allocate the exact D1 render budget")

    return {
        "protocol": "exp78b_d1_native_render_budget_v2",
        "reference_runtime": str(reference_runtime.resolve()),
        "reference_runtime_sha256": hashlib.sha256(
            reference_runtime.read_bytes()
        ).hexdigest(),
        "reference_archive_manifest_sha256": archive_manifest_sha256,
        "selected_packet_event_ids": sorted(selected_packet_events),
        "event_regular_committed_render_credit": {
            str(key): value
            for key, value in sorted(event_regular_budget.items())
        },
        "event_additional_native_render_credit": {
            str(key): value
            for key, value in sorted(additional_by_event.items())
        },
        "regular_committed_renders": regular_committed,
        "dense_committed_renders": dense_committed,
        "uncommitted_regular_render_attempts": (
            uncommitted_regular_attempts
        ),
        "uncommitted_dense_render_attempts": uncommitted_dense_attempts,
        "event_ledger_includes_dense_replay": event_ledger_includes_dense,
        "d1_total_committed_renders": (
            reference_attempted
            - uncommitted_regular_attempts
            - uncommitted_dense_attempts
        ),
        "d1_total_attempted_renders": reference_attempted,
        "vanilla_native_render_target": reference_attempted,
        "vanilla_extra_useful_render_advantage": (
            uncommitted_regular_attempts + uncommitted_dense_attempts
        ),
        "reference_event_optimizer_steps": reference_event_steps,
        "reference_dense_optimizer_steps": dense_committed,
        "reference_total_optimizer_steps": reference_total_steps,
        "final_selected_packet_event_id": max(selected_packet_events),
    }


def install_mapping_disjoint_first_birth_fix(mapper: GSBackEnd) -> dict[str, int]:
    """Correct official add_next_kf(0, ...) when UID 0 is held out.

    The official backend hardcodes Gaussian origin ID 0 for its first accepted
    camera.  That is harmless in paper-native runs where frame 0 is mapped, but
    wrong after the strict adapter removes frame 0.  This narrowly scoped
    adapter substitutes the actual first camera UID and records every use.
    """
    telemetry = {"first_birth_uid_adapter_uses": 0}
    original = mapper.add_next_kf

    def corrected(self, frame_idx, viewpoint, *args, **kwargs):
        if bool(kwargs.get("init", False)) and int(frame_idx) == 0:
            actual_uid = int(viewpoint.uid)
            if actual_uid != 0:
                frame_idx = actual_uid
                telemetry["first_birth_uid_adapter_uses"] += 1
        return original(frame_idx, viewpoint, *args, **kwargs)

    mapper.add_next_kf = MethodType(corrected, mapper)
    return telemetry


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
    full_c2w = evaluation["poses_c2w_vector"].numpy()
    np.savetxt(
        output / "traj_full_beforeBA.txt",
        np.concatenate((timestamps[:, None], full_c2w), axis=1),
    )
    keyframe_c2w = SE3(final_state["keyframe_poses_w2c"]).inv().data.numpy()
    np.savetxt(
        output / "traj_kf_beforeBA.txt",
        np.concatenate(
            (
                final_state["keyframe_sensor_timestamps"].numpy()[:, None],
                keyframe_c2w,
            ),
            axis=1,
        ),
    )
    np.save(
        output / "intrinsics.npy",
        final_state["keyframe_intrinsics_full_resolution"][0].numpy(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--time-scale",
        choices=("unbounded", "1.0", "1.5"),
        default="unbounded",
        help="sensor timestamp replay scale; 1.0 and 1.5 enforce zero-tail",
    )
    parser.add_argument(
        "--deadline-reserve-ms",
        type=float,
        default=50.0,
        help="do not start an optimizer/topology action this close to EOS",
    )
    parser.add_argument(
        "--mapping-after-metric-init",
        action="store_true",
        help=(
            "apply the common B fixed-work gate: packets before the causal "
            "metric-rescale event consume no mapping credit"
        ),
    )
    parser.add_argument(
        "--reference-service-runtime",
        type=Path,
        help=(
            "replay only the native D1 packet trace and make vanilla consume "
            "the same total physical render budget using only vanilla's "
            "native KF mapping path"
        ),
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = FrozenTrackerArchive(args.archive)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.cuda.reset_peak_memory_stats()
    with args.config.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    mapper_args = SimpleNamespace(
        output=str(output),
        gsvis=False,
        image_size=archive.manifest["preprocessing"]["output_image_size_hw"],
        length=len(archive.arrivals),
        start=0,
        stride=1,
        seed=args.seed,
    )
    mapper = GSBackEnd(config, str(output), mapper_args, use_gui=False)
    replay_start = time.monotonic()
    sensor_timestamp0 = float(archive.arrivals[0]["sensor_timestamp"])
    sensor_timestamp_last = float(archive.arrivals[-1]["sensor_timestamp"])
    time_scale = None if args.time_scale == "unbounded" else float(args.time_scale)
    deadline = (
        None
        if time_scale is None
        else replay_start
        + (sensor_timestamp_last - sensor_timestamp0) * time_scale
    )
    guard = DeadlineGuard(deadline, args.deadline_reserve_ms / 1000.0)
    telemetry = install_telemetry(mapper, guard)
    adapter = install_mapping_disjoint_first_birth_fix(mapper)
    d1_render_ledger = (
        None
        if args.reference_service_runtime is None
        else build_d1_render_ledger(
            args.reference_service_runtime.resolve(), archive
        )
    )
    render_match_adapter = (
        None
        if d1_render_ledger is None
        else D1RenderBudgetAdapter(mapper, telemetry)
    )
    d1_selected_packet_events = (
        set()
        if d1_render_ledger is None
        else set(d1_render_ledger["selected_packet_event_ids"])
    )
    if d1_render_ledger is not None:
        if args.time_scale != "unbounded":
            raise ValueError(
                "D1 render-matched vanilla is an unbounded B isolation replay"
            )
        if not args.mapping_after_metric_init:
            raise ValueError(
                "D1 render-matched vanilla requires mapping-after-metric-init"
            )
        write_json(output / "d1_render_service_ledger.json", d1_render_ledger)

    event_records = []
    skipped_empty_events = 0
    processed_event_ids: set[int] = set()
    dense_intervals_observed = 0
    dense_unique_uids_observed: set[int] = set()
    metric_ready = False

    def process_control(item: TimelineItem, input_lag: float) -> None:
        nonlocal metric_ready
        metadata = item.metadata
        event_id = int(metadata["event_id"])
        control = archive.load_event_payload(metadata)
        torch.cuda.synchronize()
        control_start = time.monotonic()
        guard.next_control_due = None
        with torch.no_grad():
            if item.kind == "metric_rescale":
                mapper.rescale(float(control["scale"]))
                metric_ready = True
            else:
                mapper.remove_all_gaussians()
                install_gaussian_hooks(mapper, telemetry, guard)
        torch.cuda.synchronize()
        processed_event_ids.add(event_id)
        event_records.append(
            {
                "event_id": event_id,
                "kind": item.kind,
                "emitted_at_frame_uid": int(metadata["emitted_at_frame_uid"]),
                "input_lag_seconds_at_start": input_lag,
                "scale": (
                    float(control["scale"])
                    if item.kind == "metric_rescale"
                    else None
                ),
                "filtered_frame_uids": [],
                "wall_seconds": time.monotonic() - control_start,
                "optimizer_steps_completed": 0,
                "rasterized_view_updates": 0,
                "completed": True,
            }
        )

    def process_dense(item: TimelineItem, input_lag: float) -> None:
        # The common causal stream exposes these RGB views to both arms.  The
        # unmodified official mapper has no dense-view replay interface, so
        # explicitly record them as observed-but-unused.
        nonlocal dense_intervals_observed
        dense_intervals_observed += 1
        interval = archive.load_dense_interval(item.metadata)
        dense_unique_uids_observed.update(
            int(value)
            for value in interval["candidate_uids"].tolist()
            if int(value) not in archive.heldout_uids
        )

    def process_packet(
        item: TimelineItem,
        input_lag: float,
        next_control_due: float | None,
        strict_deadline: float | None,
    ) -> None:
        nonlocal skipped_empty_events
        metadata = item.metadata
        event_id = int(metadata["event_id"])
        if args.mapping_after_metric_init and not metric_ready:
            processed_event_ids.add(event_id)
            event_records.append(
                {
                    "event_id": event_id,
                    "kind": item.kind,
                    "emitted_at_frame_uid": int(
                        metadata["emitted_at_frame_uid"]
                    ),
                    "input_lag_seconds_at_start": input_lag,
                    "filtered_frame_uids": [],
                    "wall_seconds": 0.0,
                    "optimizer_steps_completed": 0,
                    "rasterized_view_updates": 0,
                    "completed": True,
                    "policy_skip": "mapping_before_metric_init",
                }
            )
            return
        if d1_render_ledger is not None and (
            event_id not in d1_selected_packet_events
        ):
            processed_event_ids.add(event_id)
            event_records.append(
                {
                    "event_id": event_id,
                    "kind": item.kind,
                    "emitted_at_frame_uid": int(
                        metadata["emitted_at_frame_uid"]
                    ),
                    "input_lag_seconds_at_start": input_lag,
                    "filtered_frame_uids": [],
                    "wall_seconds": 0.0,
                    "optimizer_steps_completed": 0,
                    "rasterized_view_updates": 0,
                    "reference_regular_render_credit": 0,
                    "reference_additional_native_render_credit": 0,
                    "completed": True,
                    "policy_skip": "not_selected_by_d1_native_service_trace",
                }
            )
            return
        packet = archive.mapping_packet(metadata, filter_heldout=True)
        if packet is None:
            skipped_empty_events += 1
            processed_event_ids.add(event_id)
            return
        torch.cuda.synchronize()
        event_start = time.monotonic()
        before_steps = telemetry["optimizer_steps_completed"]
        before_views = telemetry["training_rasterized_view_updates"]
        regular_render_credit = 0
        additional_render_credit = 0
        credit_balance_before = 0
        if d1_render_ledger is not None:
            regular_render_credit = int(
                d1_render_ledger[
                    "event_regular_committed_render_credit"
                ].get(
                    str(event_id), 0
                )
            )
            additional_render_credit = int(
                d1_render_ledger[
                    "event_additional_native_render_credit"
                ].get(str(event_id), 0)
            )
            credit_balance_before = int(
                render_match_adapter._available_render_credit
            )
            render_match_adapter.begin_event(
                regular_render_credit + additional_render_credit
            )
        guard.next_control_due = next_control_due
        completed = False
        stop_reason = None
        try:
            mapper.process_track_data(packet)
            if render_match_adapter is not None:
                if event_id == int(
                    d1_render_ledger["final_selected_packet_event_id"]
                ):
                    render_match_adapter.finish_budget_inside_final_event()
                render_match_adapter.end_event()
            completed = True
            processed_event_ids.add(event_id)
        except ControlPreempted:
            stop_reason = "control_preempted"
            mapper.gaussians.optimizer.zero_grad(set_to_none=True)
            raise
        except DeadlineReached:
            stop_reason = "deadline"
            mapper.gaussians.optimizer.zero_grad(set_to_none=True)
            raise
        finally:
            if (
                render_match_adapter is not None
                and render_match_adapter._event_open
            ):
                render_match_adapter._event_open = False
            guard.next_control_due = None
            torch.cuda.synchronize()
            event_records.append(
                {
                    "event_id": event_id,
                    "kind": item.kind,
                    "emitted_at_frame_uid": int(
                        metadata["emitted_at_frame_uid"]
                    ),
                    "input_lag_seconds_at_start": input_lag,
                    "filtered_frame_uids": [
                        int(value) for value in packet["tstamp"].tolist()
                    ],
                    "wall_seconds": time.monotonic() - event_start,
                    "optimizer_steps_completed": (
                        telemetry["optimizer_steps_completed"] - before_steps
                    ),
                    "rasterized_view_updates": (
                        telemetry["training_rasterized_view_updates"] - before_views
                    ),
                    "reference_regular_render_credit": (
                        regular_render_credit
                    ),
                    "reference_additional_native_render_credit": (
                        additional_render_credit
                    ),
                    "render_credit_balance_before": credit_balance_before,
                    "render_credit_balance_after": (
                        None
                        if render_match_adapter is None
                        else int(
                            render_match_adapter._available_render_credit
                        )
                    ),
                    "completed": completed,
                    "stop_reason": stop_reason,
                }
            )

    scheduler = FrozenTimelineScheduler(
        build_frozen_timeline(archive),
        replay_start=replay_start,
        sensor_timestamp0=sensor_timestamp0,
        time_scale=time_scale,
        deadline=deadline,
        queue_capacity=2,
    )
    scheduler_stats = scheduler.run(
        process_control=process_control,
        process_dense=process_dense,
        process_packet=process_packet,
    )
    torch.cuda.synchronize()
    replay_seconds = time.monotonic() - replay_start
    if render_match_adapter is not None:
        expected_renders = int(
            d1_render_ledger["vanilla_native_render_target"]
        )
        observed_renders = int(
            telemetry["training_rasterized_view_updates"]
        )
        if render_match_adapter._event_open:
            raise RuntimeError("D1 render-match event remained open")
        if render_match_adapter._available_render_credit != 0:
            raise RuntimeError(
                "D1 render credit remained after final causal event: "
                f"{render_match_adapter._available_render_credit}"
            )
        if render_match_adapter.render_credit_received != expected_renders:
            raise RuntimeError(
                "D1 render credit ledger total mismatch: "
                f"received={render_match_adapter.render_credit_received} "
                f"expected={expected_renders}"
            )
        if observed_renders != expected_renders:
            raise RuntimeError(
                "vanilla did not match D1 physical render count: "
                f"observed={observed_renders} expected={expected_renders}"
            )
    mapped_uids = sorted(int(value) for value in mapper.viewpoints)
    heldout_overlap = sorted(set(mapped_uids).intersection(archive.heldout_uids))
    origin_uids = sorted(
        {
            int(value)
            for value in mapper.gaussians.unique_kfIDs.detach().cpu().tolist()
            if int(value) >= 0
        }
    )
    origin_heldout_overlap = sorted(
        set(origin_uids).intersection(archive.heldout_uids)
    )
    if heldout_overlap or origin_heldout_overlap:
        raise RuntimeError(
            "mapping-disjointness violated: "
            f"viewpoints={heldout_overlap} origins={origin_heldout_overlap}"
        )
    mapper.gaussians.save_ply(output / "3dgs_before_final.ply")
    save_shared_trajectories(archive, output)
    runtime = {
        "protocol": PROTOCOL,
        "method": "vanilla_vigs_official_gs_backend",
        "archive": str(archive.root),
        "archive_manifest_sha256": __import__("hashlib").sha256(
            (archive.root / "archive_manifest.json").read_bytes()
        ).hexdigest(),
        "config": str(args.config.resolve()),
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
            "d1_native_total_render_budget_v2"
            if d1_render_ledger is not None
            else (
                "official_event_credit_v1"
                if args.time_scale == "unbounded"
                and args.mapping_after_metric_init
                else None
            )
        ),
        "comparison_contract": (
            "native_d1_vs_native_vanilla_render_matched_v2"
            if d1_render_ledger is not None
            else None
        ),
        "d1_render_service_ledger": d1_render_ledger,
        "d1_render_match_summary": (
            None
            if render_match_adapter is None
            else {
                "render_credit_received": (
                    render_match_adapter.render_credit_received
                ),
                "render_credit_consumed": (
                    render_match_adapter.render_credit_consumed
                ),
                "render_credit_remaining": (
                    render_match_adapter._available_render_credit
                ),
                "logical_event_map_calls": (
                    render_match_adapter.logical_event_map_calls
                ),
                "native_requested_iterations": (
                    render_match_adapter.native_requested_iterations
                ),
                "native_executed_iterations": (
                    render_match_adapter.native_executed_iterations
                ),
                "final_partial_view_update": (
                    render_match_adapter.final_partial_view_update
                ),
                "vanilla_dense_update_path_added": False,
            }
        ),
        "mapping_after_metric_init": args.mapping_after_metric_init,
        "deadline_hit": scheduler_stats["deadline_reached"],
        "deadline_source_id": scheduler_stats["deadline_source_id"],
        "events_in_archive": len(archive.events),
        "events_processed": len(event_records),
        "event_ids_fully_processed": sorted(processed_event_ids),
        "events_not_processed": len(archive.events) - len(processed_event_ids),
        "events_skipped_after_heldout_filter": skipped_empty_events,
        "pose_scale_correction_events_processed": sum(
            record["kind"] == "pose_scale_correction" for record in event_records
        ),
        "metric_rescale_events_processed": sum(
            record["kind"] == "metric_rescale" for record in event_records
        ),
        "mapper_reset_events_processed": sum(
            record["kind"] == "mapper_reset" for record in event_records
        ),
        "mapping_wall_seconds": replay_seconds,
        "input_lag_seconds_max": scheduler_stats["arrival_lag_seconds_max"],
        "input_lag_seconds_mean": scheduler_stats["arrival_lag_seconds_mean"],
        "optimizer_steps_completed": telemetry["optimizer_steps_completed"],
        "optimizer_steps_rejected_at_deadline": guard.optimizer_steps_rejected,
        "topology_actions_rejected_at_deadline": guard.topology_actions_rejected,
        "control_boundary_preemptions": guard.control_preemptions,
        "iteration_count": int(mapper.iteration_count),
        "map_calls": telemetry["map_calls"],
        "rasterized_view_updates": telemetry[
            "training_rasterized_view_updates"
        ],
        "nontraining_renders": telemetry["nontraining_renders"],
        "dense_intervals_observed_but_unsupported": dense_intervals_observed,
        "dense_unique_views_observed_but_unsupported": len(
            dense_unique_uids_observed
        ),
        "dense_unique_frame_uids_observed_but_unsupported": sorted(
            dense_unique_uids_observed
        ),
        "unique_mapped_views": len(mapped_uids),
        "mapped_frame_uids": mapped_uids,
        "heldout_mapping_overlap_count": len(heldout_overlap),
        "gaussian_origin_uids": origin_uids,
        "heldout_gaussian_origin_overlap_count": len(origin_heldout_overlap),
        "gaussians": int(mapper.gaussians.get_xyz.shape[0]),
        "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "first_birth_uid_adapter": adapter,
        "final_ba_performed": False,
        "final_color_refinement_performed": False,
        "post_eos_optimizer_updates": (
            0
            if deadline is None
            else sum(value > deadline for value in guard.optimizer_completion_times)
        ),
        "evaluation_trajectory_is_post_eos_but_mapping_supervision_allowed": False,
        "common_scheduler": scheduler_stats,
        "events": event_records,
    }
    write_json(output / "mapping_replay_runtime.json", runtime)
    write_json(output / "mapped_uids.json", mapped_uids)
    print("EXP78B_VANILLA_REPLAY " + json.dumps(runtime, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
