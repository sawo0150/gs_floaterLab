"""Read-only Adam diagnostics; not a policy, optimizer intervention, or live hook.

The installer is for the single-threaded causal replay diagnostic only. It
chains the existing deadline guard and is removed by that harness on exit.
Sampled coordinates estimate group statistics; they are not full-vector norms.
"""
from collections import Counter
import math
import time
from types import MethodType
import torch


@torch.no_grad()
def sample_optimizer(optimizer, max_coordinates=4096):
    samples = []
    for group in optimizer.param_groups:
        if group.get('weight_decay', 0) or group.get('amsgrad', False) or group.get('maximize', False):
            raise ValueError('Probe assumes ordinary Adam without weight decay/AMSGrad/maximize')
        beta1, beta2 = group['betas']
        for parameter in group['params']:
            if parameter.grad is None or parameter.numel() == 0:
                continue
            stride = max(1, math.ceil(parameter.numel() / max_coordinates))
            select = lambda value: value.reshape(-1)[::stride].detach().clone()
            gradient = select(parameter.grad)
            state = optimizer.state.get(parameter, {})
            old_m = select(state['exp_avg']) if 'exp_avg' in state else torch.zeros_like(gradient)
            old_v = select(state['exp_avg_sq']) if 'exp_avg_sq' in state else torch.zeros_like(gradient)
            step = float(state.get('step', 0)) + 1
            m = beta1 * old_m + (1 - beta1) * gradient
            v = beta2 * old_v + (1 - beta2) * gradient.square()
            denominator = v.sqrt() / math.sqrt(1 - beta2 ** step) + group['eps']
            factor = -float(group['lr']) / (1 - beta1 ** step)
            history_delta = factor * beta1 * old_m / denominator
            current_delta = factor * (1 - beta1) * gradient / denominator
            samples.append({'parameter': parameter, 'stride': stride,
                'before': select(parameter), 'gradient': gradient, 'old_m': old_m,
                'old_v': old_v, 'expected_delta': history_delta + current_delta,
                'history_delta': history_delta, 'current_delta': current_delta,
                'name': group.get('name', 'unnamed'), 'step': step,
                'lr': float(group['lr']), 'parameter_coordinates': parameter.numel()})
    return samples


@torch.no_grad()
def summarize_samples(samples):
    result = []
    for row in samples:
        g, m = row['gradient'], row['old_m']
        actual = row['parameter'].detach().reshape(-1)[::row['stride']] - row['before']
        expected = row['expected_delta']
        product_norm = lambda a, b: (a.norm() * b.norm()).clamp_min(1e-30)
        values = torch.stack([
            g.square().mean().sqrt(), m.square().mean().sqrt(), row['old_v'].mean().sqrt(),
            row['history_delta'].square().mean().sqrt(), row['current_delta'].square().mean().sqrt(),
            (g * m).sum() / product_norm(g, m),
            (g * -expected).sum() / product_norm(g, expected),
            (g * expected).sum(), (actual - expected).abs().max(),
            actual.abs().max(), (g != 0).float().mean()]).cpu().tolist()
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite gradient/moment measurement')
        names = ('gradient_rms', 'previous_first_moment_rms', 'previous_second_moment_sqrt_mean',
                 'history_delta_rms', 'current_delta_rms', 'gradient_old_moment_cosine',
                 'gradient_descent_direction_cosine', 'gradient_dot_parameter_delta',
                 'max_adam_prediction_error', 'max_actual_delta', 'nonzero_gradient_fraction')
        result.append({'name': row['name'], 'adam_step': row['step'], 'lr': row['lr'],
            'sample_coordinates': g.numel(), 'parameter_coordinates': row['parameter_coordinates'],
            **dict(zip(names, values))})
    return result


def install(mapper, guard, heldout, every=32):
    original_loss = mapper._frontier_mapping_view_loss
    original_map = mapper.map
    guarded_adam_step = torch.optim.Adam.step
    native_uids = []
    attempts = Counter()
    report = {'protocol': 'actual_online_adam_observer_v1', 'sample_every_per_source': every,
              'max_coordinates_per_group': 4096, 'source_attempts': attempts,
              'wall_seconds': 0., 'records': [], 'rejected_probes': 0,
              'changes_optimizer_or_policy': False, 'quality_comparison': False}

    def view_loss(self, image, depth, viewpoint, *args, **kwargs):
        native_uids.append(int(viewpoint.uid))
        return original_loss(image, depth, viewpoint, *args, **kwargs)

    def mapping(self, *args, **kwargs):
        native_uids.clear()
        return original_map(*args, **kwargs)

    def step(optimizer, *args, **kwargs):
        if optimizer is not mapper.gaussians.optimizer:
            return guarded_adam_step(optimizer, *args, **kwargs)
        policy = mapper.online_view_trainer.policy
        pending = policy._pending
        if pending is not None:
            uids = list(pending.uids)
            source = 'photo_kf' if all(u in policy.keyframes for u in uids) else 'photo_dense'
        else:
            uids = list(native_uids)
            source = 'native' if uids else 'unclassified'
        native_uids.clear()
        if set(uids) & set(heldout):
            raise ValueError('Held-out observation in optimizer probe')
        attempts[source] += 1
        if source == 'unclassified' or (attempts[source] - 1) % every:
            return guarded_adam_step(optimizer, *args, **kwargs)
        guard.reject_if_unsafe('optimizer')
        started = time.monotonic()
        samples = sample_optimizer(optimizer)
        row = {'source': source, 'source_attempt': attempts[source], 'uids': uids,
            'batch_views': len(uids), 'generation': policy.generation,
            'next_service_step': policy.rgb_steps_completed + 1,
            'gaussians': len(mapper.gaussians._xyz)}
        try:
            value = guarded_adam_step(optimizer, *args, **kwargs)
        except Exception:
            report['rejected_probes'] += 1
            raise
        else:
            row['groups'] = summarize_samples(samples)
            row['completion_seconds'] = time.monotonic()
            report['records'].append(row)
            return value
        finally:
            report['wall_seconds'] += time.monotonic() - started

    mapper._frontier_mapping_view_loss = MethodType(view_loss, mapper)
    mapper.map = MethodType(mapping, mapper)
    torch.optim.Adam.step = step
    return report
