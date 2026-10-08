"""Settle-triggered consolidation on top of online uniform with replacement (runtime patch; births unchanged).

Touch: after every keyframe birth, the new Gaussians' centres (≤2000) are projected into the pool keyframes older than
the newest LAG (current poses; frustum + positive depth). A KF is touched if ≥ B_CONS_SHARE of the new points fall in
its image. Settle: a touched KF becomes settled once B_CONS_M keyframes have arrived since its last touch; it is then
queued once for consolidation together with the admitted dense views anchored to it (left anchor = last KF before the
dense frame). Draws: keyframe/dense-role draws serve the consolidation queues first while consolidation draws stay
≤ B_CONS_FRAC of all draws so far; otherwise uniform with replacement (sampling_mode_patch semantics, --tau 1e12).
Same credit, quotas, window, births. Writes <output>/consolidation.json.
"""
import atexit
import bisect
from collections import Counter, deque
import hashlib
import inspect
import json
import os
from pathlib import Path
import runpy
import sys
import textwrap

LAG = int(os.environ.get('B_CONS_LAG', '6'))
M = int(os.environ.get('B_CONS_M', '6'))
SHARE = float(os.environ.get('B_CONS_SHARE', '0.05'))
FRAC = float(os.environ.get('B_CONS_FRAC', '0.15'))
STATE = dict(mapper=None, touched={}, queue={'keyframe': deque(), 'dense': deque()}, events=[], stats=Counter())


def install():
    import torch
    import online_mapper_runtime as R
    import unified_view_training as U
    import sampling_mode_patch as SM
    import group_k_patch as GK
    from gaussian.scene.gaussian_model import GaussianModel
    st = STATE['stats']

    dispatch = R.OnlineMapperRuntime.dispatch

    def keep(self, packet):
        STATE['mapper'] = self.mapper
        return dispatch(self, packet)
    R.OnlineMapperRuntime.dispatch = keep

    ext = GaussianModel.extend_from_pcd

    def birth(model, *a, **k):
        before = len(model.get_xyz)
        out = ext(model, *a, **k)
        mp = STATE['mapper']
        if len(model.get_xyz) > before and mp is not None and getattr(mp, 'online_view_trainer', None) is not None:
            try:
                touch_and_settle(mp, model.get_xyz[before:].detach())
            except Exception as e:
                st['error'] += 1; STATE['events'].append(dict(error=repr(e)[:200]))
        return out
    GaussianModel.extend_from_pcd = birth

    def touch_and_settle(mp, xyz):
        pol = mp.online_view_trainer.policy
        kfs = sorted(pol.keyframes); now = len(kfs)
        touched = STATE['touched']
        old = kfs[:-LAG] if len(kfs) > LAG else []
        n_touch = 0
        if old:
            with torch.no_grad():
                idx = torch.randperm(len(xyz), device=xyz.device)[:2000]
                P = torch.cat([xyz[idx], torch.ones(len(idx), 1, device=xyz.device)], 1)
                for u in old:
                    v = mp.viewpoints.get(u)
                    if v is None:
                        continue
                    c = P @ v.world_view_transform.to(P.device); z = c[:, 2]
                    x = v.fx * c[:, 0] / z.clamp_min(1e-6) + v.cx; y = v.fy * c[:, 1] / z.clamp_min(1e-6) + v.cy
                    if float(((z > 0.05) & (x >= 0) & (x < v.image_width) & (y >= 0) & (y < v.image_height)).float().mean()) >= SHARE:
                        touched[u] = now; n_touch += 1
        settled = [u for u, t in touched.items() if now - t >= M]
        q = STATE['queue']
        for u in settled:
            del touched[u]
            q['keyframe'].append(u)
            dense = [d for d in sorted(pol.admitted) if (lambda i: i >= 0 and kfs[i] == u)(bisect.bisect_right(kfs, d) - 1)]
            q['dense'].extend(dense)
            st['settled_kf'] += 1; st['queued_dense'] += len(dense)
        STATE['events'].append(dict(kfs=now, touched_now=n_touch, settled=len(settled), pending=len(touched),
                                    queue=dict(keyframe=len(q['keyframe']), dense=len(q['dense']))))

    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    if hashlib.sha256(src.encode()).hexdigest() != GK.RESERVE_SHA256:
        raise RuntimeError('UnifiedTrainingSet.reserve changed')
    src = src.replace(SM.OLD.strip(), SM.NEW.strip())
    assert src.count(GK.OLD) == 1
    src = src.replace(GK.OLD, 'uid = _CONS_DRAW(self, role, pools[role], candidates, weights)')

    def cons_draw(self, role, pool, candidates, weights):
        st['draws'] += 1
        q = STATE['queue'].get(role)
        if q and st['cons_draws'] < FRAC * st['draws']:
            members = set(pool)
            while q:
                u = q.popleft()
                if u in members:
                    st['cons_draws'] += 1; st['cons_draw', role] += 1
                    return u
                st['cons_skip', role] += 1
        return self.rng.choices(candidates, weights=weights, k=1)[0]

    ns = dict(vars(U), _CONS_DRAW=cons_draw)
    exec(compile(src, f'<consolidation_patch:{U.__file__}>', 'exec'), ns)
    patched = ns['reserve']

    def reserve(self, *a, **k):
        if self.selector != 'ervs' or self.tau < 1e11:
            raise RuntimeError('consolidation patch requires --selector ervs and --tau >= 1e11 (uniform base)')
        return patched(self, *a, **k)
    U.UnifiedTrainingSet.reserve = reserve

    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'consolidation.json').write_text(json.dumps(dict(
                lag=LAG, M=M, share=SHARE, frac=FRAC,
                stats={('/'.join(k) if isinstance(k, tuple) else k): v for k, v in st.items()},
                left_in_queue={r: len(q) for r, q in STATE['queue'].items()}, pending_at_end=len(STATE['touched']),
                events=STATE['events']), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
