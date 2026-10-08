"""Birth-triggered repair replay on top of ERVS K16 (runtime patch; births, ERVS weights and K-group queue unchanged).

Finding behind it (gap_ladder + birth analysis): deferring the same updates until all Gaussians exist gains ~1 dB, while
suppressing births in covered space costs 2 dB (exp98–100). So late-born Gaussians are needed capacity that stays
under-trained online: in an old region they are only trained when an old view of that region is replayed later.

Rule: after every keyframe birth event, the new Gaussians' centres (subsample) are projected into the pool keyframes
older than the newest B_REPAIR_LAG KFs (current poses, current intrinsics; frustum + positive depth). The B_REPAIR_N
keyframes seeing the largest share of the new Gaussians (share ≥ B_REPAIR_MIN) go to the front of the KF-role queue,
and the admitted dense views anchored to them (up to B_REPAIR_N) to the front of the dense-role queue. Draws take
repair views first, then ERVS K16 groups. Same credit, quotas, window and births: only which views are served first.
Writes <output>/birth_repair.json.
"""
import atexit
from collections import Counter, deque
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import runpy
import sys
import textwrap

LAG = int(os.environ.get('B_REPAIR_LAG', '6'))
N = int(os.environ.get('B_REPAIR_N', '6'))
MIN = float(os.environ.get('B_REPAIR_MIN', '0.2'))
K = int(os.environ.get('B_GROUP_K', '16'))
STATE = dict(mapper=None, repair={'keyframe': deque(), 'dense': deque()}, events=[], stats=Counter())


def install():
    import torch
    import online_mapper_runtime as R
    import unified_view_training as U
    import group_k_patch as GK
    from gaussian.scene.gaussian_model import GaussianModel
    st = STATE['stats']

    dispatch = R.OnlineMapperRuntime.dispatch

    def keep_dispatch(self, packet):
        STATE['mapper'] = self.mapper
        return dispatch(self, packet)
    R.OnlineMapperRuntime.dispatch = keep_dispatch

    birth = GaussianModel.extend_from_pcd

    def repair_birth(model, *a, **k):
        before = len(model.get_xyz)
        out = birth(model, *a, **k)
        after = len(model.get_xyz)
        mp = STATE['mapper']
        if after > before and mp is not None and getattr(mp, 'online_view_trainer', None) is not None:
            try:
                schedule_repair(mp, model.get_xyz[before:after].detach())
            except Exception as e:   # diagnostics must never break mapping
                st['repair_error'] += 1; STATE['events'].append(dict(error=repr(e)[:200]))
        return out
    GaussianModel.extend_from_pcd = repair_birth

    def schedule_repair(mp, xyz):
        policy = mp.online_view_trainer.policy
        kfs = sorted(policy.keyframes)
        old = kfs[:-LAG] if len(kfs) > LAG else []
        if not old:
            st['birth_no_old_kf'] += 1
            return
        with torch.no_grad():
            idx = torch.randperm(len(xyz), device=xyz.device)[:2000]
            P = torch.cat([xyz[idx], torch.ones(len(idx), 1, device=xyz.device)], 1)
            share = {}
            for u in old:
                v = mp.viewpoints.get(u)
                if v is None:
                    continue
                c = P @ v.world_view_transform.to(P.device)          # world_view_transform is stored transposed
                z = c[:, 2]
                x = v.fx * c[:, 0] / z.clamp_min(1e-6) + v.cx
                y = v.fy * c[:, 1] / z.clamp_min(1e-6) + v.cy
                inside = (z > 0.05) & (x >= 0) & (x < v.image_width) & (y >= 0) & (y < v.image_height)
                share[u] = float(inside.float().mean())
        top = [u for u, s in sorted(share.items(), key=lambda t: -t[1]) if s >= MIN][:N]
        if not top:
            st['birth_no_covisible'] += 1
            return
        rq = STATE['repair']
        for u in top:
            rq['keyframe'].append(u)
        anchors = set(top)
        dense = [u for u in sorted(policy.admitted)
                 if u in policy.offered and (policy.offered[u].left in anchors or policy.offered[u].right in anchors)]
        for u in dense[:N]:
            rq['dense'].append(u)
        st['birth_repair_events'] += 1; st['repair_kf_queued'] += len(top); st['repair_dense_queued'] += len(dense[:N])
        STATE['events'].append(dict(n_new=int(len(xyz)), top=[(int(u), round(share[u], 3)) for u in top], dense=len(dense[:N])))

    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    if hashlib.sha256(src.encode()).hexdigest() != GK.RESERVE_SHA256:
        raise RuntimeError('UnifiedTrainingSet.reserve changed')
    src = src.replace(GK.OLD, 'uid = _REPAIR_DRAW(self, role, pools[role], used, scales[role], candidates)')

    def repair_draw(self, role, pool, used, scale, candidates):
        members = set(pool)
        rq = STATE['repair'].get(role)
        while rq:
            u = rq.popleft()
            if u in members and u not in used:
                st['repair_draw', role] += 1
                return u
            st['repair_skip', role] += 1
        q = self.__dict__.setdefault('_repair_groups', {}).setdefault(role, deque())
        for attempt in range(2):
            while q:
                u = q.popleft()
                if u in members and u not in used:
                    st['ervs_draw', role] += 1
                    return u
            if attempt == 0:
                ordered = sorted(members); low = min(self.counts[u] for u in ordered)
                keys = sorted(((-(self.counts[u] - low) / scale - math.log(-math.log(max(self.rng.random(), 1e-15))), u)
                               for u in ordered), reverse=True)
                q.extend(u for _, u in keys[:min(K, len(keys))])
        st['fallback', role] += 1
        return self.rng.choice(candidates)

    ns = dict(vars(U), _REPAIR_DRAW=repair_draw)
    exec(compile(src, f'<birth_repair_patch:{U.__file__}>', 'exec'), ns)
    patched = ns['reserve']

    def reserve(self, *a, **k):
        if self.selector != 'ervs':
            raise RuntimeError('birth repair patch replaces the ERVS draw path')
        return patched(self, *a, **k)
    U.UnifiedTrainingSet.reserve = reserve

    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'birth_repair.json').write_text(json.dumps(dict(
                lag=LAG, n=N, min_share=MIN, group_K=K,
                stats={('/'.join(k) if isinstance(k, tuple) else k): v for k, v in st.items()},
                events=STATE['events'][:400]), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
