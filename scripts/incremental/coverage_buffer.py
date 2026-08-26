"""SparseCoverageBuffer -- a portable, renderer-agnostic novelty-scoring buffer for
picking which camera view to train next during incremental 3D Gaussian Splatting.

Single-file, dependency-free beyond torch: designed to be copied as-is into any
training loop (3dgs-custom's train_incremental.py, VIGS-SLAM's gs_backend.py, ...)
without pulling in the rest of this repo. Do not import project-specific modules
here -- if this file needs something else, that something belongs in the caller.

Design (exp66 "COVER 이식 설계 노트", VIGS-SLAM 뷰 스케줄링):
  - Coverage is tracked per SPATIAL CELL (a sparse hash grid), not per Gaussian.
    Gaussian identity churns constantly (densify/split/prune); cells don't, so the
    buffer never needs a destructive rebuild the way a per-Gaussian histogram would.
  - Only cells that actually contain >=1 Gaussian get a row (sparse, on-demand
    allocation) -- there is no dense pre-allocated grid, and none is possible: an
    online SLAM map has no known bounding box in advance.
  - Cell membership is NEVER cached. Every call re-quantizes from current Gaussian
    positions. Gaussians move under gradient steps between visits to the same cell;
    caching would silently go stale.
  - Storage per (cell, direction-bin) is a single bit ("has been observed from
    roughly this direction, yes/no"), not a count -- matches how the upstream COVER
    formula actually consumes it (`coverage_counts == 0`), and halves memory.
  - Gaussian-count-per-cell is used ONLY at score() time, as an importance weight
    (a cell with more Gaussians = more surface detail = a novel view of it matters
    more). It is not entangled with update()'s bookkeeping; refresh it explicitly
    (refresh_gaussian_counts) whenever the Gaussian population actually changes --
    i.e. right after densify_and_prune, not on some unrelated timer.
  - Visibility (which Gaussians a view can see) and occlusion are the CALLER's
    job. This module only ever receives pre-filtered Gaussian positions ("the
    Gaussians visible from this camera") -- it never renders or frustum-culls
    anything itself, so it works the same whether the host uses gsplat, the stock
    diff-gaussian-rasterizer, or a hand-rolled frustum test.
"""
from __future__ import annotations

import torch

CELL_SIZE_DEFAULT = 0.10  # meters; matches an existing precedent in this codebase
                           # family (carve_prune.py's occupancy voxel size)
N_BINS_DEFAULT = 64       # direction bins on the unit sphere; matches upstream
                           # COVER's own default and our earlier smoke-test
_AXIS_BITS = 20            # 20 bits/axis -> +-2**19 cells/axis before overflow;
                            # at 0.10m cells that is +-52km/axis, effectively
                            # unbounded for any real indoor SLAM scene
_AXIS_OFFSET = 1 << (_AXIS_BITS - 1)
_AXIS_BASE = 1 << _AXIS_BITS


def fibonacci_sphere(n: int, device=None, dtype=torch.float32) -> torch.Tensor:
    """n roughly-evenly-spaced unit vectors on the sphere. Same construction as
    upstream COVER's `nbv_gym/util/coverage.py:fibonacci_sphere`."""
    i = torch.arange(n, device=device, dtype=dtype)
    phi = (1.0 + 5.0 ** 0.5) / 2.0
    theta = 2.0 * torch.pi * i / phi
    z = 1.0 - (2.0 * i + 1.0) / n
    r = torch.sqrt(torch.clamp(1.0 - z * z, min=0.0))
    x = r * torch.cos(theta)
    y = r * torch.sin(theta)
    return torch.stack([x, y, z], dim=-1)  # [n, 3], already unit norm


