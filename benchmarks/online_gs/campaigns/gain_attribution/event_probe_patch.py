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
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'event_probe.json').write_text(json.dumps(dict(events=EVENTS)) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
