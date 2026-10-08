"""Validation arms of the online fixes (no measurement wrappers).

B_GROUP_K=16        ERVS K16 sampler (adopted)
B_NO_SCALE_PROJ=1   no per-packet scale clamp           | B_SCALE_CAP=x  clamp at x instead of 0.1
B_COVERED_OPACITY   selective births (selop_patch): already-explained pixels start at this opacity, others 0.5
Writes <output>/validate.json with the options and final-map giant-Gaussian counts.
"""
import atexit
import json
import os
from pathlib import Path
import runpy
import sys

STATE = dict(mapper=None)


def install():
    import online_mapper_runtime as R
    if os.environ.get('B_NO_SCALE_PROJ') == '1':
        rt_init = R.OnlineMapperRuntime.__init__

        def no_scale_init(self, *a, **k):
            rt_init(self, *a, **k)
            self.mapper.online_unified_scale_projection = False
        R.OnlineMapperRuntime.__init__ = no_scale_init
    if os.environ.get('B_SCALE_CAP'):
        import scale_cap_patch
        scale_cap_patch.install(os.environ['B_SCALE_CAP'])
    if os.environ.get('B_COVERED_OPACITY'):
        import selop_patch
        selop_patch.install(probe=False)
    dispatch = R.OnlineMapperRuntime.dispatch

    def keep(self, packet):
        STATE['mapper'] = self.mapper
        return dispatch(self, packet)
    R.OnlineMapperRuntime.dispatch = keep
    import group_k_patch as GK
    GK.install()
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            info = {k: os.environ.get(k) for k in ('B_GROUP_K', 'B_NO_SCALE_PROJ', 'B_SCALE_CAP', 'B_COVERED_OPACITY')}
            mp = STATE['mapper']
            if mp is not None:
                import torch
                with torch.no_grad():
                    s = mp.gaussians.get_scaling.max(1).values; o = mp.gaussians.get_opacity.reshape(-1)
                    info.update(gaussians=int(len(s)), max_scale=float(s.max()), giant=int(((s > 0.3) & (o > 0.3)).sum()),
                                projection_calls=getattr(mp, 'online_unified_projection_calls', None))
            (output / 'validate.json').write_text(json.dumps(info, indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