class SparseCoverageBuffer:
    """Sparse per-cell x per-direction-bin observation ledger.

    Typical lifecycle in a host training loop:
        buf = SparseCoverageBuffer(device=means.device)
        ...
        # after a view V actually gets trained this step:
        buf.update(visible_gaussian_positions_of_V, camera_position_of_V)
        ...
        # right after densify_and_prune changes the Gaussian population:
        buf.refresh_gaussian_counts(all_current_gaussian_positions)
        ...
        # when picking the next view from a candidate pool:
        weights = buf.score([(vis_pos_c0, cam_pos_c0), (vis_pos_c1, cam_pos_c1), ...])
        next_view = random.choices(pool, weights=weights, k=1)[0]
    """

    def __init__(
        self,
        cell_size: float = CELL_SIZE_DEFAULT,
        n_bins: int = N_BINS_DEFAULT,
        device=None,
        dtype=torch.float32,
    ):
        self.cell_size = float(cell_size)
        self.n_bins = int(n_bins)
        self.device = device
        self.dtype = dtype
        self.bin_dirs = fibonacci_sphere(self.n_bins, device=device, dtype=dtype)  # [G,3]

        # Sparse registry: sorted 1D int64 keys, one row per occupied cell.
        self._keys = torch.empty(0, dtype=torch.int64, device=device)
        self.coverage = torch.zeros(0, self.n_bins, dtype=torch.bool, device=device)
        self.cell_gaussian_count = torch.zeros(0, dtype=torch.int64, device=device)
        self._warned_outlier = False

    # ---- cell bookkeeping -------------------------------------------------

    def _quantize(self, positions: torch.Tensor) -> torch.Tensor:
        """positions [N,3] (float, world frame) -> integer cell coords [N,3].
        Always computed live -- never cache the output of this function across
        calls, since Gaussian positions move under optimization."""
        return torch.floor(positions / self.cell_size).to(torch.int64)

    def _in_range_mask(self, positions: torch.Tensor) -> torch.Tensor:
        """positions [N,3] -> bool mask [N], True where the position's cell
        coordinate packs safely into an int64 key. Real SLAM point clouds
        routinely contain wild triangulation outliers (points thousands of
        meters from a scene whose real extent is a few meters) -- this buffer
        is a diagnostic/scoring aid, not the main training path, so it must
        never be able to crash the caller over a handful of bad points. Outliers
        are silently dropped from THIS buffer's bookkeeping; they still get
        trained normally by the host loop, which is unaffected either way."""
        cells = self._quantize(positions)
        c = cells + _AXIS_OFFSET
        in_range = ((c >= 0) & (c < _AXIS_BASE)).all(dim=-1)
        if not bool(in_range.all()) and not self._warned_outlier:
            n_dropped = int((~in_range).sum())
            print(
                f"[coverage_buffer] dropping {n_dropped}/{positions.shape[0]} "
                f"position(s) outside +-{_AXIS_OFFSET * self.cell_size:.0f}m "
                "(SLAM outlier points, not a bug in the host training loop) "
                "-- this warning prints once.",
                flush=True,
            )
            self._warned_outlier = True
        return in_range

    def _pack(self, cell_coords: torch.Tensor) -> torch.Tensor:
        """[N,3] int cell coords -> [N] int64 keys. Caller must have already
        filtered with _in_range_mask -- this does not re-check."""
        c = cell_coords + _AXIS_OFFSET
        return (c[..., 0] * _AXIS_BASE + c[..., 1]) * _AXIS_BASE + c[..., 2]

    def _cell_centers(self, cell_coords: torch.Tensor) -> torch.Tensor:
        """Cell-center world position for given integer cell coords -- the fixed,
        zero-extra-cost reference point used for all direction-vector math
        (decision: cell-center over per-cell Gaussian centroid)."""
        return (cell_coords.to(self.dtype) + 0.5) * self.cell_size

    def _rows_for_keys(self, keys: torch.Tensor, create: bool) -> torch.Tensor:
        """Map each key in `keys` [N] to a row index into self.coverage /
        self.cell_gaussian_count. If create=True, unseen keys get new rows
        appended (sparse, on-demand allocation -- no dense pre-allocated grid).
        If create=False, unseen keys map to -1 (caller must handle/skip)."""
        if create:
            self._ensure_registered(keys)
        if self._keys.numel() == 0:
            return torch.full_like(keys, -1)
        pos = torch.searchsorted(self._keys, keys)
        pos_clamped = pos.clamp(max=self._keys.numel() - 1)
        found = self._keys[pos_clamped] == keys
        return torch.where(found, pos_clamped, torch.full_like(pos_clamped, -1))

    def _ensure_registered(self, keys: torch.Tensor):
        """Grow self._keys / self.coverage / self.cell_gaussian_count to include
        every not-yet-seen key in `keys`, keeping all three arrays in the same
        sorted-by-key order."""
        candidates = torch.unique(keys)
        if self._keys.numel() == 0:
            new_keys = candidates
        else:
            pos = torch.searchsorted(self._keys, candidates)
            pos_c = pos.clamp(max=self._keys.numel() - 1)
            already_present = self._keys[pos_c] == candidates
            new_keys = candidates[~already_present]
        if new_keys.numel() == 0:
            return

        old_coverage = self.coverage
        old_counts = self.cell_gaussian_count
        merged_keys = torch.cat([self._keys, new_keys])
        self._keys, sort_idx = torch.sort(merged_keys)

        extended_coverage = torch.cat(
            [old_coverage, torch.zeros(new_keys.numel(), self.n_bins, dtype=torch.bool, device=self.device)]
        )
        extended_counts = torch.cat(
            [old_counts, torch.zeros(new_keys.numel(), dtype=torch.int64, device=self.device)]
        )
        self.coverage = extended_coverage[sort_idx]
        self.cell_gaussian_count = extended_counts[sort_idx]

    # ---- public API ---------------------------------------------------------

    @staticmethod
    def _check_positions(positions: torch.Tensor, name: str):
        """Every host codebase's own render_pkg has its own convention for
        "which Gaussians are visible" -- some are a plain bool mask, some (e.g.
        this codebase family's `(radii > 0).nonzero()`) are an INDEX tensor,
        which silently produces an extra dim when used to index a [N,3] position
        tensor (`positions[idx]` -> [Nv,1,3], not [Nv,3]). Caught exactly this
        the first time this module was wired into a real host loop -- fail loud
        and specific here instead of a confusing shape error three calls later."""
        if positions.dim() != 2 or positions.shape[-1] != 3:
            raise ValueError(
                f"{name} must be [N,3], got {tuple(positions.shape)} -- if this "
                "came from indexing Gaussian positions with a visibility mask, "
                "check whether that mask is a bool [N] tensor or an index tensor "
                "from `.nonzero()` (shape [Nv,1]); the latter needs `.squeeze(-1)` "
                "before use here."
            )

    def update(self, visible_gaussian_positions: torch.Tensor, camera_position: torch.Tensor):
        """Record that `visible_gaussian_positions` [Ni,3] were just observed from
        a camera at `camera_position` [3]. Call this once per view actually
        trained this step, right after (or alongside) the optimizer step for it.
        """
        if visible_gaussian_positions.numel() == 0:
            return
        self._check_positions(visible_gaussian_positions, "visible_gaussian_positions")
        in_range = self._in_range_mask(visible_gaussian_positions)
        visible_gaussian_positions = visible_gaussian_positions[in_range]
        if visible_gaussian_positions.numel() == 0:
            return
        cells = self._quantize(visible_gaussian_positions)
        keys = self._pack(cells)
        rows = self._rows_for_keys(keys, create=True)

        centers = self._cell_centers(cells)
        dirs = centers - camera_position[None, :]
        dirs = dirs / dirs.norm(dim=-1, keepdim=True).clamp_min(1e-8)
        bin_idx = torch.argmax(dirs @ self.bin_dirs.T, dim=-1)  # [Ni]

        # dedupe (row, bin) pairs touched more than once in this call before the
        # in-place bool set -- not strictly necessary for correctness (setting
        # True twice is a no-op) but keeps the intent explicit.
        self.coverage[rows, bin_idx] = True

    def refresh_gaussian_counts(self, all_gaussian_positions: torch.Tensor):
        """Recompute how many Gaussians currently live in each already-registered
        cell. Call this right after densify_and_prune actually changes the
        Gaussian population -- that is the only thing this number depends on, so
        there is no reason to refresh it on any other schedule (e.g. a fixed
        step-count timer would be either stale or wasteful for no benefit)."""
        if all_gaussian_positions.numel() > 0:
            self._check_positions(all_gaussian_positions, "all_gaussian_positions")
        if self._keys.numel() == 0 or all_gaussian_positions.numel() == 0:
            self.cell_gaussian_count.zero_()
            return
        in_range = self._in_range_mask(all_gaussian_positions)
        all_gaussian_positions = all_gaussian_positions[in_range]
        if all_gaussian_positions.numel() == 0:
            self.cell_gaussian_count.zero_()
            return
        cells = self._quantize(all_gaussian_positions)
        keys = self._pack(cells)
        rows = self._rows_for_keys(keys, create=False)  # do NOT grow the table here
        valid = rows >= 0
        counts = torch.zeros(self._keys.numel(), dtype=torch.int64, device=self.device)
        if valid.any():
            counts.scatter_add_(0, rows[valid], torch.ones(valid.sum(), dtype=torch.int64, device=self.device))
        self.cell_gaussian_count = counts

    def score(
        self,
        candidates: list[tuple[torch.Tensor, torch.Tensor]],
        floor: float = 0.1,
        ceiling: float = 1.0,
    ) -> list[float]:
        """Rank-normalized novelty weight per candidate, for direct use as
        `random.choices(..., weights=...)`.

        candidates: list of (visible_gaussian_positions [Ni,3], camera_position [3])
            -- visibility/occlusion filtering is the caller's job (decision:
            frustum-only, no occlusion test, done upstream).
        floor/ceiling: the fixed weight range candidates are linearly mapped into
            by rank, most-novel -> ceiling, most-redundant -> floor. Rank
            normalization (rather than using the raw redundancy score directly)
            guarantees this spread regardless of how bunched the raw scores are.

        Returns len(candidates) floats, most-novel-candidate gets the highest
        weight. If the buffer is empty (nothing observed yet -- e.g. before the
        very first update()), every candidate scores equally (weight 1.0); the
        caller's cold-start fallback (flat class weight) should dominate in that
        regime regardless.
        """
        if self._keys.numel() == 0 or len(candidates) == 0:
            return [1.0] * len(candidates)
        n = len(candidates)

        # Fully vectorized across candidates: one batched Gaussian-lookup instead
        # of a per-candidate Python loop. Measured cost of the naive per-candidate
        # loop was ~0.56ms/candidate purely from GPU kernel-launch overhead (flat
        # across 3.6K-900K Gaussians -- launch-bound, not compute-bound), i.e.
        # ~112ms for a 200-candidate pool, comparable to or larger than a whole
        # training step. This version issues a handful of kernel launches total,
        # regardless of pool size.
        all_pos, all_cam, cand_id = [], [], []
        for i, (vis_pos, cam_pos) in enumerate(candidates):
            if vis_pos.numel() == 0:
                continue
            self._check_positions(vis_pos, f"candidates[{i}][0] (visible_gaussian_positions)")
            all_pos.append(vis_pos)
            all_cam.append(cam_pos.expand(vis_pos.shape[0], 3))
            cand_id.append(torch.full((vis_pos.shape[0],), i, dtype=torch.int64, device=self.device))

        redundancy = torch.zeros(n, dtype=self.dtype, device=self.device)
        total_weight = torch.zeros(n, dtype=self.dtype, device=self.device)

        if all_pos:
            all_pos = torch.cat(all_pos)
            all_cam = torch.cat(all_cam)
            cand_id = torch.cat(cand_id)

            in_range = self._in_range_mask(all_pos)
            all_pos, all_cam, cand_id = all_pos[in_range], all_cam[in_range], cand_id[in_range]

            if all_pos.numel() > 0:
                cells = self._quantize(all_pos)
                keys = self._pack(cells)
                rows = self._rows_for_keys(keys, create=False)
                valid = rows >= 0
                rows_v, cells_v, cam_v, cand_v = rows[valid], cells[valid], all_cam[valid], cand_id[valid]

                if rows_v.numel() > 0:
                    # Chunked, not one giant [M,G] tensor: M = sum of visible-Gaussian
                    # counts across the WHOLE candidate pool, which has no fixed
                    # upper bound (pool size x per-view visible count both vary with
                    # the host scene). A pool of ~1000 candidates against a Gaussian
                    # count that's grown via active densification produced a >7M-row
                    # batch here and OOM'd on a 16GB GPU in one shot -- chunk it to
                    # bound peak memory regardless of pool/scene scale.
                    chunk = 500_000
                    for start in range(0, rows_v.numel(), chunk):
                        end = start + chunk
                        rows_c = rows_v[start:end]
                        centers = self._cell_centers(cells_v[start:end])
                        dirs = centers - cam_v[start:end]
                        dirs = dirs / dirs.norm(dim=-1, keepdim=True).clamp_min(1e-8)
                        cos_sim = dirs @ self.bin_dirs.T  # [chunk, G]
                        observed = self.coverage[rows_c]  # [chunk, G] bool
                        masked = torch.where(observed, (cos_sim + 1.0) / 2.0, torch.zeros_like(cos_sim))
                        per_gaussian_redundancy = masked.max(dim=-1).values  # [chunk]
                        weights = self.cell_gaussian_count[rows_c].clamp(min=1).to(self.dtype)  # [chunk]

                        redundancy.scatter_add_(0, cand_v[start:end], per_gaussian_redundancy * weights)
                        total_weight.scatter_add_(0, cand_v[start:end], weights)

        has_weight = total_weight > 0
        redundancy = torch.where(has_weight, redundancy / total_weight.clamp_min(1e-8), torch.zeros_like(redundancy))
        # candidates with no visible Gaussians, or none in an already-registered
        # cell, fall through to redundancy=0 (maximally novel) -- same contract
        # as before.

        order = torch.argsort(redundancy)  # ascending: index 0 = least redundant = most novel
        rank_weight = torch.empty(n, dtype=self.dtype, device=self.device)
        if n == 1:
            rank_weight[:] = ceiling
        else:
            span = torch.linspace(ceiling, floor, n, device=self.device, dtype=self.dtype)
            rank_weight[order] = span
        return rank_weight.tolist()

    def __len__(self):
        return int(self._keys.numel())
