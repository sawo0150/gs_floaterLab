#!/usr/bin/env python3

from dataclasses import dataclass

from exp78b_newborn_consolidation import (
    ObservationConditionedNewbornConsolidation,
)


@dataclass
class View:
    causal_left_keyframe: int
    causal_right_keyframe: int


def commit_points(controller, dense_uid, point_ids):
    controller.begin_projected_dense_service()
    controller.observe_projected_dense_points(
        [(point_id, dense_uid) for point_id in point_ids]
    )
    controller.commit_projected_dense_service()


def test_endpoint_draws_alone_do_not_mature_points():
    controller = ObservationConditionedNewbornConsolidation()
    viewpoints = {10: View(1, 2), 11: View(1, 2)}
    assert controller.protected_point_ids([101, 102], 0) == {101, 102}
    controller.observe_dense_draw(
        [("dense", 10), ("dense", 11)], viewpoints
    )
    assert controller.protected_point_ids([101, 102], 0) == {101, 102}


def test_two_committed_distinct_dense_services_mature_only_visible_point():
    controller = ObservationConditionedNewbornConsolidation()
    assert controller.protected_point_ids([101, 102], 0) == {101, 102}
    commit_points(controller, 10, [101])
    assert controller.protected_point_ids([101, 102], 0) == {101, 102}
    commit_points(controller, 11, [101])
    assert controller.protected_point_ids([101, 102], 0) == {102}


def test_repeating_one_committed_dense_view_is_not_independent_support():
    controller = ObservationConditionedNewbornConsolidation()
    controller.protected_point_ids([101], 0)
    commit_points(controller, 10, [101])
    commit_points(controller, 10, [101])
    assert controller.protected_point_ids([101], 1) == {101}


def test_two_views_in_one_adam_transaction_count_once():
    controller = ObservationConditionedNewbornConsolidation()
    controller.protected_point_ids([101], 0)
    controller.begin_projected_dense_service()
    controller.observe_projected_dense_points([(101, 10), (101, 11)])
    controller.commit_projected_dense_service()
    assert controller.protected_point_ids([101], 0) == {101}
    commit_points(controller, 12, [101])
    assert controller.protected_point_ids([101], 0) == set()


def test_uncommitted_pending_row_service_does_not_mature_lineage():
    controller = ObservationConditionedNewbornConsolidation()
    controller.protected_point_ids([101, 102], 0)
    controller.begin_projected_dense_service()
    controller.observe_projected_dense_points([(101, 10), (102, 11)])
    assert controller.protected_point_ids([101, 102], 0) == {101, 102}
    assert controller.summary()["pending_row_service_pairs"] == 2
    controller.begin_projected_dense_service()
    assert controller.summary()["pending_row_service_pairs"] == 0


def test_two_completed_opportunity_passes_release_unsupported_lineage():
    controller = ObservationConditionedNewbornConsolidation()
    assert controller.protected_point_ids([107], 4) == {107}
    assert controller.protected_point_ids([107], 6) == {107}
    assert controller.protected_point_ids([107], 7) == set()
    assert controller.summary()["points_mature_opportunity"] == 1


def test_unrelated_dense_interval_does_not_mature_point():
    controller = ObservationConditionedNewbornConsolidation()
    viewpoints = {10: View(3, 4), 11: View(3, 4)}
    controller.protected_point_ids([101], 0)
    controller.observe_dense_draw([("dense", 10), ("dense", 11)], viewpoints)
    assert controller.protected_point_ids([101], 0) == {101}


def test_explicit_map_reset_invalidates_old_row_service():
    controller = ObservationConditionedNewbornConsolidation()
    controller.protected_point_ids([101], 0)
    commit_points(controller, 10, [101])
    commit_points(controller, 11, [101])
    assert controller.protected_point_ids([101], 0) == set()
    controller.reset_active_map()
    assert controller.protected_point_ids([101], 0) == {101}


def test_summary_declares_no_phase_or_dataset_signal():
    summary = ObservationConditionedNewbornConsolidation().summary()
    assert summary["causal_completed_service_only"] is True
    assert summary["dataset_name_used"] is False
    assert summary["frame_or_iteration_cutoff_used"] is False
    assert summary["stream_horizon_used"] is False
    assert summary["gaussian_count_cutoff_used"] is False
    assert summary["global_topology_freeze_used"] is False
    assert summary["endpoint_draw_matures_lineage"] is False
    assert summary["maturity_granularity"] == "stable_gaussian_point_id"
    assert summary["one_certificate_per_point_per_adam_step"] is True
