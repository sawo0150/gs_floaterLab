#!/usr/bin/env python3
"""Verify actual Camera GPU targets and bounded uploads before online timing."""
import json
from types import SimpleNamespace
import torch
from gaussian.utils.camera_utils import Camera
from online_photometric import OnlinePhotometricTrainer


def main():
    rgb = (torch.arange(3 * 64 * 64).reshape(3, 64, 64) % 256).to(torch.uint8).float() / 255.
    intrinsic = torch.tensor([48., 48., 32., 32.])
    camera = Camera.init_from_tracking(rgb, None, None, torch.eye(4, device='cuda'),
                                      7, torch.eye(4, device='cuda'), intrinsic)
    trainer = OnlinePhotometricTrainer(SimpleNamespace(), heldout=set(),
        membership='kf_only', selector='rr', seed=0, guard=None, cache_images=2)
    resident = trainer.image(camera)
    assert resident is camera.original_image_gpu
    legacy_target = camera.original_image.cuda()
    assert torch.equal(resident, legacy_target)
    assert len(trainer.images) == 0
    camera.original_image_gpu = None
    uploaded = trainer.image(camera)
    assert torch.equal(uploaded, legacy_target)
    assert trainer.image(camera) is uploaded
    assert len(trainer.images) == 1
    print(json.dumps({'actual_camera_targets_equal': True, 'max_abs_pixel_difference': 0.,
                      'resident_reused': True, 'dense_upload_reused': True,
                      'image_audit': trainer.image_audit, 'quality_claim': False}, indent=2))


if __name__ == '__main__':
    main()
