"""Measurement only: PSNR change of every pool keyframe across each map-changing event (training unchanged).

Around each operation below, all keyframes of the current pool are rendered (no grad) right before and right after
it, with no optimizer step in between; PSNR is against each KF's own RGB at its current camera pose.
  packet      GSBackEnd.process_track_data (whole tracker packet: camera pose refinements, births, corrections)
  move        GSBackEnd._apply_pose_scale_updates on the live model (pose/scale correction moving Gaussians)
  birth       GaussianModel.extend_from_pcd
  prune       ProtectedOpacityPrune.after_packet (only logged when it removes Gaussians)
  control     OnlineMapperRuntime._apply_control (metric rescale / mapper reset)
Nested events are logged separately (packet includes its births/moves). Training contributions are the changes
between consecutive events. Base: online uniform with replacement (--tau 1e12, B_WITH_REPLACEMENT=1);
B_NO_SCALE_PROJ=1 disables the scale clamp. Writes <output>/event_probe.json.
"""
import atexit
import json
import os
from pathlib import Path
import runpy
import sys

EVENTS = []
STATE = dict(mapper=None, depth=0, services=0)


def install():
    import torch
    import online_mapper_runtime as R
    import gs_backend
    from gaussian.scene.gaussian_model import GaussianModel
    import protected_opacity_prune as PP

    if os.environ.get('B_NO_SCALE_PROJ') == '1':
        rt_init = R.OnlineMapperRuntime.__init__

        def no_scale_init(self, *a, **k):
            rt_init(self, *a, **k)
            self.mapper.online_unified_scale_projection = False
        R.OnlineMapperRuntime.__init__ = no_scale_init

    if os.environ.get('B_ROW_ADAM') == '1':         # per-Gaussian Adam bias correction (rowadam_patch)
        import rowadam_patch
        rowadam_patch.install()
    if os.environ.get('B_COVERED_OPACITY'):         # optional: selective low-opacity births (selop_patch)
        import selop_patch
        selop_patch.install(probe=False)
    if os.environ.get('B_BIRTH_OPACITY'):           # optional: low-opacity births (lowop_patch), measured from outside
        import lowop_patch
        lowop_patch.install(sampler=False)

    def snapshot(mp):
        tr = getattr(mp, 'online_view_trainer', None) if mp is not None else None
        if tr is None or len(mp.gaussians.get_xyz) == 0:
            return None
        out = {}
        with torch.no_grad():
            for u in sorted(tr.policy.keyframes):
                v = mp.viewpoints.get(u)
                if v is None:
                    continue
                img = gs_backend.render(v, mp.gaussians, mp.background)['render'].clamp(0, 1)
                gt = v.original_image_gpu if getattr(v, 'original_image_gpu', None) is not None else torch.as_tensor(v.original_image).cuda()
                gt = gt.to(img.dtype)
                if gt.shape == img.shape:
                    out[int(u)] = float(-10 * torch.log10(((img - gt) ** 2).mean().clamp_min(1e-10)))
        return out, int(tr.policy.rgb_view_services), getattr(tr, 'generation', None)

    def measured(kind, mp_of, fn, info=None):
        def wrapper(*a, **k):
            mp = mp_of(a)
            try:
                before = snapshot(mp)
            except Exception:
                before = None
            n0 = len(mp.gaussians.get_xyz) if mp is not None else 0
            res = fn(*a, **k)
            try:
                after = snapshot(mp) if before is not None else None
                if before is not None and after is not None:
                    b, svc, gen = before; aft = after[0]
                    common = [u for u in b if u in aft]
                    ex = info(a, k, res) if info else {}
                    n1 = len(mp.gaussians.get_xyz)
                    if kind == 'prune' and n1 == n0:
                        return res
                    EVENTS.append(dict(kind=kind, services=svc, generation=gen, gaussians=(n0, n1), n=len(common),
                                       before={u: round(b[u], 4) for u in common},
                                       after={u: round(aft[u], 4) for u in common}, **ex))
            except Exception as e:
                EVENTS.append(dict(kind=kind, error=repr(e)[:200]))
            return res
        return wrapper

    dispatch = R.OnlineMapperRuntime.dispatch

    def keep(self, packet):
        STATE['mapper'] = self.mapper
        return dispatch(self, packet)
    R.OnlineMapperRuntime.dispatch = keep
    mp_now = lambda a: STATE['mapper']

    B = gs_backend.GSBackEnd
    B.process_track_data = measured('packet', lambda a: a[0], B.process_track_data,
                                    lambda a, k, r: dict(corr=a[1].get('pose_updates') is not None,
                                                         frames=[int(x) for x in a[1]['tstamp'][-1:].tolist()] if a[1].get('tstamp') is not None else None))
    apply = B._apply_pose_scale_updates

    def move(self, model, packet):
        if model is self.gaussians:
            return measured('move', lambda a: a[0], apply)(self, model, packet)
        return apply(self, model, packet)
    B._apply_pose_scale_updates = move
    GaussianModel.extend_from_pcd = measured('birth', mp_now, GaussianModel.extend_from_pcd)
    PP.ProtectedOpacityPrune.after_packet = measured('prune', lambda a: a[0].mapper, PP.ProtectedOpacityPrune.after_packet)
    R.OnlineMapperRuntime._apply_control = measured('control', lambda a: a[0].mapper, R.OnlineMapperRuntime._apply_control,
                                                    lambda a, k, r: dict(control=str(a[1])))
    if os.environ.get('B_GROUP_K'):               # ERVS K-group sampler (adopted ERVS, tau from worker args)
        import group_k_patch as GK
        GK.install()
    else:                                          # uniform with replacement (--tau 1e12)
        import sampling_mode_patch as SM
        SM.install()
    RM = int(os.environ.get('B_REFRESH_M', '0'))
    if RM > 0:                                     # one refresh replay per change episode once a view's region settles
        import bisect
        from collections import deque
        import group_k_patch as GK
        import unified_view_training as U
        SL = int(os.environ.get('B_REFRESH_SLOTS', '1'))
        rf = STATE.setdefault('refresh', dict(touch_events=0, settled_kf=0, queued_dense=0, served_kf=0, served_dense=0,
                                              skipped=0, pending_end=0))
        touched, queues, batch = {}, {'keyframe': deque(), 'dense': deque()}, {'n': 0}
        ext0 = GaussianModel.extend_from_pcd

        def refresh_birth(model, *a, **k):
            n0 = len(model.get_xyz)
            out = ext0(model, *a, **k)
            mp = STATE['mapper']
            if mp is None or getattr(mp, 'online_view_trainer', None) is None or len(model.get_xyz) <= n0:
                return out
            with torch.no_grad():
                pol = mp.online_view_trainer.policy; kfs = sorted(pol.keyframes); now = len(kfs)
                xyz = model.get_xyz[n0:].detach()
                idx = torch.randperm(len(xyz), device=xyz.device)[:2000]
                P = torch.cat([xyz[idx], torch.ones(len(idx), 1, device=xyz.device)], 1)
                for u in (kfs[:-6] if len(kfs) > 6 else []):
                    v = mp.viewpoints.get(u)
                    if v is None:
                        continue
                    c = P @ v.world_view_transform.to(P.device); z = c[:, 2]
                    x = v.fx * c[:, 0] / z.clamp_min(1e-6) + v.cx; y = v.fy * c[:, 1] / z.clamp_min(1e-6) + v.cy
                    if float(((z > 0.05) & (x >= 0) & (x < v.image_width) & (y >= 0) & (y < v.image_height)).float().mean()) >= 0.05:
                        touched[u] = now; rf['touch_events'] += 1
                for u in [u for u, t in touched.items() if now - t >= RM]:
                    del touched[u]
                    queues['keyframe'].append(u); rf['settled_kf'] += 1
                    dense = [d for d in sorted(pol.admitted) if (lambda i: i >= 0 and kfs[i] == u)(bisect.bisect_right(kfs, d) - 1)]
                    queues['dense'].extend(dense); rf['queued_dense'] += len(dense)
                rf['pending_end'] = len(touched)
            return out
        GaussianModel.extend_from_pcd = refresh_birth

        draw0 = GK.NAMESPACE['_GROUP_DRAW']

        def refresh_draw(self, role, pool, used, scale, candidates, weights):
            q = queues.get(role)
            if q and batch['n'] < SL:
                members = set(pool)
                while q:
                    u = q.popleft()
                    if u in members and u not in used:
                        batch['n'] += 1; rf['served_' + ('kf' if role == 'keyframe' else 'dense')] += 1
                        return u
                    rf['skipped'] += 1
            return draw0(self, role, pool, used, scale, candidates, weights)
        GK.NAMESPACE['_GROUP_DRAW'] = refresh_draw
        reserve2 = U.UnifiedTrainingSet.reserve

        def refresh_reserve(self, *a, **k):
            batch['n'] = 0
            return reserve2(self, *a, **k)
        U.UnifiedTrainingSet.reserve = refresh_reserve
    CU = float(os.environ.get('B_CATCHUP_FRAC', '0'))
    if CU > 0:                                     # target-based catch-up replaces the fixed recent-KF window
        import unified_view_training as U
        reserve1 = U.UnifiedTrainingSet.reserve
        SLOTS = int(os.environ.get('B_CATCHUP_SLOTS', '3'))
        cu = STATE.setdefault('catchup', dict(calls=0, slots_used=0, empty=0, kf=0, dense=0, trace=[]))

        class _KF(set):                            # lets `set(window) & self.keyframes` keep dense catch-up views
            extra = frozenset()

            def __rand__(self, other):
                return set(other) & (set(self) | self.extra)

        def catchup_reserve(self, *a, window=(), **k):
            cu['calls'] += 1
            views = sorted(self.keyframes | self.admitted)
            target = (self.rgb_view_services + 1) / max(1, len(views))      # causal per-view budget so far
            need = sorted((u for u in views if self.counts.get(u, 0) < CU * target),
                          key=lambda u: (self.counts.get(u, 0), -u))[:SLOTS]
            cu['slots_used'] += len(need); cu['empty'] += not need
            cu['kf'] += sum(u in self.keyframes for u in need); cu['dense'] += sum(u in self.admitted for u in need)
            if cu['calls'] % 10 == 0:
                cu['trace'].append((int(self.rgb_view_services), round(target, 2), len(need)))
            kf = self.keyframes
            self.keyframes = _KF(kf); self.keyframes.extra = frozenset(u for u in need if u in self.admitted)
            try:
                return reserve1(self, *a, window=tuple(need), **k)
            finally:
                self.keyframes = kf
        U.UnifiedTrainingSet.reserve = catchup_reserve

    OFF_UID = int(os.environ.get('B_WINDOW_OFF_FROM_UID', '-1'))
    if OFF_UID >= 0:                               # diagnostic: no window role once the newest window KF reaches OFF_UID
        import unified_view_training as U
        reserve0 = U.UnifiedTrainingSet.reserve
        off_stats = STATE.setdefault('window_off', dict(calls=0, off=0, from_uid=OFF_UID))

        def no_window_reserve(self, *a, window=(), **k):
            off_stats['calls'] += 1
            if window and max(window) >= OFF_UID:
                window = (); off_stats['off'] += 1   # its quota is refilled by the KF / dense roles
            return reserve0(self, *a, window=window, **k)
        U.UnifiedTrainingSet.reserve = no_window_reserve
    LAG = int(os.environ.get('B_WINDOW_LAG', '0'))
    if LAG > 0:                                    # window role trains the KFs LAG positions behind the current window
        import unified_view_training as U
        reserve = U.UnifiedTrainingSet.reserve
        lag_stats = STATE.setdefault('lag', dict(calls=0, shifted=0))

        def lagged_reserve(self, *a, window=(), **k):
            w = sorted(set(window) & self.keyframes)
            if w:
                kfs = sorted(self.keyframes)
                hi = kfs.index(w[-1]) - LAG
                lo = hi - len(w) + 1
                if hi >= 0:
                    window = tuple(kfs[max(0, lo):hi + 1]); lag_stats['shifted'] += 1
                else:
                    window = ()                    # nothing old enough yet: window quota falls to the other roles
            lag_stats['calls'] += 1
            return reserve(self, *a, window=window, **k)
        U.UnifiedTrainingSet.reserve = lagged_reserve
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'event_probe.json').write_text(json.dumps(dict(events=EVENTS, window_lag=STATE.get('lag'), window_off=STATE.get('window_off'), catchup=STATE.get('catchup'), refresh=STATE.get('refresh'),
                optimizer=type(STATE['mapper'].gaussians.optimizer).__name__ if STATE['mapper'] is not None else None)) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
