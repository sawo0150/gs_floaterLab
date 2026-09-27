"""Causal dense-view evidence derived from the official LPM implementation.

The error-zone extraction below is a narrow adaptation of ``get_errormap``
from Surrey-UPLab/Localized-Gaussian-Point-Management, commit
``7c060267cf55df76992e9ef2b6df42133ba9349f`` (``lpm/utils.py``).  The
upstream constants and operations are intentionally kept fixed: mean
normalization with ``+0.01``, channel-summed absolute error, the 0.4 quantile,
16x16 non-overlapping patches, and an 85% significant-pixel threshold.

LPM is distributed under the Gaussian-Splatting research-only license; see
the pinned source checkout at ``/home/intern/gs_topology_references/lpm``.
This adapter is used for research/evaluation and records attribution here so
the borrowed implementation cannot be mistaken for an independently invented
operator.

Unlike full LPM, this probe performs no feature matching, triangulation,
additional render, or map mutation.  It consumes only the render/GT tensors
already present in a completed causal dense replay step.
"""

from __future__ import annotations

import collections
import math
import statistics
import time

import torch
import torch.nn.functional as F


LPM_UPSTREAM_COMMIT = "7c060267cf55df76992e9ef2b6df42133ba9349f"
LPM_UPSTREAM_FILE = "lpm/utils.py"
LPM_ERROR_QUANTILE = 0.4
LPM_PATCH_SIZE = 16
LPM_SIGNIFICANT_FRACTION = 0.85


@torch.no_grad()
def lpm_error_zone_map(
    image: torch.Tensor,
    gt_image: torch.Tensor,
) -> torch.Tensor:
    """Return the official LPM binary error-zone map for one RGB view.

    Inputs must be channel-first tensors with identical ``[C,H,W]`` shape.
    Keeping this function small and literal makes it testable against the
    downloaded author implementation without importing LPM's LightGlue stack.
    """

    if image.ndim != 3 or gt_image.ndim != 3:
        raise ValueError("LPM error-zone inputs must be [C,H,W] tensors")
    if image.shape != gt_image.shape:
        raise ValueError(
            "LPM error-zone render/GT shape mismatch: "
            f"{tuple(image.shape)} != {tuple(gt_image.shape)}"
        )
    if image.shape[1] < 1 or image.shape[2] < 1:
        raise ValueError("LPM error-zone inputs must have non-empty images")

    # Literal adaptation of upstream get_errormap(error_function="diff").
    image_adjust = image / (torch.mean(image) + 0.01)
    gt_adjust = gt_image / (torch.mean(gt_image) + 0.01)
    error_map = torch.abs(image_adjust - gt_adjust)
    error_map = torch.sum(error_map, dim=0)
    threshold = torch.quantile(error_map, LPM_ERROR_QUANTILE)
    error_mask = error_map > threshold

    height = int(image.shape[1])
    width = int(image.shape[2])
    pad_height = (
        (height + LPM_PATCH_SIZE - 1) // LPM_PATCH_SIZE * LPM_PATCH_SIZE
        - height
    )
    pad_width = (
        (width + LPM_PATCH_SIZE - 1) // LPM_PATCH_SIZE * LPM_PATCH_SIZE
        - width
    )
    error_mask = F.pad(
        error_mask,
        (0, pad_width, 0, pad_height),
        mode="constant",
        value=0,
    )
    patches = error_mask.unfold(
        0, LPM_PATCH_SIZE, LPM_PATCH_SIZE
    ).unfold(1, LPM_PATCH_SIZE, LPM_PATCH_SIZE)
    patch_sums = patches.sum(dim=(2, 3))
    significant_patches = patch_sums > (
        LPM_PATCH_SIZE * LPM_PATCH_SIZE * LPM_SIGNIFICANT_FRACTION
    )
    zone_map = significant_patches.repeat_interleave(
        LPM_PATCH_SIZE, dim=0
    ).repeat_interleave(LPM_PATCH_SIZE, dim=1)
    return zone_map[:height, :width].float()


