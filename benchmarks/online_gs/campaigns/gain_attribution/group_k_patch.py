"""Persistent K-group ERVS sampling for the adopted B mapper (runtime patch; locked sources untouched).

Revised method §3.2: at the start of each group the ERVS probabilities are computed from the current selection counts and
K distinct views are drawn without replacement; each is used once, then the next group is drawn. In B the group was
tied to one selection batch (K_keyframe = 3, K_dense = 6, truncated by the remaining packet credit). This patch keeps
one group queue per pool (keyframe, dense) across batches and packets, with a single K = `B_GROUP_K`.

- Group draw: weights exp(-(n_i - min n) / scale) over the whole current pool (same scale as B's ERVS: tau/N * (T+1),
  per_view), K distinct views by Gumbel top-K (exact successive-renormalized sampling). If the pool has fewer than K
  views, the group is the whole pool.
- Each pool draw takes the next queued view, skipping views that left the pool or were already chosen in this batch
  (e.g. by the window role). Views admitted mid-group become eligible in the next group.
- Window role, quotas 3:3:6, credit, kappa, tau, optimizer steps: unchanged.

Copies the locked `UnifiedTrainingSet.reserve` (sha256 checked) and changes one line; writes `<output>/group_k.json`.
"""
import atexit
from collections import Counter, deque
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import sys
import textwrap

RESERVE_SHA256 = '93be917d5783296d8328f32af887e13b8c6365199b853b7d1b27301821d709b2'
OLD = "uid = self.rng.choices(candidates, weights=weights, k=1)[0]"
NEW = "uid = _GROUP_DRAW(self, role, pools[role], used, scales[role], candidates, weights)"


def install():
    K = int(os.environ['B_GROUP_K'])
    assert K >= 1, K
    import unified_view_training as U
    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    digest = hashlib.sha256(src.encode()).hexdigest()
    if digest != RESERVE_SHA256:
        raise RuntimeError(f'UnifiedTrainingSet.reserve changed: {digest}')
    assert src.count(OLD) == 1
    src = src.replace(OLD, NEW)
    stats = Counter()
    sizes = {'keyframe': [], 'dense': []}

    def group_draw(self, role, pool, used, scale, candidates, weights):
        queues = self.__dict__.setdefault('_k_groups', {})
        q = queues.setdefault(role, deque())
        members = set(pool)
        for attempt in range(2):
            while q:
                uid = q.popleft()
                if uid in members and uid not in used:
                    stats['draws', role] += 1
                    return uid
                stats['skipped', role] += 1
            if attempt == 0:
                ordered = sorted(members)
                low = min(self.counts[u] for u in ordered)
                keys = []
                for u in ordered:
                    g = -math.log(-math.log(max(self.rng.random(), 1e-15)))
                    keys.append((-(self.counts[u] - low) / scale + g, u))
                keys.sort(reverse=True)
                group = [u for _, u in keys[:min(K, len(keys))]]
                q.extend(group)
                stats['groups', role] += 1
                sizes[role].append(len(group))
        # Every queued view was already chosen in this batch: fall back to the original single draw.
        stats['fallback', role] += 1
        stats['draws', role] += 1
        return self.rng.choices(candidates, weights=weights, k=1)[0]

    namespace = dict(vars(U), _GROUP_DRAW=group_draw)
    globals()['NAMESPACE'] = namespace           # lets other patches wrap _GROUP_DRAW (behaviour unchanged)
    exec(compile(src, f'<group_k_patch:{U.__file__}>', 'exec'), namespace)
    patched = namespace['reserve']

    def reserve(self, *args, **kwargs):
        if self.selector != 'ervs':
            raise RuntimeError('group-K patch applies to the ERVS selector only')
        return patched(self, *args, **kwargs)
    U.UnifiedTrainingSet.reserve = reserve
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'group_k.json').write_text(json.dumps(dict(
                K=K, reserve_sha256=digest, stats={f'{k}/{r}': n for (k, r), n in sorted(stats.items())},
                mean_group_size={r: (sum(v) / len(v) if v else None) for r, v in sizes.items()},
                full_groups={r: sum(s == K for s in v) for r, v in sizes.items()}), indent=2) + '\n')
    atexit.register(dump)
    return K


if __name__ == '__main__':
    import runpy
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)          # keep the official selected_mapping modules first
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
