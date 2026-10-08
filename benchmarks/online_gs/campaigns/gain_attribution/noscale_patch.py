"""Diagnostic: online unified mapping without the per-packet scale projection (max scale 0.1) of the B recipe.

The B worker args keep `--unified-scale-projection`; this patch only sets mapper.online_unified_scale_projection = False
right after the runtime is built, so no packet clamps Gaussian scales. Base sampler: uniform with replacement
(sampling_mode_patch; pass --tau 1e12 and B_WITH_REPLACEMENT=1), the same as the online / D2 reference.
"""
import os
from pathlib import Path
import runpy
import sys


def install():
    import online_mapper_runtime as R
    init = R.OnlineMapperRuntime.__init__

    def no_scale_init(self, *a, **k):
        init(self, *a, **k)
        self.mapper.online_unified_scale_projection = False
    R.OnlineMapperRuntime.__init__ = no_scale_init
    import sampling_mode_patch as SM
    SM.install()


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
