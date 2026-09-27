#!/usr/bin/env python3
"""Compare 6x2 versus 1x12 fixed-correspondence BA iterations on CUDA.

Numerical/cost diagnostic only; run when the GPU is free. No mapping or
held-out quality claim follows from this synthetic check.
"""
import json
import time
import torch
from lietorch import SE3
import geom.projective_ops as pops
from dense_visual_pose import PairVideo


def fixture(scale, height=48, width=64):
    tangent = torch.zeros(3, 6, device='cuda')
    tangent[1, 0], tangent[2, 0] = -.2 * scale, -.1 * scale
    tangent[2, 4] = .015
    truth = SE3.exp(tangent)
    noise = torch.zeros_like(tangent)
    noise[2, :3] = torch.tensor([.07, -.03, .02], device='cuda') * scale
    noise[2, 3:] = torch.tensor([.01, -.02, .01], device='cuda')
    initial = (SE3.exp(noise) * truth).data
    y, x = torch.meshgrid(torch.arange(height, device='cuda'),
                          torch.arange(width, device='cuda'), indexing='ij')
    depth = (2. + .1 * torch.sin(x.float()/10) + .1 * torch.cos(y.float()/10)) * scale
    disps = depth.reciprocal()[None].repeat(3, 1, 1)
    intrinsic = torch.tensor([[52.5, 52.5, width/2, height/2]] * 3, device='cuda')
    ii = torch.tensor([0, 1], device='cuda')
    jj = torch.tensor([2, 2], device='cuda')
    target, _ = pops.projective_transform(truth[None], disps[None], intrinsic[None], ii, jj)
    weight = torch.full_like(target, .8)
    damping = torch.full((2, height, width), 1e-7, device='cuda')
    return initial, disps, intrinsic, (target, weight, damping, ii, jj), truth.data


def solve(data, chunks):
    initial, disps, intrinsic, args, _ = data
    video = PairVideo()
    video.poses, video.disps = initial.clone(), disps.clone()
    video.intrinsics = intrinsic
    video.disable_mono = True
    for iterations in chunks:
        video.cuda_ba(*args, 2, 3, itrs=iterations, lm=1e-5, ep=.01, motion_only=True)
    if not torch.equal(video.poses[:2], initial[:2]) or not torch.equal(video.disps, disps):
        raise RuntimeError('BA changed fixed anchors or depths')
    return video.poses


@torch.no_grad()
def main():
    rows = []
    for scale in (0.5, 1., 1.5, 3.):
        data = fixture(scale)
        separate = solve(data, [2] * 6)
        combined = solve(data, [12])
        error = float((separate - combined).abs().max())
        if not torch.isfinite(combined).all() or error > 1e-6:
            raise RuntimeError(f'Batching changed the pose: scale={scale}, error={error}')
        initial_error = float((data[0][2] - data[4][2]).abs().max())
        final_error = float((combined[2] - data[4][2]).abs().max())
        if final_error >= initial_error:
            raise RuntimeError('Equivalent calls did not improve the synthetic pose')
        row = {'scale': scale, 'max_abs_pose_difference': error,
               'initial_truth_error': initial_error, 'final_truth_error': final_error}
        for name, chunks in [('six_calls', [2] * 6), ('one_call', [12])]:
            for _ in range(5):
                solve(data, chunks)
            torch.cuda.synchronize()
            start = time.perf_counter()
            for _ in range(50):
                solve(data, chunks)
            torch.cuda.synchronize()
            row[name + '_seconds_per_pose'] = (time.perf_counter() - start)/50
        rows.append(row)
    print(json.dumps({'equivalence_passed': True, 'mapping_quality_claim': False,
                      'rows': rows}, indent=2))


if __name__ == '__main__':
    main()
