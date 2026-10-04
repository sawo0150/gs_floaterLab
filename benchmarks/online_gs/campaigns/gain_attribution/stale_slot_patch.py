"""ERVS K16 + one stale-first dense slot per batch (rule A; runtime patch, ERVS formula untouched).

On top of group_k_patch (persistent per-pool K=16 Gumbel group queue with the unchanged ERVS weights), after each
`reserve` the first dense pick of the batch is replaced by the admitted dense view that has gone longest without a
service in this map generation (views never served count from their admission). The displaced ERVS pick is put back
at the front of the dense group queue, so the ERVS group order is kept and it is served next. Window and KF picks,
quotas, credit, kappa and tau are unchanged. Writes `<output>/stale_slot.json`.
Usage: B_GROUP_K=16 B_SELECTED_WORKER=... python stale_slot_patch.py <worker args>
"""
import atexit
from collections import Counter
from dataclasses import replace
import json
import os
from pathlib import Path
import runpy
import sys

STATS = Counter()
STALENESS = []


def install():
    import group_k_patch as GK
    GK.install()
    import unified_view_training as U
    reserve, commit_prefix = U.UnifiedTrainingSet.reserve, U.UnifiedTrainingSet.commit_prefix

    def stale_reserve(self, *a, **k):
        sel = reserve(self, *a, **k)
        if sel is None:
            return sel
        rec = self._pending_batch
        roles = list(rec['roles'])
        if 'dense' not in roles:
            STATS['batches_without_dense'] += 1
            return sel
        i = roles.index('dense')
        now = self.rgb_view_services
        last = self.__dict__.setdefault('_stale_last', {})
        born = {x['uid']: x['rgb_steps'] for x in self.admission_ledger}
        chosen = set(sel.uids)
        pool = [u for u in self.admitted if u not in chosen]
        if not pool:
            STATS['no_candidate'] += 1
            return sel
        idle = lambda u: now - last.get(u, born.get(u, 0))
        stale = max(pool, key=lambda u: (idle(u), -u))
        old = sel.uids[i]
        if idle(stale) <= idle(old):
            STATS['kept_ervs_pick'] += 1          # the ERVS pick is already at least as stale
            return sel
        uids = list(sel.uids); uids[i] = stale
        self.__dict__.setdefault('_k_groups', {}).setdefault('dense', __import__('collections').deque()).appendleft(old)
        counts = list(rec['counts_before']); counts[i] = self.counts[stale]
        anchors = {u: v for u, v in rec['dense_anchors'].items() if u != old}
        anchors[stale] = (self.offered[stale].left, self.offered[stale].right)
        self._pending = replace(sel, uids=tuple(uids))
        self._pending_batch = {**rec, 'counts_before': tuple(counts), 'dense_anchors': anchors}
        STATS['replaced'] += 1
        STALENESS.append(idle(stale))
        return self._pending

    def tracked_commit(self, selection, size):
        uids = selection.uids[:size]
        out = commit_prefix(self, selection, size)
        last = self.__dict__.setdefault('_stale_last', {})
        for u in uids:
            last[u] = self.rgb_view_services
        return out

    U.UnifiedTrainingSet.reserve = stale_reserve
    U.UnifiedTrainingSet.commit_prefix = tracked_commit
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'stale_slot.json').write_text(json.dumps(dict(
                rule='first dense pick per batch -> longest-idle admitted dense view; displaced ERVS pick re-queued first',
                stats=dict(STATS), mean_idle_of_replacements=(sum(STALENESS) / len(STALENESS) if STALENESS else None),
                max_idle_of_replacements=max(STALENESS, default=None)), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(Path(__file__).resolve().parent))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
