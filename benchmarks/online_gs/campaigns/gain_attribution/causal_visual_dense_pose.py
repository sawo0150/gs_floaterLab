"""Causal two-anchor DROID motion-only refinement, isolated from Gaussian Adam."""
from contextlib import nullcontext
from pathlib import Path
from types import MethodType
import time

import torch
from lietorch import SE3
import geom.projective_ops as pops
from factor_graph import FactorGraph
from depth_video import DepthVideo
from modules.droid_net import DroidNet
from util.poses import to_se3_vec

from dense_pose_refresh_repair import bracket


class PairVideo:
    """Minimal native BA buffer: fixed anchors 0/1, variable dense camera 2."""
    cuda_ba = DepthVideo.cuda_ba

    def get_lock(self):
        return nullcontext()

    def reproject(self, ii, jj):
        return pops.projective_transform(SE3(self.poses[None]), self.disps[None],
                                         self.intrinsics[None], ii, jj)

    def upsample(self, ix, mask):
        # Motion-only solve: upsampled disparity is not consumed or changed.
        pass


def matrix(view):
    value = torch.eye(4, device=view.R.device, dtype=view.R.dtype)
    value[:3, :3], value[:3, 3] = view.R, view.T
    return value


class VisualRefiner:
    def __init__(self, weights):
        started = time.perf_counter()
        # Loading the model must not change mapper/selector random streams.
        with torch.random.fork_rng(devices=[0]):
            self.net = DroidNet()
            state = {k.replace('module.', ''): v for k, v in
                     torch.load(weights, map_location='cpu', weights_only=False).items()}
            for name in ('weight', 'delta'):
                for suffix in ('weight', 'bias'):
                    key = f'update.{name}.2.{suffix}'
                    state[key] = state[key][:2]
            self.net.load_state_dict(state)
            self.net = self.net.cuda().eval()
        for parameter in self.net.parameters():
            parameter.requires_grad_(False)
        torch.cuda.synchronize()
        self.load_seconds = time.perf_counter() - started
        self.cache = {}

    @torch.no_grad()
    def features(self, view):
        uid = int(view.uid)
        if uid not in self.cache:
            image = view.original_image.cuda().float()[None, None]
            mean = image.new_tensor([.485, .456, .406])[None, None, :, None, None]
            std = image.new_tensor([.229, .224, .225])[None, None, :, None, None]
            image = (image - mean) / std
            with torch.amp.autocast('cuda', enabled=True):
                fmap = self.net.fnet(image)[0]
                net, inp = self.net.cnet(image).split([128, 128], dim=2)
            self.cache[uid] = (fmap.half().cpu(), net[0, 0].tanh().half().cpu(),
                               inp[0, 0].relu().half().cpu())
        return tuple(x.cuda() for x in self.cache[uid])

    @torch.no_grad()
    def refine(self, left, right, dense):
        views = [left, right, dense]
        v = PairVideo()
        v.ht, v.wd = dense.image_height, dense.image_width
        if v.ht % 8 or v.wd % 8:
            raise ValueError('Expected native DROID dimensions divisible by eight')
        pose_matrices = torch.stack([matrix(x) for x in views])
        v.poses = torch.tensor([to_se3_vec(x.cpu().numpy()) for x in pose_matrices],
                               device='cuda', dtype=torch.float32)
        v.disps = torch.ones((3, v.ht//8, v.wd//8), device='cuda')
        for i, view in enumerate(views[:2]):
            depth = torch.as_tensor(view.depth, device='cuda', dtype=torch.float32)
            depth = depth.reshape(v.ht, v.wd)[3::8, 3::8]
            v.disps[i] = torch.where(depth > .01, depth.reciprocal(), 0.001).clamp(min=.001)
        v.intrinsics = torch.tensor([[x.fx, x.fy, x.cx, x.cy] for x in views],
                                    device='cuda', dtype=torch.float32) / 8
        f = [self.features(x) for x in views]
        v.fmaps = torch.stack([x[0] for x in f])
        v.nets = torch.stack([x[1] for x in f])
        v.inps = torch.stack([x[2] for x in f])
        v.disable_mono = True
        before_anchors, before_depth = v.poses[:2].clone(), v.disps.clone()
        graph = FactorGraph(v, self.net.update)
        graph.add_factors([0, 1], [2, 2])
        for _ in range(6):
            graph.update(2, 3, motion_only=True)
        if not torch.equal(v.poses[:2], before_anchors) or not torch.equal(v.disps, before_depth):
            raise RuntimeError('Motion-only refinement mutated anchor pose or depth')
        result = SE3(v.poses[2:3]).matrix()[0]
        if not torch.isfinite(result).all():
            raise RuntimeError('Nonfinite visual pose')
        delta = SE3(v.poses[2:3]) * SE3(torch.tensor(
            to_se3_vec(pose_matrices[2].cpu().numpy()), device='cuda',
            dtype=torch.float32)[None]).inv()
        return result, {'rotation_change_rad': float(delta.log()[0, 3:].norm()),
                        'translation_change': float((result[:3, 3]-pose_matrices[2, :3, 3]).norm()),
                        'anchor_pose_unchanged': True, 'depth_unchanged': True}


def install(mapper, weights, heldout):
    engine = VisualRefiner(weights)
    original = mapper._training_viewpoint
    latest = {}
    audit = {'protocol': 'causal_two_anchor_visual_pose_v1', 'calls': [],
             'unbracketed_skips': 0, 'cache_hits': 0, 'wall_seconds': 0.,
             'network_load_seconds': engine.load_seconds, 'heldout_overlap': 0}
    mapper._visual_pose_audit = audit
    mapper._visual_pose_latest = latest

    def training(self, view):
        if getattr(view, 'sensor_type', None) != 'rgb_dense':
            return original(view)
        uid = int(view.uid)
        keys = sorted(int(k) for k in self.viewpoints)
        pair = bracket(keys, uid)
        if pair is None:
            audit['unbracketed_skips'] += 1
            return original(view)
        if {uid, *pair} & heldout:
            raise RuntimeError('Held-out RGB supplied to pose refinement')
        left, right = [self.viewpoints[k] for k in pair]
        # All three cameras already exist in the causal mapper. Latest KF is
        # an observed upper bound; no archive lookahead or eval trajectory read.
        if not pair[0] < uid < pair[1] <= max(keys):
            raise RuntimeError('Noncausal pose bracket')
        endpoints = torch.stack([matrix(left), matrix(right)]).cpu()
        current = matrix(view).cpu()
        previous = latest.get(uid)
        if (previous is not None and previous['camera_id'] == id(view)
                and previous['pair'] == pair
                and torch.equal(previous['endpoints'], endpoints)
                and torch.equal(previous['pose'], current)):
            audit['cache_hits'] += 1
            return original(view)
        torch.cuda.synchronize(); started = time.perf_counter()
        corrected, stats = engine.refine(left, right, view)
        view.update_RT(corrected[:3, :3], corrected[:3, 3])
        # Avoid rendering with an old scaled-camera cache after changing pose.
        self._scaled_viewpoint_cache.clear()
        self._training_viewpoint_cache.clear()
        torch.cuda.synchronize(); elapsed = time.perf_counter() - started
        audit['wall_seconds'] += elapsed
        audit['calls'].append({'uid': uid, 'left': pair[0], 'right': pair[1],
                              'latest_mapper_kf': max(keys), 'updates': 6,
                              'wall_seconds': elapsed, **stats})
        latest[uid] = {'pose': corrected.cpu().clone(), 'pair': pair,
                       'endpoints': endpoints, 'camera_id': id(view)}
        return original(view)
    mapper._training_viewpoint = MethodType(training, mapper)
