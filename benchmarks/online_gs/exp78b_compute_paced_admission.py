#!/usr/bin/env python3
"""Pure scheduling state for exp78-B compute-paced dense admission.

The controller deliberately owns no images, poses, CUDA tensors, wall clock,
dataset labels, or stream horizon.  One global causal seed breaks the initial
deadlock.  Afterwards, only completed dense-view updates can pay for another
already-arrived candidate.  Credit is destroyed whenever no candidate is
waiting, so past work can never pre-purchase a future observation.
"""

from __future__ import annotations

import collections
from collections.abc import Callable, Hashable, Iterable
from typing import Any


PROTOCOL = "exp78b_compute_paced_dense_admission_v1"


class ComputePacedDenseAdmission:
    """Admit one view per fixed number of completed dense-view updates."""

    def __init__(self, token_cost: int) -> None:
        self.token_cost = int(token_cost)
        if self.token_cost <= 0:
            raise ValueError("token_cost must be positive")
        self._pending: dict[Hashable, collections.deque[tuple]] = {}
        self._known_uids: set[int] = set()
        self._admitted_per_interval: collections.Counter = collections.Counter()
        self._last_service_updates = 0
        self._service_credit = 0
        self._bootstrapped = False
        self.candidates_arrived = 0
        self.duplicate_candidates_ignored = 0
        self.bootstrap_admissions = 0
        self.paid_admissions = 0
        self.invalid_candidates_dropped = 0
        self.service_updates_minted = 0
        self.service_updates_spent = 0
        self.service_updates_discarded = 0
        self.service_clock_resets = 0
        self.no_prepurchase_violations = 0

    @staticmethod
    def _uid(record: tuple) -> int:
        return int(record[0])

    def _eligible_intervals(self) -> list[Hashable]:
        return [key for key, values in self._pending.items() if values]

    def _discard_credit(self) -> None:
        self.service_updates_discarded += self._service_credit
        self._service_credit = 0

    def add_interval(
        self,
        interval: Hashable,
        ordered_records: Iterable[tuple],
        *,
        bootstrap: bool = True,
    ) -> list[tuple]:
        """Add an already-arrived interval and return its global seed, if any."""
        if interval in self._pending:
            return []
        values: collections.deque[tuple] = collections.deque()
        for record in ordered_records:
            uid = self._uid(record)
            if uid in self._known_uids:
                self.duplicate_candidates_ignored += 1
                continue
            self._known_uids.add(uid)
            values.append(record)
            self.candidates_arrived += 1
        self._pending[interval] = values
        return self.bootstrap() if bootstrap else []

    def bootstrap(
        self,
        *,
        is_valid: Callable[[tuple], bool] | None = None,
    ) -> list[tuple]:
        """Materialize exactly one globally free valid seed."""
        if self._bootstrapped:
            return []
        while True:
            eligible = self._eligible_intervals()
            if not eligible:
                return []
            interval = min(
                eligible,
                key=lambda key: (
                    self._admitted_per_interval[key],
                    repr(key),
                ),
            )
            seed = self._pending[interval].popleft()
            if is_valid is not None and not is_valid(seed):
                self.invalid_candidates_dropped += 1
                continue
            self._bootstrapped = True
            self.bootstrap_admissions += 1
            self._admitted_per_interval[interval] += 1
            return [seed]

    def admit(
        self,
        completed_dense_view_updates: int,
        *,
        is_valid: Callable[[tuple], bool] | None = None,
    ) -> list[tuple]:
        """Spend completed-work credit on waiting causal candidates.

        A decreasing service clock denotes a mapper reset.  Work accumulated
        by the old Gaussian map is discarded and cannot be combined with the
        new map's service.  Invalidated candidates (for example, a UID that
        later became a tracked keyframe) are removed without spending credit.
        """
        service = max(0, int(completed_dense_view_updates))
        if service < self._last_service_updates:
            self._discard_credit()
            self._last_service_updates = service
            self.service_clock_resets += 1
            delta = 0
        else:
            delta = service - self._last_service_updates
            self._last_service_updates = service
        self._service_credit += delta
        self.service_updates_minted += delta

        if not self._eligible_intervals():
            self._discard_credit()
            if self._service_credit != 0:
                self.no_prepurchase_violations += 1
            return []

        quota = self._service_credit // self.token_cost
        admitted: list[tuple] = []
        while len(admitted) < quota:
            eligible = self._eligible_intervals()
            if not eligible:
                break
            interval = min(
                eligible,
                key=lambda key: (
                    self._admitted_per_interval[key],
                    repr(key),
                ),
            )
            record = self._pending[interval].popleft()
            if is_valid is not None and not is_valid(record):
                self.invalid_candidates_dropped += 1
                continue
            admitted.append(record)
            self._admitted_per_interval[interval] += 1

        spent = len(admitted) * self.token_cost
        self._service_credit -= spent
        self.service_updates_spent += spent
        self.paid_admissions += len(admitted)
        if not self._eligible_intervals():
            self._discard_credit()
        if not self._eligible_intervals() and self._service_credit != 0:
            self.no_prepurchase_violations += 1
        return admitted

    def scale_pending_translations(self, scale: float) -> None:
        """Apply the causal IMU metric-rescale event to waiting poses."""
        value = float(scale)
        for records in self._pending.values():
            for record in records:
                record[2][:3, 3] *= value

    def reset_service_clock(self, completed_dense_view_updates: int = 0) -> None:
        """Synchronize an explicit mapper reset without dropping observations."""
        self._discard_credit()
        self._last_service_updates = max(
            0, int(completed_dense_view_updates)
        )
        self.service_clock_resets += 1

    @property
    def pending_count(self) -> int:
        return sum(len(values) for values in self._pending.values())

    def summary(self) -> dict[str, Any]:
        accounting_error = (
            self.service_updates_minted
            - self.service_updates_spent
            - self.service_updates_discarded
            - self._service_credit
        )
        return {
            "protocol": PROTOCOL,
            "token_cost_dense_view_updates": self.token_cost,
            "global_seed_only": True,
            "interval_bootstrap": False,
            "future_frames_used": False,
            "dataset_name_used": False,
            "stream_horizon_used": False,
            "candidates_arrived": self.candidates_arrived,
            "unique_candidate_uids": len(self._known_uids),
            "duplicate_candidates_ignored": self.duplicate_candidates_ignored,
            "pending_candidates": self.pending_count,
            "bootstrap_admissions": self.bootstrap_admissions,
            "paid_admissions": self.paid_admissions,
            "invalid_candidates_dropped": self.invalid_candidates_dropped,
            "last_completed_dense_view_updates": self._last_service_updates,
            "service_updates_minted": self.service_updates_minted,
            "service_updates_spent": self.service_updates_spent,
            "service_updates_discarded_no_prepurchase": (
                self.service_updates_discarded
            ),
            "service_credit_remaining": self._service_credit,
            "service_accounting_error": accounting_error,
            "service_clock_resets": self.service_clock_resets,
            "no_prepurchase_violations": self.no_prepurchase_violations,
            "admitted_per_interval": {
                repr(key): int(value)
                for key, value in sorted(
                    self._admitted_per_interval.items(), key=lambda item: repr(item[0])
                )
            },
        }
