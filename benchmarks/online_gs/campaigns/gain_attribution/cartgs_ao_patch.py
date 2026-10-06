"""CaRtGS Adaptive Optimization (Feng et al., RA-L 2025, §III.C.2, Eq. 5-8) as a replay sampler in the B mapper.

Re-implementation in our unified trainer, applied separately to the KF pool and the dense pool (CaRtGS has only a
keyframe pool; our dense pool gets the same rule):
  * follows the released code (github.com/DapengFeng/cartgs, src/gaussian_mapper.cpp useOneRandomSlidingWindowKeyframe):
    a view entering a pool gets r0 uses (B_AO_R0, default 2 = new_keyframe_times_of_use in the TUM configs); draws walk
    a shuffled order of the pool (reshuffled when the pool changes) and take the next view with r > 0, decrementing it;
  * after a full cycle without a usable view, every view gets +1 and the top max(1, k / d) by last training loss get
    one more (d = B_AO_D, default 4 = auto_distribute); views never trained have no loss and only get the +1;
  * batch adaptation: views already chosen in this batch are skipped; refills happen only under the official
    condition (no view of the pool has uses left); if every view with uses left is already in this batch, the next
    unused view in walk order is borrowed without consuming a use (counted as `borrow`). Loop-closure / local-BA bonus uses are not modelled
    (our frozen tracker stream has no loop-closure flag; local_BA_increased_times_of_use is 0 in the TUM configs).
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
        # Mirrors GaussianMapper::useOneRandomSlidingWindowKeyframe (CaRtGS src/gaussian_mapper.cpp L1075-1130):
        # walk a shuffled order of the pool (reshuffled when the pool changes), skip views with no remaining uses;
        # after a full cycle with no usable view, add 1 use to every view and 1 more to the top max(1, k / 4) by last
        # loss (auto_distribute = 4), then keep walking. New views get new_keyframe_times_of_use = 2 (TUM config).
        # Batch adaptation: views already chosen in this batch are skipped like exhausted ones.
        st = self.__dict__.setdefault('_ao', {}).setdefault(role, dict(r={}, perm=[], members=None, idx=0))
        r = st['r']
        for u in pool:
            if u not in r:
                r[u] = R0; STATS['admit', role] += 1
        members = tuple(pool)
        if st['members'] != members:
            st['perm'] = list(members); self.rng.shuffle(st['perm']); st['members'] = members
            st['idx'] = min(st['idx'], len(members) - 1); STATS['reshuffle', role] += 1
        perm, n = st['perm'], len(st['perm'])
        if not any(r[u] > 0 for u in pool):
            # Official condition: a full cycle finds no view with remaining uses -> +1 to all, +1 to top max(1, k/d).
            TS.materialize()
            gen = int(self.generation)
            loss = {u: (TS.STATE['views'].get((gen, u)) or {}).get('loss') for u in pool}
            for u in pool:
                r[u] += 1
            known = [u for u in pool if loss[u] is not None]
            k = max(1, len(known) // D) if known else 0
            for u in sorted(known, key=lambda v: -loss[v])[:k]:
                r[u] += 1
            STATS['refill', role] += 1; STATS['refill_top', role] += k
        uid = None
        for step in range(1, n + 1):
            u = perm[(st['idx'] + step) % n]
            if r[u] > 0 and u not in used:
                st['idx'] = (st['idx'] + step) % n; uid = u; STATS['draw', role] += 1
                break
        if uid is None:
            # Batch adaptation: every view with remaining uses is already in this batch (CaRtGS trains one view per
            # step, so this never arises there). Borrow the next unused view in walk order without consuming a use.
            for step in range(1, n + 1):
                u = perm[(st['idx'] + step) % n]
                if u not in used:
                    st['idx'] = (st['idx'] + step) % n; uid = u; STATS['borrow', role] += 1
                    break
        if uid is None:
            uid = self.rng.choice(candidates); STATS['fallback', role] += 1
        if r.get(uid, 0) > 0:
            r[uid] -= 1
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
