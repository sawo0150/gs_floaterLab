"""Fail closed if the no-densify/prune ablation reaches a forbidden operator.

Tracker-requested whole-map reset remains allowed and is recorded separately.
Class wrappers cover models replaced after an IMU initialization/reset.
"""
from types import MethodType


class NoDensifyPruneAudit:
    def __init__(self, mapper):
        self.mapper = mapper
        self.reset_depth = 0
        self.forbidden_calls = []
        self.reset_prunes = []
        self.births = []
        model_class = type(mapper.gaussians)
        for name in ('densify_and_prune', 'densify_and_split',
                     'densify_and_clone', 'densify_and_clone_with_budget',
                     'add_densification_stats'):
            def reject(model, *args, __name=name, **kwargs):
                self.forbidden_calls.append(__name)
                raise RuntimeError('Disabled topology operator called: ' + __name)
            setattr(model_class, name, reject)
        original_prune = model_class.prune_points

        def prune(model, mask):
            if not self.reset_depth:
                self.forbidden_calls.append('prune_points')
                raise RuntimeError('Pruning outside a tracker-requested map reset')
            before = len(model.get_xyz)
            value = original_prune(model, mask)
            self.reset_prunes.append({'before': before, 'after': len(model.get_xyz)})
            return value
        model_class.prune_points = prune
        for reset_name in ('remove_all_gaussians', 'reset'):
            original_reset = getattr(mapper, reset_name)

            def reset(instance, *args, __original=original_reset, **kwargs):
                self.reset_depth += 1
                try:
                    return __original(*args, **kwargs)
                finally:
                    self.reset_depth -= 1
            setattr(mapper, reset_name, MethodType(reset, mapper))
        original_birth = model_class.extend_from_pcd

        def birth(model, *args, **kwargs):
            before = len(model.get_xyz)
            result = original_birth(model, *args, **kwargs)
            self.births.append({'before': before, 'after': len(model.get_xyz)})
            return result
        model_class.extend_from_pcd = birth

    def report(self):
        m = self.mapper
        return {'enabled': True, 'forbidden_calls': self.forbidden_calls,
                'tracker_reset_prunes': self.reset_prunes,
                'birth_calls': len(self.births),
                'birth_gaussians': sum(r['after']-r['before'] for r in self.births),
                'birth_events': self.births,
                'observation_topology_gate': m._mapping_observation_topology_gate,
                'model_scheduler': m._mapping_model_scheduler,
                'opacity_reset_policy': 'unchanged',
                'pass': bool(m._mapping_disable_densify_prune
                             and not m._mapping_observation_topology_gate
                             and not m._mapping_model_scheduler
                             and not self.forbidden_calls
                             and self.reset_depth == 0 and self.births)}
