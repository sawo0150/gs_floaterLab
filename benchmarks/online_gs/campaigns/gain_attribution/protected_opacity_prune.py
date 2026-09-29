"""Experiment-only opacity pruning; protect the latest KF birth batches.

Uses stable point IDs, not truncated timestamp-based unique_kfIDs. All
clone/split/stats and unsolicited prune calls remain forbidden.
"""
from collections import deque
from types import MethodType
import time


def old_low_opacity_mask(point_ids, opacity, birth_starts, protect, threshold):
    import torch
    if len(birth_starts) <= protect:
        return torch.zeros_like(opacity, dtype=torch.bool)
    cutoff = birth_starts[-protect]
    return (point_ids.to(opacity.device) < cutoff) & (opacity < threshold)


class ProtectedOpacityPrune:
    def __init__(self, mapper, protect=10, threshold=None, every_renders=300):
        self.mapper = mapper
        self.protect = protect
        self.threshold = float(mapper.gaussian_th if threshold is None else threshold)
        if every_renders <= 0 or int(every_renders) != every_renders:
            raise ValueError('Pruning interval must be a positive integer render count')
        self.period = int(every_renders)
        self.starts = deque(maxlen=protect + 1)
        self.events = []
        self.births = []
        self.reset_prunes = []
        self.forbidden_calls = []
        self.reset_depth = 0
        self.authorized = False
        self.next_render = self.period
        cls = type(mapper.gaussians)
        for name in ('densify_and_prune', 'densify_and_split', 'densify_and_clone',
                     'densify_and_clone_with_budget', 'add_densification_stats'):
            def reject(model, *args, __name=name, **kwargs):
                self.forbidden_calls.append(__name)
                raise RuntimeError('Forbidden topology operator: ' + __name)
            setattr(cls, name, reject)
        original_prune = cls.prune_points

        def prune(model, mask):
            if not (self.reset_depth or self.authorized):
                self.forbidden_calls.append('prune_points')
                raise RuntimeError('Unscheduled prune')
            before = len(model.get_xyz)
            result = original_prune(model, mask)
            if self.reset_depth:
                self.reset_prunes.append({'before': before, 'after': len(model.get_xyz)})
            return result
        cls.prune_points = prune

        for name in ('remove_all_gaussians', 'reset'):
            original = getattr(mapper, name)
            def reset(instance, *args, __original=original, **kwargs):
                self.reset_depth += 1
                try:
                    return __original(*args, **kwargs)
                finally:
                    self.reset_depth -= 1
                    if self.reset_depth == 0:
                        self.starts.clear()
            setattr(mapper, name, MethodType(reset, mapper))

        original_birth = cls.extend_from_pcd
        def birth(model, *args, **kwargs):
            before = len(model.get_xyz)
            value = original_birth(model, *args, **kwargs)
            after = len(model.get_xyz)
            if after > before:
                start = int(model.point_ids[before].item())
                if self.starts and start <= self.starts[-1]:
                    raise RuntimeError('Point IDs are not monotonic within map generation')
                self.starts.append(start)
            self.births.append({'before': before, 'after': after})
            return value
        cls.extend_from_pcd = birth

    def after_packet(self, renders, arrival):
        if renders < self.next_render:
            return
        # One pass at a packet boundary; no extra renders, no terminal cleanup.
        self.next_render = (renders // self.period + 1) * self.period
        import torch
        model = self.mapper.gaussians
        with torch.no_grad():
            opacity = model.get_opacity.detach().reshape(-1)
            mask = old_low_opacity_mask(model.point_ids, opacity, list(self.starts),
                                        self.protect, self.threshold)
            before = len(model.get_xyz)
            removed = int(mask.sum().item())
            cutoff = self.starts[-self.protect] if len(self.starts) > self.protect else None
            protected = torch.ones_like(mask) if cutoff is None else model.point_ids.to(mask.device) >= cutoff
            protected_before = model.point_ids[protected.cpu()].clone()
            assert not bool((mask & protected).any())
            expected_ids = model.point_ids[(~mask).cpu()].clone()
            if removed:
                self.authorized = True
                try:
                    model.prune_points(mask)
                finally:
                    self.authorized = False
            assert torch.equal(expected_ids, model.point_ids)
            after_protected = model.point_ids if cutoff is None else model.point_ids[model.point_ids >= cutoff]
            assert torch.equal(protected_before, after_protected)
            for group in model.optimizer.param_groups:
                if group['name'] in ('xyz', 'f_dc', 'f_rest', 'opacity', 'scaling', 'rotation'):
                    param = group['params'][0]
                    assert param.shape[0] == len(model.point_ids)
                    state = model.optimizer.state.get(param, {})
                    for key in ('exp_avg', 'exp_avg_sq'):
                        if key in state:
                            assert state[key].shape == param.shape
            self.events.append({'arrival_uid': arrival, 'renders': renders,
                                'before': before, 'removed': removed,
                                'after': len(model.get_xyz), 'protected': len(protected_before),
                                'protected_removed': 0, 'cutoff_point_id': cutoff,
                                'birth_starts': list(self.starts), 'alignment_pass': True,
                                'completed_at': time.monotonic()})

    def report(self):
        return {'enabled': True, 'mode': 'protected_opacity_only',
                'threshold': self.threshold, 'period_completed_renders': self.period,
                'protect_recent_birth_batches': self.protect,
                'events': self.events, 'birth_events': self.births,
                'tracker_reset_prunes': self.reset_prunes,
                'forbidden_calls': self.forbidden_calls,
                'pass': not self.forbidden_calls and not self.reset_depth and not self.authorized}
