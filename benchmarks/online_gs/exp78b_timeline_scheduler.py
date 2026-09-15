#!/usr/bin/env python3
"""Method-independent wall-clock scheduler for exp78b frozen mapper replay.

The frozen tracker emits packets independently of either Gaussian mapper.  This
module gives both mapper arms the same single-worker contract:

* source timestamps define arrival time;
* at most two ordinary mapping packets wait in FIFO order;
* a full queue drops its oldest waiting packet;
* mapper reset controls flush waiting packets and run before packets with the
  same timestamp;
* a running frontier map may yield at an optimizer/topology boundary when a
  control is due; and
* no work may complete after the strict sensor deadline.

The scheduler deliberately knows nothing about VIGS or Gaussian internals.
Mapper-specific hooks are supplied by the replay drivers.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time
from typing import Any, Callable, Iterable


PROTOCOL = "exp78b_common_timeline_scheduler_v1"
CONTROL_KINDS = frozenset(("metric_rescale", "mapper_reset"))


class ControlPreempted(RuntimeError):
    """Raised by a mapper hook at a safe boundary after a control became due."""


class DeadlineReached(RuntimeError):
    """Raised by a mapper hook before work that cannot safely meet the deadline."""


@dataclass(frozen=True)
class TimelineItem:
    source_id: str
    category: str
    kind: str
    sensor_timestamp: float
    stable_order: tuple[int, int]
    metadata: dict[str, Any]


def _category_priority(item: TimelineItem) -> int:
    # Controls must precede ordinary packets sharing the timestamp.  Dense RGB
    # becomes available only after its right pose bracket, so register it last.
    return {"control": 0, "mapping_packet": 1, "dense_interval": 2}[
        item.category
    ]


def build_frozen_timeline(archive: Any) -> list[TimelineItem]:
    output: list[TimelineItem] = []
    for metadata in archive.events:
        event_id = int(metadata["event_id"])
        kind = str(metadata["kind"])
        output.append(
            TimelineItem(
                source_id=f"event:{event_id}",
                category=("control" if kind in CONTROL_KINDS else "mapping_packet"),
                kind=kind,
                sensor_timestamp=float(metadata["emitted_at_sensor_timestamp"]),
                stable_order=(0, event_id),
                metadata=metadata,
            )
        )
    for interval_id, metadata in enumerate(archive.dense_intervals):
        output.append(
            TimelineItem(
                source_id=f"dense:{interval_id}",
                category="dense_interval",
                kind="dense_interval",
                sensor_timestamp=float(metadata["available_at_sensor_timestamp"]),
                stable_order=(1, interval_id),
                metadata=metadata,
            )
        )
    output.sort(
        key=lambda item: (
            item.sensor_timestamp,
            _category_priority(item),
            item.stable_order,
        )
    )
    return output


class FrozenTimelineScheduler:
    """Run a frozen timeline using mapper-specific callbacks.

    ``process_packet`` and ``idle_step`` may raise :class:`ControlPreempted` or
    :class:`DeadlineReached`.  They receive absolute monotonic boundaries so
    their optimizer hooks can yield safely.
    """

    def __init__(
        self,
        timeline: Iterable[TimelineItem],
        *,
        replay_start: float,
        sensor_timestamp0: float,
        time_scale: float | None,
        deadline: float | None,
        queue_capacity: int = 2,
    ) -> None:
        if queue_capacity < 1:
            raise ValueError("queue_capacity must be positive")
        self.timeline = list(timeline)
        self.replay_start = float(replay_start)
        self.sensor_timestamp0 = float(sensor_timestamp0)
        self.time_scale = time_scale
        self.deadline = deadline
        self.queue_capacity = int(queue_capacity)
        self._cursor = 0
        self._pending: deque[TimelineItem] = deque()
        self._stats: dict[str, Any] = {
            "protocol": PROTOCOL,
            "queue_capacity": self.queue_capacity,
            "timeline_items": len(self.timeline),
            "mapping_packets_enqueued": 0,
            "mapping_packets_started": 0,
            "mapping_packets_completed": 0,
            "mapping_packets_preempted_by_control": 0,
            "mapping_packets_dropped_oldest": 0,
            "mapping_packets_flushed_by_reset": 0,
            "dropped_source_ids": [],
            "flushed_source_ids": [],
            "control_source_ids_processed": [],
            "dense_source_ids_processed": [],
            "deadline_reached": False,
            "deadline_source_id": None,
            "arrival_lag_seconds": [],
        }

    def absolute_due(self, item: TimelineItem) -> float:
        if self.time_scale is None:
            return self.replay_start
        return self.replay_start + (
            item.sensor_timestamp - self.sensor_timestamp0
        ) * self.time_scale

    def _next_control_due(self) -> float | None:
        # In deterministic sequential/fixed-work replay, only one timeline
        # item is made available at a time.  A later control therefore cannot
        # arrive in the middle of the current packet and must not preempt it.
        if self.time_scale is None:
            return None
        for item in self.timeline[self._cursor :]:
            if item.category == "control":
                return self.absolute_due(item)
        return None

    def _next_arrival_due(self) -> float | None:
        if self._cursor >= len(self.timeline):
            return None
        return self.absolute_due(self.timeline[self._cursor])

    @property
    def pending_mapping_packets(self) -> int:
        return len(self._pending)

    def _enqueue_packet(self, item: TimelineItem) -> None:
        while len(self._pending) >= self.queue_capacity:
            dropped = self._pending.popleft()
            self._stats["mapping_packets_dropped_oldest"] += 1
            self._stats["dropped_source_ids"].append(dropped.source_id)
        self._pending.append(item)
        self._stats["mapping_packets_enqueued"] += 1

    def _flush_pending(self) -> None:
        while self._pending:
            flushed = self._pending.popleft()
            self._stats["mapping_packets_flushed_by_reset"] += 1
            self._stats["flushed_source_ids"].append(flushed.source_id)

    def _ingest_due(
        self,
        now: float,
        *,
        process_control: Callable[[TimelineItem, float], None],
        process_dense: Callable[[TimelineItem, float], None],
    ) -> None:
        ingested = 0
        while self._cursor < len(self.timeline):
            if self.time_scale is None and ingested:
                # Unbounded is a deterministic sequential diagnostic, not an
                # infinitely fast producer that drops the whole trace at t=0.
                break
            item = self.timeline[self._cursor]
            due = self.absolute_due(item)
            if due > now:
                break
            self._cursor += 1
            ingested += 1
            lag = max(0.0, time.monotonic() - due)
            self._stats["arrival_lag_seconds"].append(lag)
            if item.category == "control":
                if item.kind == "mapper_reset":
                    self._flush_pending()
                process_control(item, lag)
                self._stats["control_source_ids_processed"].append(item.source_id)
            elif item.category == "mapping_packet":
                self._enqueue_packet(item)
            else:
                process_dense(item, lag)
                self._stats["dense_source_ids_processed"].append(item.source_id)

    def run(
        self,
        *,
        process_control: Callable[[TimelineItem, float], None],
        process_dense: Callable[[TimelineItem, float], None],
        process_packet: Callable[
            [TimelineItem, float, float | None, float | None], None
        ],
        idle_step: Callable[[float | None, float | None], bool] | None = None,
    ) -> dict[str, Any]:
        while True:
            now = time.monotonic()
            if self.deadline is not None and now >= self.deadline:
                self._stats["deadline_reached"] = True
                break

            self._ingest_due(
                now,
                process_control=process_control,
                process_dense=process_dense,
            )

            if self._pending:
                item = self._pending.popleft()
                due = self.absolute_due(item)
                lag = max(0.0, time.monotonic() - due)
                self._stats["mapping_packets_started"] += 1
                try:
                    process_packet(
                        item,
                        lag,
                        self._next_control_due(),
                        self.deadline,
                    )
                except ControlPreempted:
                    self._stats["mapping_packets_preempted_by_control"] += 1
                except DeadlineReached:
                    self._stats["deadline_reached"] = True
                    self._stats["deadline_source_id"] = item.source_id
                    break
                else:
                    self._stats["mapping_packets_completed"] += 1
                continue

            next_arrival = self._next_arrival_due()
            if idle_step is not None:
                try:
                    if idle_step(next_arrival, self.deadline):
                        continue
                except DeadlineReached:
                    self._stats["deadline_reached"] = True
                    self._stats["deadline_source_id"] = "idle"
                    break

            if next_arrival is None:
                break
            wake_at = next_arrival
            if self.deadline is not None:
                wake_at = min(wake_at, self.deadline)
            wait_seconds = wake_at - time.monotonic()
            if wait_seconds > 0:
                time.sleep(wait_seconds)

        self._stats["timeline_items_ingested"] = self._cursor
        self._stats["timeline_items_not_ingested"] = len(self.timeline) - self._cursor
        self._stats["mapping_packets_pending_at_stop"] = len(self._pending)
        lag_values = self._stats.pop("arrival_lag_seconds")
        self._stats["arrival_lag_seconds_max"] = max(lag_values, default=0.0)
        self._stats["arrival_lag_seconds_mean"] = (
            sum(lag_values) / len(lag_values) if lag_values else 0.0
        )
        return dict(self._stats)
