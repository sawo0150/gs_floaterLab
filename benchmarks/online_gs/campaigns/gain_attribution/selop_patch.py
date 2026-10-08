"""Selective low-opacity births: same birth count and positions; only the initial opacity depends on coverage.

At every keyframe birth after the first of a generation, the current map is rendered (no grad) from the birth KF
before the new Gaussians are added. Each new point is projected into that KF: if the pixel is already explained by the
map (Gaussian-SLAM rule, gaussian_slam_seed_mask: rendered alpha ≥ 0.6 and no positive depth residual > 40 × median
|error|), the point starts at opacity B_COVERED_OPACITY (default 0.12); otherwise (hole / new surface in front) at the
default 0.5. Exp98–100 removed the covered candidates instead and lost 34–58% of the Gaussians; here count and
positions are unchanged. The birth probe (birth_probe_patch) is installed on top to measure immediate damage.
Base sampler: uniform with replacement (pass --tau 1e12, B_WITH_REPLACEMENT=1). Writes <output>/selop.json.
"""
import atexit
from collections import Counter
import json
import math
import os
from pathlib import Path
import runpy
import sys

OP = float(os.environ.get('B_COVERED_OPACITY', '0.12'))
ALPHA, MULT = 0.6, 40.0
STATE = dict(mapper=None, stats=Counter())


def install():
    import torch
    import online_mapper_runtime as R
    import gs_backend
    from gaussian.scene.gaussian_model import GaussianModel
    st = STATE['stats']

    dispatch = R.OnlineMapperRuntime.dispatch

    def keep(self, packet):
        STATE['mapper'] = self.mapper
        return dispatch(self, packet)
    R.OnlineMapperRuntime.dispatch = keep

    ext = GaussianModel.extend_from_pcd
    logit = math.log(OP / (1 - OP))
    names = ('fused_point_cloud', 'features', 'scales', 'rots', 'opacities', 'kf_id')

    def selective(model, *a, **k):
        args = dict(zip(names, a)); args.update(k)
        mp = STATE['mapper']
        v = mp.viewpoints.get(int(args.get('kf_id', -1))) if mp is not None else None
        if len(model.get_xyz) == 0 or v is None:
            st['skipped_births'] += 1
            return ext(model, *a, **k)
        try:
            with torch.no_grad():
                pkg = gs_backend.render(v, model, mp.background)
                T = pkg['transmittance'].squeeze(); D = pkg['depth'].squeeze()
                H, W = D.shape
                P = args['fused_point_cloud'].detach().float()
                c = torch.cat([P, torch.ones(len(P), 1, device=P.device)], 1) @ v.world_view_transform.to(P.device)
                z = c[:, 2]
                x = (v.fx * c[:, 0] / z.clamp_min(1e-6) + v.cx).round().long()
                y = (v.fy * c[:, 1] / z.clamp_min(1e-6) + v.cy).round().long()
                inside = (z > 0) & (x >= 0) & (x < W) & (y >= 0) & (y < H)
                xi, yi = x.clamp(0, W - 1), y.clamp(0, H - 1)
                alpha = 1 - T[yi, xi]; pred = D[yi, xi]
                valid = inside & torch.isfinite(pred) & (z > 0)
                err = (z - pred).abs()
                med = err[valid].median() if valid.any() else torch.zeros((), device=P.device)
                eligible = (alpha < ALPHA) | ((pred > z) & (err > MULT * med)) | ~valid
                covered = ~eligible
                op = args['opacities'].detach().clone()
                op[covered] = logit
            args['opacities'] = op
            st['births'] += 1; st['points'] += int(len(P)); st['covered_points'] += int(covered.sum())
            st['outside_points'] += int((~inside).sum())
            return ext(model, **args)
        except Exception as e:
            st['error'] += 1; STATE.setdefault('err', repr(e)[:300])
            return ext(model, *a, **k)
    GaussianModel.extend_from_pcd = selective

    import birth_probe_patch as BP          # outermost wrapper: before/after renders around the whole birth
    BP.install()                            # also installs sampling_mode_patch (with replacement)
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            s = dict(st)
            s['covered_share'] = s.get('covered_points', 0) / max(1, s.get('points', 0))
            (output / 'selop.json').write_text(json.dumps(dict(covered_opacity=OP, alpha=ALPHA, mult=MULT, stats=s,
                                                               error=STATE.get('err')), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
