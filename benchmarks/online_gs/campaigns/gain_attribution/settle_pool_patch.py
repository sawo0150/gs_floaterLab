"""Settle-aware pool management on top of ERVS K16 (runtime patch; ERVS weights and K-group queue unchanged).

Finding behind it (gap_ladder): replay of regions the camera has left is washed out by later training elsewhere, and
updates are worth more once a region stops changing; fresh regions are trained by the window role anyway. So the
replay pools (KF role and dense role) hold only views whose region has *settled*; the window role keeps the newest KFs.

B_SETTLE_MODE:
  kf    a view is settled once at least B_SETTLE_M keyframes have arrived after it (dense: after its right anchor KF).
  pose  a view is settled once the newest keyframe camera is far from it: centre distance > B_SETTLE_K × median
        distance between consecutive KFs (scale-free), or viewing-direction angle > B_SETTLE_DEG degrees. Dense views
        use the mean of their two anchor KFs' centres and the left anchor's direction. Poses are read from the mapper
        at each decision (current, causal estimates).
Rules:
  * dense admission (Optimization-Guided View Set Growth, largest temporal hole first, one per κ steps) only
    considers settled offered views; unspent growth slots carry over until settled views appear;
  * KF-role and dense-role draws use ERVS K16 group draws over the settled members of the pool; if no member is
    settled the full pool is used (counted);
  * window picks, quotas 3:3:6, credit, κ, τ, births unchanged.
Writes <output>/settle_pool.json.
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

MODE = os.environ['B_SETTLE_MODE']
assert MODE in ('kf', 'pose'), MODE
M = int(os.environ.get('B_SETTLE_M', '5'))
KD = float(os.environ.get('B_SETTLE_K', '8'))
DEG = float(os.environ.get('B_SETTLE_DEG', '45'))
K = int(os.environ.get('B_GROUP_K', '16'))
STATE = dict(mapper=None, stats=Counter(), pool_sizes=[])


def install():
    import online_mapper_runtime as R
    import online_view_training as O
    import unified_view_training as U
    import group_k_patch as GK
    st = STATE['stats']

    dispatch = R.OnlineMapperRuntime.dispatch

    def keep_dispatch(self, packet):
        STATE['mapper'] = self.mapper
        return dispatch(self, packet)
    R.OnlineMapperRuntime.dispatch = keep_dispatch

    def kf_geometry(kfs):
        import torch
        mp = STATE['mapper']
        cen, fwd = {}, {}
        for u in kfs:
            v = mp.viewpoints.get(u) if mp is not None else None
            if v is None:
                continue
            with torch.no_grad():
                cen[u] = v.camera_center.detach().float().cpu().numpy()
                fwd[u] = v.R.detach().float().cpu().numpy()[2]       # world-to-camera R: third row = optical axis
        return cen, fwd

    def settled_fn(policy):
        kfs = sorted(policy.keyframes)
        if not kfs:
            return lambda kind, u, row=None: True
        newest = kfs[-1]
        if MODE == 'kf':
            import bisect

            def fn(kind, u, row=None):
                ref = row.right if kind == 'dense' else u
                return len(kfs) - bisect.bisect_right(kfs, ref) >= M
            return fn
        import numpy as np
        cen, fwd = kf_geometry(kfs)
        if newest not in cen or len(cen) < 3:
            return lambda kind, u, row=None: False
        seq = [cen[u] for u in kfs if u in cen]
        step = float(np.median([np.linalg.norm(b - a) for a, b in zip(seq, seq[1:])])) or 1e-6
        c0, f0 = cen[newest], fwd[newest]

        def far(c, f):
            ang = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(f, f0)) / (np.linalg.norm(f) * np.linalg.norm(f0) + 1e-12)))))
            return float(np.linalg.norm(c - c0)) > KD * step or ang > DEG

        def fn(kind, u, row=None):
            if kind == 'dense':
                a, b = row.left, row.right
                if a not in cen or b not in cen:
                    return False
                return far((cen[a] + cen[b]) / 2, fwd[a])
            return u in cen and far(cen[u], fwd[u])
        return fn

    # ---- admission: only settled offered dense views are candidates
    admit = O.OnlineTrainingSet._admit

    def settled_admit(self):
        full = self.offered
        fn = settled_fn(self)
        self.offered = {u: r for u, r in full.items() if u in self.admitted or fn('dense', u, r)}
        st['admit_calls'] += 1; st['admit_offered_settled'] += len(self.offered) - len(self.admitted & set(self.offered))
        try:
            return admit(self)
        finally:
            self.offered = full
    O.OnlineTrainingSet._admit = settled_admit

    # ---- draws: ERVS K16 over settled members of the KF / dense pools
    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    if hashlib.sha256(src.encode()).hexdigest() != GK.RESERVE_SHA256:
        raise RuntimeError('UnifiedTrainingSet.reserve changed')
    src = src.replace(GK.OLD, 'uid = _SETTLE_DRAW(self, role, pools[role], used, scales[role], candidates)')

    def settle_draw(self, role, pool, used, scale, candidates):
        cache = self.__dict__.setdefault('_settle_cache', {})
        key = (self.rgb_view_services, role)
        if cache.get('key') != key:
            fn = settled_fn(self)
            kind = 'dense' if role == 'dense' else 'kf'
            members = {u for u in pool if fn(kind, u, self.offered.get(u) if kind == 'dense' else None)} \
                if kind == 'kf' else set(pool)          # dense pool already holds settled views only (admission)
            if not members:
                members = set(pool); st['unsettled_fallback', role] += 1
            cache.clear(); cache.update(key=key, members=members)
            STATE['pool_sizes'].append((role, len(members), len(pool)))
        members = cache['members']
        q = self.__dict__.setdefault('_settle_groups', {}).setdefault(role, deque())
        for attempt in range(2):
            while q:
                u = q.popleft()
                if u in members and u not in used:
                    st['draw', role] += 1
                    return u
            if attempt == 0:
                ordered = sorted(members); low = min(self.counts[u] for u in ordered)
                keys = sorted(((-(self.counts[u] - low) / scale - math.log(-math.log(max(self.rng.random(), 1e-15))), u)
                               for u in ordered), reverse=True)
                q.extend(u for _, u in keys[:min(K, len(keys))])
        st['fallback', role] += 1
        return self.rng.choice(candidates)

    ns = dict(vars(U), _SETTLE_DRAW=settle_draw)
    exec(compile(src, f'<settle_pool_patch:{U.__file__}>', 'exec'), ns)
    patched = ns['reserve']

    def reserve(self, *a, **k):
        if self.selector != 'ervs':
            raise RuntimeError('settle patch replaces the ERVS draw path')
        return patched(self, *a, **k)
    U.UnifiedTrainingSet.reserve = reserve

    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            ps = STATE['pool_sizes']
            frac = {r: (sum(a for rr, a, b in ps if rr == r) / max(1, sum(b for rr, a, b in ps if rr == r))) for r in ('keyframe', 'dense')}
            (output / 'settle_pool.json').write_text(json.dumps(dict(
                mode=MODE, M=M, K_dist=KD, deg=DEG, group_K=K, settled_share_of_pool=frac,
                stats={('/'.join(k) if isinstance(k, tuple) else k): v for k, v in st.items()}), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
