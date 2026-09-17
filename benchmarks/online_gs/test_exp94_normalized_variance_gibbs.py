#!/usr/bin/env python3
"""Regression checks for the normalized-variance Gibbs law in both queues."""

import collections
import math
import sys
import unittest


sys.path.insert(0, "/home/intern/VIGS-SLAM-paper-full")
from vigs.map_scheduler import (  # noqa: E402
    ServiceShortfallIntervalReplayQueue,
    TransactionalGlobalKeyframeServiceShortfallQueue,
)


class NormalizedVarianceGibbsTest(unittest.TestCase):
    def setUp(self):
        self.gamma = math.log(1.5)
        self.counts = collections.Counter({"a": 0, "b": 1, "c": 3})
        self.candidates = set(self.counts)
        self.total = sum(self.counts.values())

    def assert_gibbs_log_odds(self, weights):
        for left in self.candidates:
            for right in self.candidates:
                expected = -self.gamma * (
                    self.counts[left] - self.counts[right]
                ) / (self.total + 1)
                self.assertAlmostEqual(weights[left] - weights[right], expected)

    def test_dense_and_auxiliary_queue_uses_per_view_gibbs(self):
        queue = ServiceShortfallIntervalReplayQueue(
            selection_potential="normalized_variance"
        )
        queue._current_candidates = self.candidates
        queue.selection_counts.update(self.counts)
        grouped = {key: [key] for key in self.candidates}
        rows = queue._interval_distribution(grouped)
        self.assert_gibbs_log_odds(
            {key: row["log_weight"] for key, row in rows.items()}
        )

    def test_native_keyframe_queue_uses_per_view_gibbs(self):
        queue = TransactionalGlobalKeyframeServiceShortfallQueue(
            selection_potential="normalized_variance"
        )
        queue._current_candidates = self.candidates
        self.assert_gibbs_log_odds(queue._weights(self.candidates, self.counts))

    def test_effective_balancing_weakens_as_total_service_grows(self):
        queue = TransactionalGlobalKeyframeServiceShortfallQueue(
            selection_potential="normalized_variance"
        )
        queue._current_candidates = self.candidates
        early = queue._weights(self.candidates, self.counts)
        later_counts = collections.Counter({key: value + 10 for key, value in self.counts.items()})
        later = queue._weights(self.candidates, later_counts)
        self.assertLess(later["a"] - later["c"], early["a"] - early["c"])
        self.assertAlmostEqual(
            (later["a"] - later["c"]) / (early["a"] - early["c"]),
            (self.total + 1) / (sum(later_counts.values()) + 1),
        )


if __name__ == "__main__":
    unittest.main()
