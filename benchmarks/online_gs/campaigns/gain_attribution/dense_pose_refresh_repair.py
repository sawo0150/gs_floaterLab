"""Causal, idempotent IMU residual refresh when mapper brackets change."""
from bisect import bisect_left
from collections import defaultdict
from types import MethodType

import numpy as np
import torch

from exp78b_dense_imu_pose import integrate_gyro_queries_strict_causal, _slerp_identity


def bracket(keys, uid):
    i = bisect_left(keys, uid)
    if i == 0 or i == len(keys) or keys[i] == uid:
        return None
    return keys[i-1], keys[i]


def residuals(shaper, left, right, uids):
    start, end = shaper.timestamps[left], shaper.timestamps[right]
    queries = [shaper.timestamps[uid] for uid in uids]
    if any(not start < q < end for q in queries):
        raise ValueError('Dense time must be inside its current causal bracket')
    curve = integrate_gyro_queries_strict_causal(shaper.imu, start, end, queries)
    result = {}
    for uid, query in zip(uids, queries):
        beta = (query-start)/(end-start)
        curvature = _slerp_identity(curve[end], beta).T @ curve[query]
        result[uid] = (shaper.r_cb @ curvature @ shaper.r_bc).T
    return result


def install(mapper, shaper):
    original = mapper._refresh_causal_dense_poses
    cache = {}
    audit = {'calls': 0, 'refreshed_views': 0, 'unbracketed_skips': 0,
             'residual_rebuilds': 0, 'bracket_changes': 0, 'future_imu_used': False}
    last_bracket = {}
    mapper._dense_pose_refresh_repair_audit = audit

    def refreshed(self):
        # The backend resets only bracketed poses to unshaped interpolation.
        updated = original()
        audit['calls'] += 1
        keys = sorted(k for k in self.viewpoints if isinstance(k, (int, float)))
        groups = defaultdict(list)
        for uid in self.polish_viewpoints:
            if uid not in shaper.left_residual_by_uid:
                continue
            pair = bracket(keys, uid)
            if pair is None:
                # Never compound a residual onto a camera original() skipped.
                audit['unbracketed_skips'] += 1
                continue
            groups[pair].append(uid)
        for (left, right), uids in groups.items():
            missing = [uid for uid in uids if (uid, left, right) not in cache]
            if missing:
                values = residuals(shaper, left, right, missing)
                for uid, value in values.items():
                    cache[(uid, left, right)] = value
                audit['residual_rebuilds'] += len(missing)
            for uid in uids:
                view = self.polish_viewpoints[uid]
                if getattr(view, 'causal_pose_residual', None) is not None:
                    raise RuntimeError('Unexpected second pose residual convention')
                pair = (left, right)
                if uid in last_bracket and last_bracket[uid] != pair:
                    audit['bracket_changes'] += 1
                last_bracket[uid] = pair
                residual = torch.eye(4, dtype=view.R.dtype, device=view.R.device)
                residual[:3, :3] = torch.as_tensor(cache[(uid, left, right)],
                                                  dtype=view.R.dtype, device=view.R.device)
                pose = torch.eye(4, dtype=view.R.dtype, device=view.R.device)
                pose[:3, :3], pose[:3, 3] = view.R, view.T
                corrected = residual @ pose
                view.update_RT(corrected[:3, :3], corrected[:3, 3])
                view.causal_pose_left_residual = residual.detach().cpu().clone()
                view.dense_pose_source = 'causal_raw_imu_current_bracket_refresh'
                view.dense_geometry_trusted = False
                audit['refreshed_views'] += 1
        return updated

    mapper._refresh_causal_dense_poses = MethodType(refreshed, mapper)
