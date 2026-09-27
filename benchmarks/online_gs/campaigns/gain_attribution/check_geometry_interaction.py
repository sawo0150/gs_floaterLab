#!/usr/bin/env python3
"""Exercise actual RGB-D/normal helpers and verify factorial isolation."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import torch
from diagnose_geometry_interaction import native_loss, schedules
from gaussian.utils.slam_utils import get_loss_mapping_rgbd, get_loss_normal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    gt = torch.full((3, 8, 8), .7, device='cuda'); gt[:, 0, 0] = 0
    normal = torch.zeros((3, 8, 8), device='cuda'); normal[2] = -1
    view = SimpleNamespace(original_image_gpu=gt, depth_gpu=torch.ones(1, 8, 8, device='cuda'),
        normal_gpu=normal, image_width=8, image_height=8, FoVx=1., FoVy=1.)
    image = torch.full_like(gt, .4, requires_grad=True)
    depth = torch.full((1, 8, 8), 1.25, device='cuda', requires_grad=True)
    config = {'Training': {'alpha': .95, 'rgb_boundary_threshold': .01}}
    gradients = {}
    for mode in (False, True):
        loss = native_loss([{'render': image, 'depth': depth}], [view], config, .5, mode)
        gradients[mode] = torch.autograd.grad(loss, (image, depth))
    assert torch.equal(gradients[False][0], gradients[True][0])
    assert gradients[False][1].abs().max() == 0
    assert torch.isfinite(gradients[True][1]).all() and gradients[True][1].abs().sum() > 0
    assert gradients[True][0][:, 0, 0].abs().max() == 0
    legacy = get_loss_mapping_rgbd(config, image, depth, view) + .05 * get_loss_normal(depth, view)
    legacy_gradients = torch.autograd.grad(legacy, (image, depth))
    assert all(torch.equal(a, b) for a, b in zip(legacy_gradients, gradients[True]))
    invalid_depth = depth.detach().clone(); invalid_depth[:, 0, 0] = 0; invalid_depth.requires_grad_(True)
    assert not torch.isfinite(get_loss_mapping_rgbd(config, image, invalid_depth, view))
    for mode in (False, True):
        value = native_loss([{'render': image, 'depth': invalid_depth}], [view], config, .5, mode)
        assert torch.isfinite(value)
        grads = torch.autograd.grad(value, (image, invalid_depth))
        assert all(torch.isfinite(g).all() for g in grads)
    a, b = schedules(range(20), range(20)), schedules(range(20), range(40))
    assert a[1] == b[1] and all(len(set(batch)) == 17 for batch in a[1])
    result = {'rgb_image_gradients_identical': True, 'geometry_off_depth_gradient_zero': True,
        'geometry_on_depth_gradient_nonzero_finite': True, 'rgb_mask_preserved': True,
        'native_schedule_identical_across_pools': True,
        'valid_input_gradients_equal_legacy': True, 'invalid_depth_handled_before_reciprocal': True,
        'photo_steps': len(a[0]),
        'native_steps': len(a[1]), 'training_renders_per_arm': len(a[0]) + sum(map(len, a[1]))}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.output / 'checker_source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(result))


if __name__ == '__main__':
    main()
