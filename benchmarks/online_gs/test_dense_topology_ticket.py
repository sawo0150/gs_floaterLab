import pathlib
import sys
import unittest

import torch


sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dense_topology_ticket import DenseGradientTopologyTicket


class _Gaussians:
    def __init__(self, count):
        self._xyz = torch.zeros((count, 3))
        self.point_ids = torch.arange(100, 100 + count, dtype=torch.int64)

    @property
    def get_xyz(self):
        return self._xyz

    def densify_and_clone_with_budget(
        self,
        scores,
        budget,
        scene_extent,
        *,
        generator,
        preserve_densification_stats=False,
    ):
        candidates = (scores > 0).nonzero(as_tuple=True)[0]
        selected = candidates[: min(int(budget), len(candidates))]
        selected_ids = self.point_ids[selected.cpu()].tolist()
        count = len(selected_ids)
        self._xyz = torch.cat((self._xyz, torch.zeros((count, 3))))
        self.point_ids = torch.cat(
            (
                self.point_ids,
                torch.arange(1000, 1000 + count, dtype=torch.int64),
            )
        )
        return {
            "requested": int(budget),
            "eligible": len(candidates),
            "selected": count,
            "preserved_densification_stats": preserve_densification_stats,
            "selected_point_ids": selected_ids,
        }


class DenseGradientTopologyTicketTest(unittest.TestCase):
    def test_requires_two_distinct_dense_views_and_consumes_once(self):
        model = _Gaussians(4)
        ticket = DenseGradientTopologyTicket(seed=7)
        ticket.bind_generation(model, 2)
        gradient = torch.tensor([[[4.0]], [[3.0]], [[2.0]], [[1.0]]])
        ticket.observe(model, 10, gradient)
        ticket.observe(model, 10, gradient)
        self.assertEqual(ticket.summary()["current_generation_repeated_points"], 0)
        ticket.observe(model, 11, gradient)
        record = ticket.mutate(
            model, scene_extent=1.0, regular_added=2
        )
        self.assertEqual(record["selected_without_replacement"], 2)
        self.assertEqual(ticket.summary()["consumed_parent_ids"], 2)

    def test_reset_discards_previous_generation_evidence(self):
        ticket = DenseGradientTopologyTicket(seed=7)
        first = _Gaussians(2)
        ticket.bind_generation(first, 0)
        gradient = torch.ones((2, 1, 1))
        ticket.observe(first, 1, gradient)
        ticket.observe(first, 2, gradient)
        self.assertEqual(ticket.summary()["current_generation_repeated_points"], 2)

        second = _Gaussians(2)
        ticket.bind_generation(second, 1)
        self.assertEqual(ticket.summary()["current_generation_repeated_points"], 0)

    def test_first_persistence_spends_once_and_preserves_stats(self):
        model = _Gaussians(4)
        ticket = DenseGradientTopologyTicket(
            seed=7, mode="first_persistence"
        )
        ticket.bind_generation(model, 0)
        gradient = torch.tensor([[[4.0]], [[3.0]], [[2.0]], [[1.0]]])
        ticket.observe(model, 10, gradient)
        self.assertIsNone(
            ticket.mutate_first_persistence(model, scene_extent=1.0)
        )
        ticket.observe(model, 11, gradient)
        record = ticket.mutate_first_persistence(
            model, scene_extent=1.0
        )
        self.assertEqual(record["selected_without_replacement"], 4)
        self.assertTrue(record["preserved_densification_stats"])
        self.assertIsNone(
            ticket.mutate_first_persistence(model, scene_extent=1.0)
        )


if __name__ == "__main__":
    unittest.main()
