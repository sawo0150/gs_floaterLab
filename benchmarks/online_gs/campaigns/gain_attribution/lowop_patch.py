"""Diagnostic: new Gaussians start nearly transparent (births unchanged otherwise).

GaussianModel.create_pcd_from_image* initialises every birth at opacity 0.5. Here every keyframe birth after the
first one of a map generation starts at opacity B_BIRTH_OPACITY (default 0.12, just above the protected-prune
threshold 0.1), so untrained new Gaussians barely cover what is already trained; training raises opacity where it
helps. Base sampler: uniform with replacement (sampling_mode_patch; pass --tau 1e12, B_WITH_REPLACEMENT=1).
Writes <output>/lowop.json.
"""
import atexit
from collections import Counter
import json
import math
import os
from pathlib import Path
import runpy
import sys

OP = float(os.environ.get('B_BIRTH_OPACITY', '0.12'))
STATS = Counter()


def install():
    import torch
    from gaussian.scene.gaussian_model import GaussianModel
    ext = GaussianModel.extend_from_pcd
    logit = math.log(OP / (1 - OP))

    def low_birth(model, *a, **k):
        first = len(model.get_xyz) == 0
        if not first:
            if 'opacities' in k:
                k['opacities'] = torch.full_like(k['opacities'], logit)
            elif len(a) >= 5:
                a = list(a); a[4] = torch.full_like(a[4], logit); a = tuple(a)
            STATS['low_births'] += 1
        else:
            STATS['first_births'] += 1
        before = len(model.get_xyz)
        out = ext(model, *a, **k)
        STATS['low_gaussians' if not first else 'first_gaussians'] += len(model.get_xyz) - before
        return out
    GaussianModel.extend_from_pcd = low_birth
    import sampling_mode_patch as SM
    SM.install()
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'lowop.json').write_text(json.dumps(dict(birth_opacity=OP, stats=dict(STATS)), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
