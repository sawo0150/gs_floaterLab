#!/usr/bin/env python3
"""Committed point-service maturity state for exp78-B newborn Gaussians.

This module deliberately owns no frame, iteration, stream-fraction, dataset,
Gaussian-count, or evaluation threshold.  It reuses final-v7's smallest
repeated-evidence contract: two distinct supervision opportunities, or two
complete replay opportunity passes when direct support never arrives.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Protocol, Sequence


FINAL_V7_REQUIRED_OPPORTUNITIES = 2
# The queue increments ``epochs_started`` when it fills a new epoch.  As in
# TopologyReplayController, an advance of three from the registration epoch
# proves that two preceding shuffled opportunity passes completed.
FINAL_V7_TWO_PASS_EPOCH_ADVANCE = 3


class DenseEndpointView(Protocol):
    causal_left_keyframe: int
    causal_right_keyframe: int


class ObservationConditionedNewbornConsolidation:
    """Protect each stable Gaussian point only while supervision is immature.

    Endpoint selection alone is only telemetry: it does not prove that a
    newborn Gaussian was visible or updated.  A point matures only after that
    exact stable ``point_id`` was visible in two *distinct* causal dense
    views on two committed Adam steps and received a non-zero projected
    appearance gradient.  A point that never receives direct row service is
    released after the replay queue certifies two full opportunity passes,
    preventing permanent protection in sparse or partially held-out
    intervals.  Both rules depend only on already-completed causal service.
    """

    protocol = "exp78b_observation_conditioned_newborn_consolidation_v3"

    def __init__(self) -> None:
        self.first_seen_epoch: dict[int, int] = {}
        self.endpoint_draw_uids: dict[int, set[int]] = defaultdict(set)
        self.first_service_uid: dict[int, int] = {}
        self.pending_point_service_uid: dict[int, int] = {}
        self.mature_direct: set[int] = set()
        self.mature_opportunity: set[int] = set()
        self.dense_draws_observed = 0
        self.dense_unique_draws: set[int] = set()
        self.row_service_commits = 0
        self.row_service_commits_with_rows = 0
        self.row_service_pairs_committed = 0
        self.map_resets = 0
        self.topology_queries = 0
        self.protected_point_query_sum = 0
        self.protected_point_query_max = 0
        self.last_protected: set[int] = set()
        self.topology_events: list[dict[str, int]] = []

    @staticmethod
    def _dense_uid(key: object) -> int | None:
        if not isinstance(key, tuple) or len(key) < 2 or key[0] != "dense":
            return None
        return int(key[1])

    def observe_dense_draw(
        self,
        keys: Sequence[object],
        viewpoints: Mapping[int, DenseEndpointView],
    ) -> None:
        """Record selector outputs without treating endpoint draws as service."""
        for key in keys:
            dense_uid = self._dense_uid(key)
            if dense_uid is None:
                continue
            viewpoint = viewpoints.get(dense_uid)
            if viewpoint is None:
                continue
            endpoints = {
                int(value)
                for value in (
                    getattr(viewpoint, "causal_left_keyframe", -1),
                    getattr(viewpoint, "causal_right_keyframe", -1),
                )
                if int(value) >= 0
            }
            self.dense_draws_observed += 1
            self.dense_unique_draws.add(dense_uid)
            for keyframe_uid in endpoints:
                self.endpoint_draw_uids[keyframe_uid].add(dense_uid)

    def begin_projected_dense_service(self) -> None:
        """Start a tentative dense service transaction for the next Adam step."""
        self.pending_point_service_uid.clear()

    def observe_projected_dense_points(
        self,
        services: Sequence[tuple[int, int]],
    ) -> None:
        """Stage visible, gradient-bearing ``(point_id, dense_uid)`` evidence.

        This method is intentionally non-committing.  If the optimizer step
        fails or never executes, a later ``begin`` discards this evidence.
        At most one dense UID is accepted per point in one transaction, so a
        batch containing multiple views cannot fake two repeated services.
        """
        for point_id, dense_uid in services:
            point = int(point_id)
            uid = int(dense_uid)
            if point >= 0 and point not in self.mature_direct:
                self.pending_point_service_uid.setdefault(point, uid)

    def commit_projected_dense_service(self) -> None:
        """Publish staged row evidence only after the shared Adam step commits."""
        self.row_service_commits += 1
        committed_pairs = len(self.pending_point_service_uid)
        if committed_pairs:
            self.row_service_commits_with_rows += 1
            self.row_service_pairs_committed += committed_pairs
        for point, dense_uid in self.pending_point_service_uid.items():
            first_uid = self.first_service_uid.get(point)
            if first_uid is None:
                self.first_service_uid[point] = dense_uid
            elif first_uid != dense_uid:
                self.mature_direct.add(point)
                self.first_service_uid.pop(point, None)
        self.pending_point_service_uid.clear()

    def reset_active_map(self) -> None:
        """Invalidate evidence for rows deleted by an explicit map reset."""
        self.map_resets += 1
        self.first_seen_epoch.clear()
        self.first_service_uid.clear()
        self.pending_point_service_uid.clear()
        self.mature_direct.clear()
        self.mature_opportunity.clear()
        self.last_protected.clear()

    def protected_point_ids(
        self,
        point_ids: Iterable[int],
        epochs_started: int,
        *,
        record_query: bool = True,
    ) -> set[int]:
        """Return immature stable points using only completed causal evidence."""
        epoch = max(0, int(epochs_started))
        points = {int(value) for value in point_ids if int(value) >= 0}

        # Bound state by the live map.  Services can arrive before the first
        # topology query, so retain every live pre-registered point.
        self.first_seen_epoch = {
            point: first_epoch
            for point, first_epoch in self.first_seen_epoch.items()
            if point in points
        }
        self.first_service_uid = {
            point: dense_uid
            for point, dense_uid in self.first_service_uid.items()
            if point in points
        }
        self.mature_direct.intersection_update(points)
        self.mature_opportunity.intersection_update(points)
        for point in points:
            self.first_seen_epoch.setdefault(point, epoch)

        protected: set[int] = set()
        for point in points:
            if point in self.mature_direct:
                continue
            first_epoch = self.first_seen_epoch[point]
            if epoch - first_epoch >= FINAL_V7_TWO_PASS_EPOCH_ADVANCE:
                self.mature_opportunity.add(point)
                continue
            protected.add(point)

        if record_query:
            self.topology_queries += 1
            self.protected_point_query_sum += len(protected)
            self.protected_point_query_max = max(
                self.protected_point_query_max, len(protected)
            )
        self.last_protected = set(protected)
        return protected

    def observe_topology_result(
        self,
        *,
        epochs_started: int,
        protected_points: int,
        protected_rows_before: int,
        protected_rows_after: int,
        gaussian_count_before: int,
        gaussian_count_after: int,
    ) -> None:
        self.topology_events.append(
            {
                "epochs_started": int(epochs_started),
                "protected_points": int(protected_points),
                "protected_rows_before": int(protected_rows_before),
                "protected_rows_after": int(protected_rows_after),
                "gaussian_count_before": int(gaussian_count_before),
                "gaussian_count_after": int(gaussian_count_after),
            }
        )

    def summary(self) -> dict[str, object]:
        endpoint_draws = {
            str(keyframe_uid): len(values)
            for keyframe_uid, values in sorted(self.endpoint_draw_uids.items())
        }
        return {
            "protocol": self.protocol,
            "causal_completed_service_only": True,
            "dataset_name_used": False,
            "frame_or_iteration_cutoff_used": False,
            "stream_horizon_used": False,
            "gaussian_count_cutoff_used": False,
            "global_topology_freeze_used": False,
            "required_distinct_dense_opportunities": (
                FINAL_V7_REQUIRED_OPPORTUNITIES
            ),
            "direct_maturity_evidence": (
                "stable_point_visible_nonzero_projected_appearance_gradient_"
                "two_committed_adam_steps_distinct_dense_uid"
            ),
            "endpoint_draw_matures_lineage": False,
            "maturity_granularity": "stable_gaussian_point_id",
            "one_certificate_per_point_per_adam_step": True,
            "two_pass_epoch_advance": FINAL_V7_TWO_PASS_EPOCH_ADVANCE,
            "dense_draws_observed": self.dense_draws_observed,
            "dense_unique_draws": len(self.dense_unique_draws),
            "row_service_commits": self.row_service_commits,
            "row_service_commits_with_rows": self.row_service_commits_with_rows,
            "row_service_pairs_committed": self.row_service_pairs_committed,
            "pending_row_service_pairs": len(
                self.pending_point_service_uid
            ),
            "map_resets": self.map_resets,
            "points_seen": len(self.first_seen_epoch),
            "points_with_one_committed_service": len(self.first_service_uid),
            "points_mature_direct": len(self.mature_direct),
            "points_mature_opportunity": len(self.mature_opportunity),
            "points_last_protected": len(self.last_protected),
            "topology_queries": self.topology_queries,
            "protected_point_query_sum": self.protected_point_query_sum,
            "protected_point_query_max": self.protected_point_query_max,
            "endpoint_draw_distinct_dense_views_by_keyframe": endpoint_draws,
            "topology_events": list(self.topology_events),
        }
