"""CaRtGS Adaptive Optimization (Feng et al., RA-L 2025, §III.C.2, Eq. 5-8) as a replay sampler in the B mapper.

Re-implementation in our unified trainer, applied separately to the KF pool and the dense pool (CaRtGS has only a
keyframe pool; our dense pool gets the same rule):
  * a view entering a pool gets a remaining-iteration count r0 (B_AO_R0, default 2 = CaRtGS's TUM-RGBD/VECtor setting);
  * each draw picks uniformly at random among pool views with r > 0 (not already in this batch) and decrements r;
  * when no view of the pool has r > 0, the pool is refilled: the top d_k = max(1, floor(k / d)) views by last training
    loss get 2, all others 1 (d = B_AO_D, default 4 = CaRtGS default). Views never trained count as highest loss.
  * if every view with r > 0 is already in this batch, the draw falls back to a uniform pick among the remaining
    candidates (decrementing its r if positive); counted in stats.
Last training loss per view comes from train_signal's per-render hook (same loss the optimizer uses). Window picks,
quotas 3:3:6, credit, kappa and births are unchanged; the ERVS weights are not used. Writes <output>/cartgs_ao.json.
Usage: B_SELECTED_WORKER=... python cartgs_ao_patch.py <worker args>
"""
import atexit
from collections import Counter
import hashlib
import inspect
import json
import os
from pathlib import Path
import runpy
import sys
import textwrap

R0 = int(os.environ.get('B_AO_R0', '2'))
D = int(os.environ.get('B_AO_D', '4'))
STATS = Counter()


def install():
    import train_signal as TS
    import group_k_patch as GK
    TS.install_logger()
    import unified_view_training as U
    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    if hashlib.sha256(src.encode()).hexdigest() != GK.RESERVE_SHA256:
        raise RuntimeError('UnifiedTrainingSet.reserve changed')
    src = src.replace(GK.OLD, "uid = _AO_DRAW(self, role, pools[role], used, candidates)")

    def ao_draw(self, role, pool, used, candidates):
        st = self.__dict__.setdefault('_ao', {}).setdefault(role, {})
        for u in pool:
            if u not in st:
                st[u] = R0; STATS['admit', role] += 1
        live = [u for u in pool if st[u] > 0]
        if not live:
            TS.materialize()
            gen = int(self.generation)
            loss = {u: (TS.STATE['views'].get((gen, u)) or {}).get('loss') for u in pool}
            k = len(pool); dk = max(1, k // D)
            order = sorted(pool, key=lambda u: (-(loss[u] if loss[u] is not None else float('inf')), u))
            top = set(order[:dk])
            for u in pool:
                st[u] = 2 if u in top else 1
            STATS['refill', role] += 1; STATS['refill_top', role] += len(top)
            live = list(pool)
        eligible = [u for u in live if u not in used]
        if eligible:
            uid = self.rng.choice(eligible); STATS['draw', role] += 1
        else:
            uid = self.rng.choice(candidates); STATS['fallback', role] += 1
        if st.get(uid, 0) > 0:
            st[uid] -= 1
        return uid

    ns = dict(vars(U), _AO_DRAW=ao_draw)
    exec(compile(src, f'<cartgs_ao_patch:{U.__file__}>', 'exec'), ns)
    patched = ns['reserve']

    def reserve(self, *a, **k):
        if self.selector != 'ervs':
            raise RuntimeError('CaRtGS-AO patch replaces the ERVS draw path')
        return patched(self, *a, **k)
    U.UnifiedTrainingSet.reserve = reserve
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'cartgs_ao.json').write_text(json.dumps(dict(
                method='CaRtGS adaptive optimization (Eq. 5-8), per pool', r0=R0, d=D,
                stats={f'{a}/{b}': n for (a, b), n in sorted(STATS.items())}), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
