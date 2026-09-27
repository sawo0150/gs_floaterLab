#!/usr/bin/env python3
"""Capture actual encoder inputs without fitting poses or using evaluation data."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import torch
from dense_visual_pose import VisualRefiner


class Captured(Exception):
    pass


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    official = Path('/home/intern/VIGS-SLAM-official-exp78/vigs')
    motion = module('official_motion_preprocessing_check', official / 'motion_filter.py')
    filler_module = module('official_filler_preprocessing_check', official / 'util/trajectory_filler.py')
    captures = {}
    def encoder(name):
        def capture(value):
            captures[name] = value.detach().float().cpu().clone()
            raise Captured(name)
        return capture
    rgb = torch.tensor([255., 64., 8.]).reshape(1, 3, 1, 1).expand(1, 3, 64, 64).contiguous()
    mean = torch.tensor([.485, .456, .406], device='cuda')[:, None, None]
    std = torch.tensor([.229, .224, .225], device='cuda')[:, None, None]
    tracker = motion.MotionFilter.__new__(motion.MotionFilter)
    tracker.device, tracker.MEAN, tracker.STDV = 'cuda:0', mean, std
    tracker.mono_model = 'omnidata'
    tracker.feature_encoder = encoder('tracker')
    try:
        tracker.track(1, 1., rgb, intrinsics=torch.tensor([[48., 48., 32., 32.]]))
    except Captured:
        pass
    filler = filler_module.PoseTrajectoryFiller.__new__(filler_module.PoseTrajectoryFiller)
    filler.device, filler.MEAN, filler.STDV = 'cuda:0', mean, std
    filler.fnet = encoder('filler')
    filler.feature_encoder_trt = None
    filler.video = SimpleNamespace(counter=SimpleNamespace(value=2),
        tstamp=torch.tensor([0., 2.], device='cuda'),
        poses=torch.tensor([[0., 0., 0., 0., 0., 0., 1.]] * 2, device='cuda'))
    try:
        filler.fill([1], [rgb])
    except Captured:
        pass
    refiner = VisualRefiner.__new__(VisualRefiner)
    refiner.cache = {}
    refiner.net = SimpleNamespace(fnet=encoder('current_refiner'))
    try:
        refiner.features(SimpleNamespace(uid=1, original_image=rgb[0] / 255.))
    except Captured:
        pass
    assert set(captures) == {'tracker', 'filler', 'current_refiner'}
    assert torch.equal(captures['filler'], captures['current_refiner'])
    assert not torch.equal(captures['tracker'], captures['filler'])
    normalized = (rgb[0] / 255. - mean.cpu()) / std.cpu()
    reversed_normalized = (rgb[0, [2, 1, 0]] / 255. - mean.cpu()) / std.cpu()
    assert torch.equal(captures['filler'][0, 0], normalized)
    assert torch.equal(captures['tracker'][0, 0], reversed_normalized)
    print(json.dumps({'actual_methods_exercised': True,
        'normalized_rgb_pixel': captures['filler'][0, 0, :, 0, 0].tolist(),
        'normalized_tracker_pixel': captures['tracker'][0, 0, :, 0, 0].tolist(),
        'tracker_filler_max_abs_difference': float((captures['tracker'] - captures['filler']).abs().max()),
        'filler_current_refiner_max_abs_difference': 0.,
        'pose_estimation_performed': False, 'heldout_or_eval_poses_used': False,
        'mapping_or_evaluator_modified': False, 'quality_claim': False}, indent=2))


if __name__ == '__main__':
    main()