class LpmErrorZoneEvidenceProbe:
    """Record LPM error-zone evidence from already-paid dense renders."""

    def __init__(self, *, behavior_neutral: bool = True) -> None:
        self.behavior_neutral = bool(behavior_neutral)
        self.records: list[dict[str, object]] = []
        self._current_generation: int | None = None
        self._scores_by_generation_uid: dict[
            tuple[int, int], list[float]
        ] = collections.defaultdict(list)
        self._cpu_enqueue_seconds = 0.0
        self._cuda_events: list[tuple[torch.cuda.Event, torch.cuda.Event]] = []
        self._pending_scores: dict[tuple[int, int], float] = {}
        self._pending_mass_priors: dict[tuple[int, int], float] = {}
        self._utility_scores_consumed = 0

    def bind_generation(self, generation: int) -> None:
        if (
            self._current_generation is not None
            and int(generation) != self._current_generation
        ):
            self._pending_scores.clear()
            self._pending_mass_priors.clear()
        self._current_generation = int(generation)

    @torch.no_grad()
    def observe(
        self,
        dense_uid: int,
        image: torch.Tensor,
        gt_image: torch.Tensor,
    ) -> None:
        if self._current_generation is None:
            raise ValueError("LPM error-zone evidence has no map generation")
        started = time.perf_counter()
        start_event = end_event = None
        if image.is_cuda:
            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)
            start_event.record()

        zone_map = lpm_error_zone_map(image.detach(), gt_image.detach())
        score = float(zone_map.mean().item())
        active_pixels = int(zone_map.count_nonzero().item())

        if end_event is not None:
            end_event.record()
            self._cuda_events.append((start_event, end_event))
        generation = int(self._current_generation)
        key = (generation, int(dense_uid))
        prior_count = len(self._scores_by_generation_uid[key])
        self._scores_by_generation_uid[key].append(score)
        self._pending_scores[key] = score
        # One official 16x16 LPM patch is the only pseudocount. Dividing by
        # the common total merely keeps the KL base measure in (0,1]; it
        # cancels from probabilities for equal-resolution views.
        patch_pixels = LPM_PATCH_SIZE * LPM_PATCH_SIZE
        image_pixels = int(image.shape[1]) * int(image.shape[2])
        self._pending_mass_priors[key] = float(
            (active_pixels + patch_pixels) / (image_pixels + patch_pixels)
        )
        self.records.append(
            {
                "opportunity": len(self.records),
                "map_generation": generation,
                "dense_uid": int(dense_uid),
                "observation_index_for_view": prior_count,
                "height": int(image.shape[1]),
                "width": int(image.shape[2]),
                "significant_pixel_fraction": score,
                "significant_pixels": active_pixels,
            }
        )
        self._cpu_enqueue_seconds += time.perf_counter() - started

    def _pending_key(self, dense_uid: int) -> tuple[int, int]:
        if self._current_generation is None:
            raise ValueError("LPM error-zone evidence has no map generation")
        return (int(self._current_generation), int(dense_uid))

    def consume_pending_score(self, dense_uid: int) -> float:
        """Consume this step's coverage after its Adam update succeeds."""

        key = self._pending_key(dense_uid)
        if key not in self._pending_scores:
            raise RuntimeError(
                "no LPM error-zone score was produced for completed dense "
                f"service {key!r}"
            )
        self._utility_scores_consumed += 1
        self._pending_mass_priors.pop(key)
        return float(self._pending_scores.pop(key))

    def consume_pending_mass_prior(self, dense_uid: int) -> float:
        """Consume `(active pixels + one patch)/(pixels + one patch)`."""

        key = self._pending_key(dense_uid)
        if key not in self._pending_mass_priors:
            raise RuntimeError(
                "no LPM error-zone mass was produced for completed dense "
                f"service {key!r}"
            )
        self._utility_scores_consumed += 1
        self._pending_scores.pop(key)
        return float(self._pending_mass_priors.pop(key))

    @staticmethod
    def _mean(values: list[float]) -> float:
        return 0.0 if not values else float(statistics.fmean(values))

    def summary(self) -> dict[str, object]:
        if self._cuda_events:
            torch.cuda.synchronize()
        gpu_milliseconds = float(
            math.fsum(
                start.elapsed_time(end) for start, end in self._cuda_events
            )
        )
        scores = [
            float(record["significant_pixel_fraction"])
            for record in self.records
        ]
        repeated_groups = [
            values
            for values in self._scores_by_generation_uid.values()
            if len(values) >= 2
        ]
        consecutive_same_view_abs_delta = [
            abs(right - left)
            for values in repeated_groups
            for left, right in zip(values, values[1:])
        ]
        nonzero = sum(value > 0.0 for value in scores)
        saturated = sum(value >= 1.0 for value in scores)
        unique_score_count = len({round(value, 12) for value in scores})
        return {
            "enabled": True,
            "behavior_neutral": self.behavior_neutral,
            "scheduler_utility_enabled": not self.behavior_neutral,
            "source_repository": (
                "https://github.com/Surrey-UPLab/"
                "Localized-Gaussian-Point-Management"
            ),
            "source_commit": LPM_UPSTREAM_COMMIT,
            "source_file": LPM_UPSTREAM_FILE,
            "source_operator": "get_errormap(error_function='diff')",
            "source_constants": {
                "mean_epsilon": 0.01,
                "error_quantile": LPM_ERROR_QUANTILE,
                "patch_size": LPM_PATCH_SIZE,
                "significant_fraction": LPM_SIGNIFICANT_FRACTION,
            },
            "uses_lightglue": False,
            "uses_triangulation": False,
            "extra_renders": 0,
            "extra_adam_steps": 0,
            "mutation_rows": 0,
            "future_frames_used": False,
            "dataset_name_used": False,
            "calls": len(self.records),
            "utility_scores_consumed": int(self._utility_scores_consumed),
            "pending_scores": len(self._pending_scores),
            "pending_mass_priors": len(self._pending_mass_priors),
            "unique_generation_views": len(self._scores_by_generation_uid),
            "repeat_calls": len(self.records)
            - len(self._scores_by_generation_uid),
            "views_observed_at_least_twice": len(repeated_groups),
            "score_nonzero_calls": nonzero,
            "score_zero_calls": len(scores) - nonzero,
            "score_saturated_calls": saturated,
            "score_unique_values": unique_score_count,
            "score_min": min(scores) if scores else 0.0,
            "score_max": max(scores) if scores else 0.0,
            "score_mean": self._mean(scores),
            "score_population_std": (
                float(statistics.pstdev(scores)) if len(scores) >= 2 else 0.0
            ),
            "same_view_consecutive_abs_delta_mean": self._mean(
                consecutive_same_view_abs_delta
            ),
            "same_view_consecutive_abs_delta_max": (
                max(consecutive_same_view_abs_delta)
                if consecutive_same_view_abs_delta
                else 0.0
            ),
            "cpu_enqueue_seconds": float(self._cpu_enqueue_seconds),
            "gpu_milliseconds": gpu_milliseconds,
            "records": self.records,
        }
