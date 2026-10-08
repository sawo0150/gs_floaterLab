"""Diagnostic: does a keyframe birth itself degrade already-trained views? (measurement only; training unchanged)

At every keyframe birth after the first of a generation, before the new Gaussians are added, the new points
(the fused point cloud passed to extend_from_pcd) are projected into the keyframes older than the newest B_PROBE_LAG.
Up to B_PROBE_N of them seeing the largest share of new points ("covered") and B_PROBE_N with no new points ("control")
are rendered without gradient right before and right after the birth (no optimizer step in between); the PSNR of each
render against that keyframe's own RGB is logged. Δ = after − before isolates the immediate effect of the birth.
No-grad renders are counted separately by the render audit and do not change the training budget.
Base sampler: uniform with replacement (sampling_mode_patch; pass --tau 1e12, B_WITH_REPLACEMENT=1).
Writes <output>/birth_probe.json.
"""
import atexit
import json
import os
from pathlib import Path
import runpy
import sys

LAG = int(os.environ.get('B_PROBE_LAG', '6'))
N = int(os.environ.get('B_PROBE_N', '6'))
STATE = dict(mapper=None, events=[], errors=0)


def install(sampler=True):
    import torch
    import online_mapper_runtime as R
    import gs_backend
    from gaussian.scene.gaussian_model import GaussianModel

    dispatch = R.OnlineMapperRuntime.dispatch

    def keep(self, packet):
        STATE['mapper'] = self.mapper
        return dispatch(self, packet)
    R.OnlineMapperRuntime.dispatch = keep

    def psnr(mp, v):
        out = gs_backend.render(v, mp.gaussians, mp.background)['render'].clamp(0, 1)
        gt = v.original_image_gpu if getattr(v, 'original_image_gpu', None) is not None else torch.as_tensor(v.original_image).cuda()
        gt = gt.to(out.dtype)
        if gt.shape != out.shape:
            return None
        mse = ((out - gt) ** 2).mean()
        return float(-10 * torch.log10(mse.clamp_min(1e-10)))

    ext = GaussianModel.extend_from_pcd

    def probe_birth(model, *a, **k):
        mp = STATE['mapper']
        pts = k.get('fused_point_cloud', a[0] if a else None)
        probes = None
        if mp is not None and len(model.get_xyz) > 0 and pts is not None and getattr(mp, 'online_view_trainer', None) is not None:
            try:
                with torch.no_grad():
                    kfs = sorted(mp.online_view_trainer.policy.keyframes)
                    old = [u for u in kfs[:-LAG]] if len(kfs) > LAG else []
                    P = pts.detach().float()
                    if len(P) > 3000:
                        P = P[torch.randperm(len(P), device=P.device)[:3000]]
                    P = torch.cat([P, torch.ones(len(P), 1, device=P.device)], 1)
                    share = {}
                    for u in old:
                        v = mp.viewpoints.get(u)
                        if v is None or getattr(v, 'original_image_gpu', None) is None and v.original_image is None:
                            continue
                        c = P @ v.world_view_transform.to(P.device); z = c[:, 2]
                        x = v.fx * c[:, 0] / z.clamp_min(1e-6) + v.cx; y = v.fy * c[:, 1] / z.clamp_min(1e-6) + v.cy
                        share[u] = float(((z > 0.05) & (x >= 0) & (x < v.image_width) & (y >= 0) & (y < v.image_height)).float().mean())
                    order = sorted(share, key=lambda u: -share[u])
                    covered = [u for u in order if share[u] > 0.05][:N]
                    control = [u for u in order[::-1] if share[u] == 0.0][:N]
                    if covered or control:
                        probes = [(u, 'covered' if u in covered else 'control', share[u],
                                   psnr(mp, mp.viewpoints[u])) for u in covered + control]
            except Exception as e:
                STATE['errors'] += 1; probes = None
        out = ext(model, *a, **k)
        if probes:
            try:
                with torch.no_grad():
                    rows = []
                    for u, kind, sh, before in probes:
                        after = psnr(mp, mp.viewpoints[u])
                        if before is not None and after is not None:
                            rows.append(dict(uid=int(u), kind=kind, share=round(sh, 4), before=round(before, 4),
                                             after=round(after, 4), delta=round(after - before, 4)))
                    STATE['events'].append(dict(n_new=int(len(pts)), gaussians=int(len(model.get_xyz)),
                                                services=int(mp.online_view_trainer.policy.rgb_view_services), probes=rows))
            except Exception:
                STATE['errors'] += 1
        return out
    GaussianModel.extend_from_pcd = probe_birth

    if sampler:                             # uniform with replacement (default); off when another patch owns draws
        import sampling_mode_patch as SM
        SM.install()
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            rows = [r for e in STATE['events'] for r in e['probes']]
            summ = {}
            for kind in ('covered', 'control'):
                d = [r['delta'] for r in rows if r['kind'] == kind]
                summ[kind] = dict(n=len(d), mean_delta=(sum(d) / len(d) if d else None),
                                  share_negative=(sum(x < 0 for x in d) / len(d) if d else None))
            (output / 'birth_probe.json').write_text(json.dumps(dict(
                lag=LAG, n=N, errors=STATE['errors'], summary=summ, events=STATE['events']), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
