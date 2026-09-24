"""Generation-scoped dense-gradient ticket for bounded online topology.

Persistent per-Gaussian evidence follows the author-code structure of TileGS
commit 7f109a403ed522ba5ec7610f3d4778c363b68b11. The actual mutation is delegated
to VIGS's port of Taming 3DGS commit
fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16: weighted multinomial sampling
without replacement under an explicit ticket. Dense RGB contributes only
appearance-gradient evidence; it never invents depth or directly births 3D
points.
"""

from __future__ import annotations

import collections

import torch


class DenseGradientTopologyTicket:
    """Accumulate repeated dense evidence and spend it at native events."""

    TOP_K_PER_VIEW = 1024
    MIN_DISTINCT_DENSE_UIDS = 2

    def __init__(self, *, seed: int) -> None:
        self.seed = int(seed)
        self.generation: int | None = None
        self._uids_by_point: dict[int, set[int]] = {}
        self._consumed_point_ids: set[int] = set()
        self._generator: torch.Generator | None = None
        self.dense_observations = 0
        self.events: list[dict[str, object]] = []

    def bind_generation(self, gaussians, generation: int) -> None:
        generation = int(generation)
        setattr(gaussians, "_exp78b_dense_ticket_generation", generation)
        self.generation = generation
        self._uids_by_point.clear()
        self._consumed_point_ids.clear()
        self._generator = torch.Generator(
            device=gaussians.get_xyz.device
        ).manual_seed(self.seed + 1_000_003 * generation)

    def _check_generation(self, gaussians) -> int:
        observed = getattr(
            gaussians, "_exp78b_dense_ticket_generation", None
        )
        if observed is None or int(observed) != self.generation:
            raise ValueError("dense topology ticket saw an unbound map generation")
        return int(observed)

    @torch.no_grad()
    def observe(self, gaussians, dense_uid: int, gradient: torch.Tensor) -> None:
        self._check_generation(gaussians)
        if gradient is None:
            raise ValueError("dense topology ticket needs an f_dc gradient")
        row_count = int(gaussians.get_xyz.shape[0])
        if int(gradient.shape[0]) != row_count:
            raise ValueError(
                "dense ticket gradient/Gaussian row mismatch: "
                f"{int(gradient.shape[0])} != {row_count}"
            )
        scores = torch.linalg.vector_norm(
            gradient.detach().reshape(row_count, -1), dim=1
        )
        positive = torch.isfinite(scores) & (scores > 0)
        count = min(
            self.TOP_K_PER_VIEW,
            int(positive.count_nonzero().item()),
        )
        if count:
            positive_rows = positive.nonzero(as_tuple=True)[0]
            local_order = torch.topk(
                scores[positive_rows], count, sorted=False
            ).indices
            rows = positive_rows[local_order]
            point_ids = gaussians.point_ids[rows.detach().cpu()].tolist()
            uid = int(dense_uid)
            for point_id in point_ids:
                self._uids_by_point.setdefault(
                    int(point_id), set()
                ).add(uid)
        self.dense_observations += 1

    @torch.no_grad()
    def mutate(self, gaussians, *, scene_extent: float, regular_added: int) -> dict:
        generation = self._check_generation(gaussians)
        regular_added = max(0, int(regular_added))
        point_ids = [int(value) for value in gaussians.point_ids.tolist()]
        weights = torch.as_tensor(
            [
                (
                    len(self._uids_by_point.get(point_id, ()))
                    if point_id not in self._consumed_point_ids
                    and len(self._uids_by_point.get(point_id, ()))
                    >= self.MIN_DISTINCT_DENSE_UIDS
                    else 0
                )
                for point_id in point_ids
            ],
            dtype=torch.float32,
            device=gaussians.get_xyz.device,
        )
        persistent_candidates = int((weights > 0).count_nonzero().item())
        before = int(gaussians.get_xyz.shape[0])
        result = gaussians.densify_and_clone_with_budget(
            weights,
            regular_added,
            scene_extent,
            generator=self._generator,
        )
        selected_ids = {
            int(value) for value in result["selected_point_ids"]
        }
        self._consumed_point_ids.update(selected_ids)
        record = {
            "map_generation": generation,
            "regular_added_ticket": regular_added,
            "persistent_candidates_before_scale_filter": (
                persistent_candidates
            ),
            "small_scale_eligible": int(result["eligible"]),
            "selected_without_replacement": int(result["selected"]),
            "gaussians_before": before,
            "gaussians_after": int(gaussians.get_xyz.shape[0]),
        }
        self.events.append(record)
        return record

    def summary(self) -> dict[str, object]:
        distinct_counts = [
            len(uids) for uids in self._uids_by_point.values()
        ]
        return {
            "enabled": True,
            "protocol": "generation_scoped_dense_gradient_ticket_v1",
            "top_k_per_view": self.TOP_K_PER_VIEW,
            "minimum_distinct_dense_uids": self.MIN_DISTINCT_DENSE_UIDS,
            "budget_mode": "match_regular_additions",
            "weighted_without_replacement": True,
            "extra_renders": 0,
            "extra_adam_steps": 0,
            "dense_observations": self.dense_observations,
            "final_map_generation": self.generation,
            "current_generation_nominated_points": len(
                self._uids_by_point
            ),
            "current_generation_repeated_points": sum(
                count >= self.MIN_DISTINCT_DENSE_UIDS
                for count in distinct_counts
            ),
            "consumed_parent_ids": len(self._consumed_point_ids),
            "events": self.events,
            "topology_events": len(self.events),
            "requested_mutations": sum(
                int(row["regular_added_ticket"]) for row in self.events
            ),
            "selected_mutations": sum(
                int(row["selected_without_replacement"])
                for row in self.events
            ),
        }
