"""Behavior-neutral dense-gradient locality probe for online topology.

The design is informed by TileGS's persistent per-Gaussian appearance/failure
counters (author code commit 7f109a403ed522ba5ec7610f3d4778c363b68b11)
and Taming 3DGS's explicit without-replacement mutation budgets (author code
commit fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16).  No code is copied from
either implementation.  In particular, this probe does not use TileGS's CUDA
tile-analysis path: it observes gradients already produced by a paid dense
RGB replay render and never mutates the map.
"""

from __future__ import annotations

import collections
import statistics
import time

import torch


class DenseTopologyEvidenceProbe:
    """Measure concentration and repetition of dense appearance gradients."""

    TOP_K = (256, 1024, 4096)

    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []
        self.nominations = {
            k: collections.Counter() for k in self.TOP_K
        }
        self._last_top1024: set[int] | None = None
        self._consecutive_jaccard: list[float] = []
        self.elapsed_seconds = 0.0

    @torch.no_grad()
    def observe(self, gaussians, dense_uid: int, gradient: torch.Tensor) -> None:
        started = time.perf_counter()
        if gradient is None:
            raise ValueError("dense topology evidence needs an f_dc gradient")
        row_count = int(gaussians.get_xyz.shape[0])
        if int(gradient.shape[0]) != row_count:
            raise ValueError(
                "dense gradient/Gaussian row mismatch: "
                f"{int(gradient.shape[0])} != {row_count}"
            )
        if int(gaussians.point_ids.shape[0]) != row_count:
            raise ValueError("stable point-id/Gaussian row mismatch")

        scores = torch.linalg.vector_norm(
            gradient.detach().reshape(row_count, -1), dim=1
        )
        positive = torch.isfinite(scores) & (scores > 0)
        positive_count = int(positive.count_nonzero().item())
        total_mass = float(scores[positive].sum().item())
        largest_k = min(max(self.TOP_K), positive_count)
        if largest_k:
            positive_rows = positive.nonzero(as_tuple=True)[0]
            top_values, local_order = torch.topk(
                scores[positive_rows], largest_k, sorted=True
            )
            top_rows = positive_rows[local_order]
            top_ids = gaussians.point_ids[
                top_rows.detach().cpu()
            ].tolist()
            top_values_cpu = top_values.detach().float().cpu().tolist()
        else:
            top_ids = []
            top_values_cpu = []

        mass_fraction = {}
        candidate_counts = {}
        for k in self.TOP_K:
            actual = min(k, positive_count)
            candidate_counts[str(k)] = actual
            selected_ids = [int(value) for value in top_ids[:actual]]
            self.nominations[k].update(selected_ids)
            selected_mass = float(sum(top_values_cpu[:actual]))
            mass_fraction[str(k)] = (
                0.0 if total_mass <= 0.0 else selected_mass / total_mass
            )

        current_top1024 = set(
            int(value) for value in top_ids[: min(1024, positive_count)]
        )
        if self._last_top1024 is not None:
            union = current_top1024 | self._last_top1024
            self._consecutive_jaccard.append(
                1.0
                if not union
                else len(current_top1024 & self._last_top1024) / len(union)
            )
        self._last_top1024 = current_top1024
        self.records.append(
            {
                "opportunity": len(self.records),
                "dense_uid": int(dense_uid),
                "gaussians": row_count,
                "positive_gradient_rows": positive_count,
                "positive_fraction": (
                    0.0 if row_count == 0 else positive_count / row_count
                ),
                "total_gradient_mass": total_mass,
                "candidate_counts": candidate_counts,
                "mass_fraction": mass_fraction,
            }
        )
        self.elapsed_seconds += time.perf_counter() - started

    @staticmethod
    def _mean(values: list[float]) -> float:
        return 0.0 if not values else float(statistics.fmean(values))

    def summary(self, live_point_ids: torch.Tensor) -> dict[str, object]:
        live = set(int(value) for value in live_point_ids.tolist())
        repeated = {}
        for k, counts in self.nominations.items():
            keys = set(counts)
            repeated[str(k)] = {
                "unique_lifetime": len(keys),
                "nominated_at_least_2": sum(
                    value >= 2 for value in counts.values()
                ),
                "nominated_at_least_3": sum(
                    value >= 3 for value in counts.values()
                ),
                "nominated_at_least_5": sum(
                    value >= 5 for value in counts.values()
                ),
                "live_unique": len(keys & live),
                "live_nominated_at_least_2": sum(
                    point_id in live and value >= 2
                    for point_id, value in counts.items()
                ),
                "live_nominated_at_least_3": sum(
                    point_id in live and value >= 3
                    for point_id, value in counts.items()
                ),
            }
        return {
            "enabled": True,
            "behavior_neutral": True,
            "extra_renders": 0,
            "mutation_rows": 0,
            "opportunities": len(self.records),
            "unique_dense_uids": len(
                {int(row["dense_uid"]) for row in self.records}
            ),
            "probe_wall_seconds": float(self.elapsed_seconds),
            "mean_gaussians": self._mean(
                [float(row["gaussians"]) for row in self.records]
            ),
            "mean_positive_gradient_rows": self._mean(
                [
                    float(row["positive_gradient_rows"])
                    for row in self.records
                ]
            ),
            "mean_positive_fraction": self._mean(
                [float(row["positive_fraction"]) for row in self.records]
            ),
            "mean_gradient_mass_fraction": {
                str(k): self._mean(
                    [
                        float(row["mass_fraction"][str(k)])
                        for row in self.records
                    ]
                )
                for k in self.TOP_K
            },
            "mean_consecutive_top1024_jaccard": self._mean(
                self._consecutive_jaccard
            ),
            "persistent_nominations": repeated,
            "records": self.records,
        }
