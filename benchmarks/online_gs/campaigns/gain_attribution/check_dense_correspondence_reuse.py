#!/usr/bin/env python3
"""Numerical warm-solve check: immutable image matches, changed online geometry.

Synthetic pose correctness only; this is not evidence of mapping quality gain.
Run after checking GPU availability, with the isolated backend environment.
"""
import json
from types import SimpleNamespace
import torch
from lietorch import SE3
import geom.projective_ops as pops
from dense_visual_pose_reuse import CorrespondenceRefiner


def view(uid, tx):
    return SimpleNamespace(uid=uid, original_image=torch.zeros(3, 64, 64),
        image_height=64, image_width=64, fx=48., fy=48., cx=32., cy=32.,
        R=torch.eye(3, device='cuda'), T=torch.tensor([tx, 0., 0.], device='cuda'),
        depth=torch.full((64, 64), 2., device='cuda'))


def main():
    left, right, dense = [view(i, t) for i, t in [(0, 0.), (10, -.2), (5, -.1)]]
    views = [left, right, dense]
    pose = torch.tensor([[0., 0., 0., 0., 0., 0., 1.],
                         [-.2, 0., 0., 0., 0., 0., 1.],
                         [-.1, 0., 0., 0., 0., 0., 1.]], device='cuda')
    ii = torch.tensor([0, 1], device='cuda')
    jj = torch.tensor([2, 2], device='cuda')
    intrinsic = torch.tensor([[6., 6., 4., 4.]] * 3, device='cuda')
    disps = torch.full((3, 8, 8), .5, device='cuda')
    target, _ = pops.projective_transform(SE3(pose[None]), disps[None],
                                        intrinsic[None], ii, jj)
    engine = CorrespondenceRefiner.__new__(CorrespondenceRefiner)
    engine.measurements = {5: {'key': engine.measurement_key(views), 'tensors':
        tuple(x.cpu() for x in (target, torch.ones_like(target),
                               torch.full((2, 8, 8), 1e-7, device='cuda'), ii, jj))}}
    records = []
    for scale in [1., 1.5]:
        # Native packets recreate tensors for the same immutable RGB UID.
        # Allocation changes must not disable the warm path.
        for v in views:
            v.original_image = v.original_image.clone()
        # Same images/correspondences under a changed world scale. Using stale
        # depth or anchor pose yields the wrong dense translation in case two.
        right.T[0] = -.2 * scale
        left.depth.fill_(2. * scale)
        right.depth.fill_(2. * scale)
        dense.T[0] = -.17
        before = [(v.R.clone(), v.T.clone(), v.depth.clone()) for v in views[:2]]
        corrected, stats = engine.refine(left, right, dense)
        error = float((corrected[:3, 3] - corrected.new_tensor([-.1 * scale, 0., 0.])).norm())
        assert error < 1e-4, (scale, error, corrected)
        assert stats['correspondences_reused'] and stats['neural_updates'] == 0
        for v, (r, t, d) in zip(views[:2], before):
            assert torch.equal(v.R, r) and torch.equal(v.T, t) and torch.equal(v.depth, d)
        records.append({'world_scale': scale, 'translation_error': error, **stats})
    old_key = engine.measurement_key(views)
    dense.original_image = dense.original_image.clone()
    assert engine.measurement_key(views) == old_key
    dense.uid += 1
    assert engine.measurement_key(views) != old_key
    dense.uid -= 1
    dense.fx += 1
    assert engine.measurement_key(views) != old_key
    print(json.dumps({'synthetic_checks_passed': True, 'quality_claim': False,
                      'records': records}, indent=2))


if __name__ == '__main__':
    main()
