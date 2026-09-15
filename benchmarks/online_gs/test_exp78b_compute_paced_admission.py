#!/usr/bin/env python3
"""CPU-only regression checks for exp78-B compute-paced admission."""

from __future__ import annotations

import unittest

import torch

from exp78b_compute_paced_admission import ComputePacedDenseAdmission


def record(uid: int) -> tuple:
    return (uid, None, torch.eye(4))


class ComputePacedDenseAdmissionTest(unittest.TestCase):
    def test_global_seed_then_paid_admission(self) -> None:
        controller = ComputePacedDenseAdmission(4)
        self.assertEqual(
            [value[0] for value in controller.add_interval((0, 10), [record(5), record(2)])],
            [5],
        )
        self.assertEqual(controller.admit(3), [])
        self.assertEqual([value[0] for value in controller.admit(4)], [2])
        summary = controller.summary()
        self.assertEqual(summary["bootstrap_admissions"], 1)
        self.assertEqual(summary["paid_admissions"], 1)
        self.assertEqual(summary["service_accounting_error"], 0)

    def test_no_prepurchase(self) -> None:
        controller = ComputePacedDenseAdmission(4)
        controller.admit(20)
        self.assertEqual(controller.summary()["service_credit_remaining"], 0)
        self.assertEqual(
            [value[0] for value in controller.add_interval((0, 10), [record(5), record(2)])],
            [5],
        )
        self.assertEqual(controller.admit(20), [])
        self.assertEqual(controller.admit(24)[0][0], 2)
        self.assertEqual(controller.summary()["no_prepurchase_violations"], 0)

    def test_invalid_candidate_does_not_spend_token(self) -> None:
        controller = ComputePacedDenseAdmission(2)
        controller.add_interval((0, 10), [record(5), record(2), record(8)])
        admitted = controller.admit(2, is_valid=lambda value: value[0] != 2)
        self.assertEqual([value[0] for value in admitted], [8])
        summary = controller.summary()
        self.assertEqual(summary["invalid_candidates_dropped"], 1)
        self.assertEqual(summary["service_updates_spent"], 2)

    def test_reset_discards_credit_but_keeps_pending(self) -> None:
        controller = ComputePacedDenseAdmission(4)
        controller.add_interval((0, 10), [record(5), record(2)])
        controller.admit(3)
        controller.reset_service_clock(0)
        self.assertEqual(controller.pending_count, 1)
        self.assertEqual(controller.admit(3), [])
        self.assertEqual(controller.admit(4)[0][0], 2)
        self.assertEqual(controller.summary()["service_accounting_error"], 0)

    def test_pending_pose_rescale(self) -> None:
        controller = ComputePacedDenseAdmission(4)
        waiting = record(2)
        waiting[2][0, 3] = 2.0
        controller.add_interval((0, 10), [record(5), waiting])
        controller.scale_pending_translations(3.0)
        self.assertEqual(float(controller.admit(4)[0][2][0, 3]), 6.0)


if __name__ == "__main__":
    unittest.main()
