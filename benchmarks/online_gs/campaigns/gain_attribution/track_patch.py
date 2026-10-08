"""Measurement only: birth probe + periodic PSNR of every pool keyframe, online or offline (training unchanged).

B_TRACK_BASE = online  → online uniform with replacement (pass --tau 1e12, B_WITH_REPLACEMENT=1)
             = offline → offline_patch (deferred training; B_OFFLINE_REF / B_OFFLINE_LAST_UID as usual)
Births: birth_probe_patch (before/after renders of covered/control old KFs, no training in between).
Tracking: after every photometric step that crosses a multiple of B_TRACK_EVERY completed RGB services, every
keyframe of the current pool is rendered without gradient and its PSNR against its own RGB is logged.
B_NO_SCALE_PROJ=1 disables the per-packet scale clamp. Writes <output>/track.json (+ birth_probe.json).
"""
import atexit
import json
import os
from pathlib import Path
import runpy
import sys

BASE = os.environ.get('B_TRACK_BASE', 'online')
EVERY = int(os.environ.get('B_TRACK_EVERY', '50'))
SNAPS = []


def install():
    import torch
    import online_photometric as P
    import online_mapper_runtime as R
    import gs_backend
    if BASE == 'offline':
        import offline_patch
        offline_patch.install()
    if os.environ.get('B_NO_SCALE_PROJ') == '1' and BASE == 'online':   # offline_patch handles its own switch
        rt_init = R.OnlineMapperRuntime.__init__

        def no_scale_init(self, *a, **k):
            rt_init(self, *a, **k)
            self.mapper.online_unified_scale_projection = False
        R.OnlineMapperRuntime.__init__ = no_scale_init
    import birth_probe_patch as BP
    BP.install(sampler=(BASE == 'online'))

    def psnr(mp, v):
        out = gs_backend.render(v, mp.gaussians, mp.background)['render'].clamp(0, 1)
        gt = v.original_image_gpu if getattr(v, 'original_image_gpu', None) is not None else torch.as_tensor(v.original_image).cuda()
        gt = gt.to(out.dtype)
        if gt.shape != out.shape:
            return None
        return float(-10 * torch.log10(((out - gt) ** 2).mean().clamp_min(1e-10)))

    step = P.OnlinePhotometricTrainer.step
    last = {}

    def tracked(self, *a, **k):
        res = step(self, *a, **k)
        try:
            pol = self.policy; n = pol.rgb_view_services; g = getattr(self, 'generation', None)
            mp = BP.STATE['mapper']
            if mp is not None and n // EVERY > last.get(g, -1):
                last[g] = n // EVERY
                with torch.no_grad():
                    vals = {int(u): psnr(mp, mp.viewpoints[u]) for u in sorted(pol.keyframes) if u in mp.viewpoints}
                SNAPS.append(dict(generation=g, services=int(n), gaussians=int(len(mp.gaussians.get_xyz)),
                                  psnr={u: round(x, 4) for u, x in vals.items() if x is not None}))
        except Exception as e:
            SNAPS.append(dict(error=repr(e)[:200]))
        return res
    P.OnlinePhotometricTrainer.step = tracked
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'track.json').write_text(json.dumps(dict(base=BASE, every=EVERY, snapshots=SNAPS)) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
